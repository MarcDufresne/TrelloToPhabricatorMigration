import json
import os

import datetime

import simplejson
import yaml

from phabricator import Phabricator


CUR_DIR = os.getcwd()
config_dir = os.path.join(CUR_DIR, 'config')

conf_file = 'conf.yaml'
token_file = 'token.yaml'
project_map_file = 'project_map.yaml'
user_map_file = 'user_map.yaml'

with open(os.path.join(config_dir, conf_file)) as f:
    CONF = yaml.load(f)

with open(os.path.join(config_dir, token_file)) as f:
    PHAB_API_TOKEN = yaml.load(f)['phab_api_token']

with open(os.path.join(config_dir, project_map_file)) as f:
    PROJECT_MAP_CONF = yaml.load(f)

with open(os.path.join(config_dir, user_map_file)) as f:
    USER_MAP_CONF = yaml.load(f)


DRY_RUN = bool(CONF['card_import_dry_run'])

MIGRATED_PROJECT_PHID = CONF['migrated_project_phid']


BOARDS_FILES_TO_BOARD = CONF['file_map']
BOARD_PROJECTS = CONF['project_phab_ids']


TAGS_TO_PROJECTS = PROJECT_MAP_CONF['project_map']


MEMBER_TO_PHID = USER_MAP_CONF['user_map']
MEMBER_TO_USERNAME = USER_MAP_CONF['memberid_to_username']


PHIDS_NAMES = None


phab = Phabricator(token=PHAB_API_TOKEN)
phab.update_interfaces()


def populate_phids_names():
    def get_phids(d):
        return [v for k, v in d.items()
                if isinstance(v, str) and "PHID-" in v]

    if PHIDS_NAMES:
        return

    phids_list = get_phids(BOARD_PROJECTS)
    phids_list += [MIGRATED_PROJECT_PHID]
    phids_list += get_phids(TAGS_TO_PROJECTS)
    phids_list += get_phids(MEMBER_TO_PHID)

    response = phab.phid.query(phids=phids_list).response

    phids_names = {}
    for phid, value in response.items():
        phids_names[phid] = value['name']

    globals()['PHIDS_NAMES'] = phids_names


def phid_to_name(phid):
    populate_phids_names()
    return PHIDS_NAMES.get(phid, "UNKNOWN")


def member_list_to_phab_users_phids(members):
    users_phids = []
    for member in members:
        if member in MEMBER_TO_PHID and MEMBER_TO_PHID[member]:
            users_phids.append(MEMBER_TO_PHID[member])
    return users_phids


def labels_to_projects(labels, project):
    project_list = []

    for label in labels:
        if label in TAGS_TO_PROJECTS:
            project_list.append(TAGS_TO_PROJECTS[label])

    if project in BOARD_PROJECTS:
        project_list.append(BOARD_PROJECTS[project])

    if MIGRATED_PROJECT_PHID:
        project_list.append(MIGRATED_PROJECT_PHID)

    return project_list


def generate_formatted_checklists(checklists):
    formatted_checklists = ""

    for checklist in checklists:
        formatted_checklists += "=== {} ===\n\n".format(checklist.get('name'))
        for checked_item in checklist.get('checkItems', []):
            if checked_item.get('state', "") == 'complete':
                box = "[X]"
            else:
                box = "[ ]"
            formatted_checklists += "{} - {}\n".format(
                box, checked_item.get('name'))
        formatted_checklists += "\n\n"

    return formatted_checklists


def generate_comments(comments):
    def date_sort(d):
        d = d[:-5]
        d = datetime.datetime.strptime(d, "%Y-%m-%dT%H:%M:%S")
        return d

    comments = sorted(comments, key=lambda d: date_sort(d['date']))

    comments_block = "=== Previous Comments ===\n\n"

    for comment in comments:
        comments_block += "\n@{} - {}\n{}\n".format(
            MEMBER_TO_USERNAME.get(comment['author_id'],
                                   comment['author_id']),
            comment['date'], comment['text'])

    return comments_block


def run():
    boards = {}

    exports_path = os.path.join(CUR_DIR, 'trello_exports')

    for exp_file in BOARDS_FILES_TO_BOARD.keys():
        board_file_path = os.path.join(exports_path, exp_file)

        with open(board_file_path, 'r') as board_file:
            contents = board_file.read()
            boards[BOARDS_FILES_TO_BOARD[exp_file]] = json.loads(contents)

    created_tasks = []
    failed_creation = []

    for board_id, board in boards.items():
        import_cards_to_phab(board.get('cards'), board_id,
                             board.get('checklists'), created_tasks,
                             failed_creation)


def import_cards_to_phab(cards, board_id, checklists, created_tasks,
                         failed_creation):
    for card in cards:

        if card.get('closed', True):
            continue

        desc = card.get('desc')

        cards_checklists = []
        for checklist in checklists:
            if checklist.get('id') in card.get('idChecklists', []):
                cards_checklists.append(checklist)

        formatted_checklists = generate_formatted_checklists(cards_checklists)
        card_url = "\n\nSee older comments and " \
                   "attachments here: {} \n".format(card.get('shortUrl'))

        comments = ""
        if card.get('comments'):
            comments = generate_comments(card['comments'])

        desc += formatted_checklists + card_url + comments

        cc_phids = member_list_to_phab_users_phids(card.get('idMembers', []))
        projects = labels_to_projects(card.get('idLabels', []), board_id)

        request_payload = dict(
            title=card.get('name'), description=desc,
            ccPHIDs=cc_phids, projectPHIDs=projects)

        if DRY_RUN:
            cc_names = []
            for cc_phid in cc_phids:
                cc_names.append(phid_to_name(cc_phid))

            project_names = []
            for project_phid in projects:
                project_names.append(phid_to_name(project_phid))

            request_payload['ccPHIDs'] = cc_names
            request_payload['projectPHIDs'] = project_names

            pretty_format = simplejson.dumps(
                request_payload, indent=4, sort_keys=True)
            print("{}\n\n{}\n".format("*" * 30, pretty_format))
            continue

        try:
            new_task_res = phab.maniphest.createtask(**request_payload)
        except:
            print("Could not create task with "
                  "payload\n{}\n".format(request_payload))
            failed_creation.append(request_payload)
        else:
            created_tasks.append(new_task_res.response)


if __name__ == '__main__':
    run()
