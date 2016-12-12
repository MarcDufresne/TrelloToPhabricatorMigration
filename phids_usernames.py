import os

import yaml

from phabricator import Phabricator


CUR_DIR = os.getcwd()
config_dir = os.path.join(CUR_DIR, 'config')

token_file = 'token.yaml'
user_map_file = 'user_map.yaml'

with open(os.path.join(config_dir, token_file)) as f:
    PHAB_API_TOKEN = yaml.load(f)['phab_api_token']

with open(os.path.join(config_dir, user_map_file)) as f:
    USER_MAP_CONF = yaml.load(f)


def main():
    phab = Phabricator(token=PHAB_API_TOKEN)
    phab.update_interfaces()

    user_map = USER_MAP_CONF['user_map']
    all_phids = user_map.values()

    phids_data = phab.phid.query(phids=all_phids).response

    for member_id, phid in user_map.items():
        if phid:
            print("{}: \"{}\"".format(member_id, phids_data[phid]['name']))

if __name__ == '__main__':
    main()
