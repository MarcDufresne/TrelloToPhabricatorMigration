# Trello to Phabricator Import Tool

This is a tool to export all cards from Trello and import them as tasks
in a Phabricator installation. It will import the card name, description,
members, checklists and comments as well as give a link to the card for
any additional details.

- Card name -> Task title
- Card description, checklists, earlier comments -> Task description
- Card labels -> Project Tags
- Card members -> Task subscribers

Note that this does not create users or projects in your Phabricator 
instance. Those will need to be created beforehand.

### Getting Started

To get started follow the steps below:

- Clone this repo locally.
- Create a virtualenv and run `pip install -r requirements.txt` to install
  all the dependencies.
  
Then you will need to copy all the `yaml` files in the config directory
and remove the `.sample` from the name of each one. Then you will need to 
populate those files. A reference of each config value is provided below. 

##### conf.yaml

`card_import_dry_run`: `true` or `false`, whether the tool will create 
the tasks for real or not. `true` will not create tasks.

`migrated_project_phid`: optional PHID, will be applied to all created 
tasks so they are easy to keep track of. You will need to create this 
one in Phabricator.

`file_map`: a simple mapping of file name to board ID, determines which 
file will be used for migration. Files not in this list won't be imported.

`project_phab_ids`: mapping of board IDs to project PHIDs to assign labels based
on the original board. You will need to create those in Phabricator then
add the PHIDs here.

##### project_map.yaml

`project_map`: Mapping of label IDs to project PHIDs. Get the label IDs 
from each board's JSON file. You will need to 
create corresponding projects ("tags") in Phabricator and add the 
PHIDs here.

##### user_map.yaml

`user_map`: Mapping of member IDs to user PHIDs, use `import_members.py`
to populate the list of members. You will need to get the corresponding 
user PHIDs from Phabricator and add them next to the member IDs. You can
also leave some empty PHIDs, those members won't be subscribed to tasks.

`memberid_to_username`: Mapping between member IDs and Phabricator user 
names. Use `phids_usernames.py` to populate this config. It will use 
`user_map` as a base.

##### token.yaml

`phab_api_token`: Conduit API token from an admin user. It is recommended 
to use a bot since it will be subscribed to all created tasks.

`trello_org_name_or_id`: Name of your Organization on Trello, you can 
get this one in the URL of your Org page on Trello.

`trello_key`: Your Trello API key, get it [here](https://trello.com/app-key).

`trello_token` Trello user token for private boards/orgs, get it 
with this URL in a browser. Replace `TRELLO_KEY` with your own key.

```
https://trello.com/1/authorize?key=TRELLO_KEY&name=Import+Tool&expiration=30days&response_type=token&scope=read
```

### Importing Members

##### import_members.py

This will print all your Trello members in your console. Copy and 
paste the value in `user_map.yaml`/`user_map`. You can reuse this script
to update the members later on, it will only show members that are not
in your current config file.

##### phids_usernames.py

This will use the `user_map.yaml`/`user_map` values to fetch the 
Phabricator usernames for every member. Copy and paste the result in
`user_map.yaml`/`memberid_to_username`.

### Importing Boards JSON

To get all boards, cards and comments for your Organization run 
`import_boards.py`. This will fetch all the boards and save them as JSON
in the `trello_exports` directory. You can then edit the 
`conf.yaml`/`file_map` to determine which boards will be imported. 
As well as getting the labels from each boards to populate 
`project_map.yaml`/`project_map`

### Import Cards
 
Run `main.py` to import all the boards from `conf.yaml`/`file_map` into 
Phabricator. `conf.yaml`/`card_import_dry_run` will determine if tasks will
be created or just shown without being created on Phabricator.

