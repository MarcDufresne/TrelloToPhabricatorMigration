import os

import simplejson as simplejson
import yaml

from trello import TrelloApi


cur_dir = os.getcwd()
token_config_filepath = os.path.join(cur_dir, 'config', 'token.yaml')
export_path = os.path.join(cur_dir, 'trello_exports')

with open(token_config_filepath) as f:
    TOKEN_CONF = yaml.load(f)

TRELLO_ORG = TOKEN_CONF['trello_org_name_or_id']
TRELLO_KEY = TOKEN_CONF['trello_key']
TRELLO_TOKEN = TOKEN_CONF['trello_token']

client = TrelloApi(TRELLO_KEY)
client.set_token(TRELLO_TOKEN)


def get_boards():
    boards = client.organizations.get_board(TRELLO_ORG, fields=['id', 'name'])
    return boards


def get_card_comments(card_id):
    comments = client.cards.get_action(card_id, filter=['commentCard'])
    parsed_comments = []
    for comment in comments:
        text = comment['data']['text']
        author_id = comment['idMemberCreator']
        date = comment['date']
        parsed_comments.append(dict(text=text, date=date,
                                    author_id=author_id))
    return parsed_comments


def get_board_json(board_id):
    board_json = client.boards.get(
        board_id, cards="open", checklists="all", members="all")

    board_labels = client.boards.get_field("labels", board_id)

    board_json['labels'] = board_labels

    for card in board_json['cards']:
        if card['badges']['comments'] > 0:
            card['comments'] = get_card_comments(card['id'])

    return board_json


def write_json_to_file(board_name, board_json):
    filename = board_name.lower().replace(' ', '_') + ".json"
    pretty_json = simplejson.dumps(board_json, sort_keys=True, indent=2)

    with open(os.path.join(export_path, filename), mode='w') as jf:
        jf.write(pretty_json)


def run():
    boards = get_boards()

    boards_json = {}
    for board in boards:
        boards_json[board['name']] = get_board_json(board['id'])

    for name, board_json in boards_json.items():
        write_json_to_file(name, board_json)


if __name__ == '__main__':
    run()
