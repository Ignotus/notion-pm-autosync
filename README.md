# notion-pm-autosync

Synchronizes git commits with Notion Agile Project Manager dashboards. Tickets
referenced as `#PM-<ID>` will be automatically updated with a git commit.


### Configuration

1. Create a Github App at https://github.com/settings/apps with Read access on Metadata and Contents. Subscribe for Push events.
2. Setup your webhook URL and also github webook secret.
3. Install an app into your Github account.
4. Create a notion integration https://www.notion.so/profile/integrations . Provide access to Insert Comments.
5. Connect the new integration to a database
6. Add an ID field for your ticket pages
7. Run an autosync service on the server accessible via the webhook.

``
python3 -m notion_pm_autosync.autosync -c config.toml -p 8001
``

### Requirements

``
pip3 install -r requirements.txt
``
