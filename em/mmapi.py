from os import environ

import mattermost
from aiohttp import web

MATTERMOST_BOT_TOKEN = environ.get('BOT_TOKEN', '')
MATTERMOST_ENDPOINT = environ.get('MATTERMOST_URL') + ":" + environ.get('MATTERMOST_PORT')
MATTERMOST_TEAM_ID = environ.get('MATTERMOST_TEAM_ID', '')
MATTERMOST_EXTERNAL = environ['MATTERMOST_EXTERNAL']
mm = mattermost.MMApi(f"{MATTERMOST_ENDPOINT}/api")
mm.login(bearer=MATTERMOST_BOT_TOKEN)


def get_target_userid(email):
    # noinspection PyProtectedMember
    return mm._get("/v4/users/email/" + email)['id']


def get_current_email(user_id):
    return mm.get_user(user_id)['email']


def send_message(user_id, message, actions=None):
    target_channel = mm.create_dm_channel_with(user_id)
    props = {
        "from_webhook": "false",
    }
    if actions is not None:
        props["attachments"] = [{"actions": [action for action in actions]}],

    mm.create_post(
        channel_id=target_channel['id'], message=message, props=props
    )
    team_name = mm.get_team(MATTERMOST_TEAM_ID)['name']
    return f"{MATTERMOST_EXTERNAL}/{team_name}/channels/{target_channel['name']}"


def add_to_my_team(user_id):
    mm.add_user_to_team(user_id=user_id, team_id=MATTERMOST_TEAM_ID)


def health(_):
    mm.get_user()
    return web.Response(text="Hello")
