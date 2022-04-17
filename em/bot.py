from aiohttp import web
from botocore.exceptions import ClientError
from mmpy_bot import Plugin, listen_webhook, WebHookEvent, Bot, ActionEvent

from em.cloudflare import cf_send_validation
from em.mmapi import get_target_userid, send_message, add_to_my_team, get_current_email
from em.routes import setup_routes, redirect, OP_URL_PREFIX
from em.s3 import get_token, put_token


class EmailManagerBot(Plugin):
    def __init__(self):
        super().__init__()

    async def match(self, request):
        if not request.headers.get('X-Auth-Request-Email', ''):
            return web.Response(status=401, reason="Unauthorized", body="Request is not authorized")
        token = request.match_info['token']
        try:
            j = get_token(token)
        except ClientError:
            return web.Response(status=500, reason="Server Error", body="Invalid token")
        email = request.headers['X-Auth-Request-Email']
        user_id = get_target_userid(self.driver, email)
        if j.get('matched'):
            if user_id == j.get('user_id'):
                return redirect(send_message(self.driver, user_id, "This link was already matched to your account."))
            else:
                return redirect(send_message(self.driver, user_id, "This link was used from another account, "
                                                                   "contact ~HELP to get this sorted."))

        add_to_my_team(self.driver, user_id)
        alias = j['alias']
        j['matched'] = True
        j['user_id'] = user_id
        put_token(token, j)
        url = f"{OP_URL_PREFIX}/hooks/send_email"
        actions = [
            {
                "id": 'hooks',
                "name": 'Send cloudflare verification email',
                "integration": {
                    "url": url,
                    "context": {
                        "token": token,
                        "user_id": user_id,
                    }
                }
            },
        ]
        return redirect(send_message(
            self.driver,
            user_id,
            f"I've matched {alias}@nix.co.il with your account.\n"
            f"Next, click the button at the bottom of this message to get a verification email from cloudflare.\n"
            f"You will only be sent a single email per address. You must complete verification to receive emails.",
            actions=actions
        ))

    @listen_webhook("send_email")
    async def send_email(self, event: WebHookEvent):
        if not isinstance(event, ActionEvent):
            return
        # noinspection PyBroadException
        try:
            token = event.context['token']
            j = get_token(token)
            user_id = j.get('user_id')
            email = get_current_email(self.driver, user_id)
            cf_send_validation(email)
            j['validated'] = email
            put_token(token, j)
            self.driver.respond_to_web(
                event,
                {
                    "update": {
                        "message": "An email from Cloudflare was dispatched (once) to your email address, "
                                   "please complete the process.",
                        "props": {}
                    },
                },
            )
        except:
            self.driver.respond_to_web(
                event,
                {
                    "ephemeral_text": "There was an error creating the validation request with cloudflare. "
                                      "Please contact ~HELP to get this resolved.",
                }
            )


def get_bot():
    return setup_routes(Bot(plugins=[EmailManagerBot()]))
