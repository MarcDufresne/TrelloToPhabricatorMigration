import os

import simplejson
import yaml

from trello import TrelloApi

CUR_DIR = os.getcwd()
config_dir = os.path.join(CUR_DIR, 'config')
exports_dir = os.path.join(CUR_DIR, 'trello_exports')

token_file = 'token.yaml'
conf_file = 'conf.yaml'
project_map_file = 'project_map.yaml'

with open(os.path.join(config_dir, token_file)) as f:
    token_config = yaml.load(f)
    TRELLO_ORG = token_config['trello_org_name_or_id']
    TRELLO_KEY = token_config['trello_key']
    TRELLO_TOKEN = token_config['trello_token']

with open(os.path.join(config_dir, project_map_file)) as f:
    project_map_conf = yaml.load(f)
    PROJECT_MAP = project_map_conf['project_map']

with open(os.path.join(config_dir, conf_file)) as f:
    conf = yaml.load(f)
    FILE_MAP = conf['file_map']

client = TrelloApi(TRELLO_KEY)
client.set_token(TRELLO_TOKEN)


def get_trello_labels():
    board_labels = []
    for filename, board_id in FILE_MAP.items():
        with open(os.path.join(exports_dir, filename)) as bf:
            board_dict = simplejson.loads(bf.read())
        for label in board_dict['labels']:
            if label.get('name'):
                board_labels.append(dict(
                    id=label['id'], name=label['name'],
                    board_name=board_dict['name']))
    return board_labels


def main():
    labels = get_trello_labels()

    for label in labels:
        if label['id'] not in PROJECT_MAP:
            print("# {board_name} - {name}\n{id}: \"\"".format(**label))


if __name__ == '__main__':
    main()
