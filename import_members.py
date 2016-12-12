import os

import yaml

from phabricator import Phabricator
from trello import TrelloApi


CUR_DIR = os.getcwd()
config_dir = os.path.join(CUR_DIR, 'config')

token_file = 'token.yaml'
user_map_file = 'user_map.yaml'

with open(os.path.join(config_dir, token_file)) as f:
    token_config = yaml.load(f)
    PHAB_API_TOKEN = token_config['phab_api_token']
    TRELLO_ORG = token_config['trello_org_name_or_id']
    TRELLO_KEY = token_config['trello_key']
    TRELLO_TOKEN = token_config['trello_token']

with open(os.path.join(config_dir, user_map_file)) as f:
    USER_MAP_CONF = yaml.load(f)


client = TrelloApi(TRELLO_KEY)
client.set_token(TRELLO_TOKEN)


def get_trello_members():
    return client.organizations.get_field('members', TRELLO_ORG)


def main():
    phab = Phabricator(token=PHAB_API_TOKEN)
    phab.update_interfaces()

    user_map = USER_MAP_CONF['user_map']

    members = get_trello_members()

    for member in members:
        if not member['id'] in user_map.keys():
            print "# {}\n{}: \"{}\"".format(
                member['fullName'], member['id'], "")


if __name__ == '__main__':
    main()
