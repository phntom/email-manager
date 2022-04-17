from os import environ

from aiohttp import web
from mmpy_bot.driver import Driver

MATTERMOST_TEAM_ID = environ['MATTERMOST_TEAM_ID']
MATTERMOST_EXTERNAL = environ['MATTERMOST_EXTERNAL']


def get_target_userid(driver: Driver, email: str):
    return driver.users.get_user_by_email(email)['id']


def get_current_email(driver: Driver, user_id: str):
    return driver.users.get_user(user_id)['email']


def send_message(driver: Driver, user_id, message, actions=None):
    target_channel = driver.channels.create_direct_message_channel([driver.user_id, user_id])
    props = {
        "from_webhook": "false",
    }
    if actions is not None:
        props = {
            "attachments": [
                {
                    "actions": actions
                }
            ]
        }
    driver.posts.create_post({
        "channel_id": target_channel['id'],
        "message": message,
        "props": props,
    })
    team_name = driver.teams.get_team(MATTERMOST_TEAM_ID)['name']
    return f"{MATTERMOST_EXTERNAL}/{team_name}/channels/{target_channel['name']}"


def add_to_my_team(driver: Driver, user_id):
    driver.teams.add_user_to_team(team_id=MATTERMOST_TEAM_ID, user_id=user_id)


def health(_):
    return web.Response(text="Hello")
