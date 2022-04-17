from aiohttp import web
from botocore.exceptions import ClientError
from mmpy_bot import Plugin, listen_webhook, WebHookEvent, Bot, ActionEvent, listen_to, Message

from em.cloudflare import cf_send_validation, cf_check_validation, cf_create_email_forward, CLOUDFLARE_ZONE_ID, \
    cf_get_all_rules
from em.mmapi import get_target_userid, send_message, add_to_my_team, get_current_email
from em.routes import setup_routes, redirect, OP_URL_PREFIX
from em.s3 import get_token, put_token


class EmailManagerBot(Plugin):
    def __init__(self):
        super().__init__()

    @listen_to(
        "^create email [a-z0-9]+@[a-z.]+ @[^ ]+",
        direct_only=True,
        allowed_users=['phantom', 'hypathia', 'yurynix'],
    )
    async def create_alias(self, message: Message):
        if len(message.mentions) != 1:
            return self.driver.reply_to(message, "mention a single target user after the email address")
        _, _, source_email, target = message.text.split(' ', 3)
        user = self.driver.users.get_user_by_username(target.lstrip('@'))
        target_id = user['id']
        target_email = user['email']
        domain = source_email.split('@')[1]
        if domain not in CLOUDFLARE_ZONE_ID:
            return self.driver.reply_to(message, f"domain {domain} not registered in bot")
        rules_cache = cf_get_all_rules()
        if source_email in rules_cache[domain]:
            target = rules_cache[domain][source_email]
            return self.driver.reply_to(message, f"email {source_email} already forwarded to {target}")
        await self.send_message_verify_or_done(source_email, target_email, target_id)

    async def match(self, request):
        if not request.headers.get('X-Auth-Request-Email', ''):
            return web.Response(status=401, reason="Unauthorized", body="Request is not authorized")
        token = request.match_info['token']
        try:
            j = get_token(token)
        except ClientError:
            return web.Response(status=500, reason="Server Error", body="Invalid token")
        target_email = request.headers['X-Auth-Request-Email']
        user_id = get_target_userid(self.driver, target_email)
        if j.get('matched'):
            if user_id == j.get('user_id'):
                return redirect(send_message(self.driver, user_id, "This link was already matched to your account."))
            else:
                return redirect(send_message(self.driver, user_id, "This link was used from another account, "
                                                                   "contact ~HELP to get this sorted."))

        add_to_my_team(self.driver, user_id)
        alias = j['alias']
        source_email = f'{alias}@nix.co.il'
        j['matched'] = True
        j['user_id'] = user_id
        put_token(token, j)
        nix_url = await self.send_message_verify_or_done(source_email, target_email, user_id)
        return redirect(nix_url)

    @listen_webhook("send_email")
    async def send_email(self, event: WebHookEvent):
        if not isinstance(event, ActionEvent):
            return
        try:
            user_id = event.context['user_id']
            source_email = event.context['source_email']
            target_email = get_current_email(self.driver, user_id)
            cf_send_validation(target_email)
            if not cf_check_validation(target_email):
                await self.message_confirm_verification(source_email, event, user_id)
            else:
                cf_create_email_forward(source_email, target_email)
                await self.send_forward_complete(source_email, event)
        except:
            await self.send_ephemeral("There was an error creating the validation request with cloudflare. "
                                      "Please contact ~HELP to get this resolved.", event)

    @listen_webhook("confirm_email")
    async def confirm_email(self, event: WebHookEvent):
        if not isinstance(event, ActionEvent):
            return
        # noinspection PyBroadException
        try:
            user_id = event.context['user_id']
            source_email = event.context['source_email']
            target_email = get_current_email(self.driver, user_id)
            if cf_check_validation(target_email):
                cf_create_email_forward(source_email, target_email)
                await self.send_forward_complete(source_email, event)
            else:
                await self.send_ephemeral("Your email verification with cloudflare was not complete yet.", event)
        except:
            await self.send_ephemeral("There was an error creating the validation request with cloudflare. "
                                      "Please contact ~HELP to get this resolved.", event)

    async def send_ephemeral(self, message, event):
        self.driver.respond_to_web(
            event,
            {
                "ephemeral_text": message,
            }
        )

    async def message_confirm_verification(self, source_email, event, user_id):
        actions = [
            {
                "id": 'hooks',
                "name": "Confirm cloudflare verification is complete",
                "integration": {
                    "url": f"{OP_URL_PREFIX}/hooks/confirm_email",
                    "context": {
                        "user_id": user_id,
                        "source_email": source_email,
                    }
                }
            },
        ]
        self.driver.respond_to_web(
            event,
            {
                "update": {
                    "message": "An email from cloudflare was sent to your email address for verification.\n"
                               f"Please complete the process and click the button below to finish setting up "
                               f"forwarding for {source_email}.",
                    "props": {
                        "attachments": [
                            {
                                "actions": actions
                            }
                        ]
                    }
                },
            },
        )

    async def send_verification_request(self, source_email, user_id):
        actions = [
            {
                "id": 'hooks',
                "name": 'Send cloudflare verification email',
                "integration": {
                    "url": f"{OP_URL_PREFIX}/hooks/send_email",
                    "context": {
                        "user_id": user_id,
                        "source_email": source_email,
                    }
                }
            },
        ]
        return send_message(
            self.driver,
            user_id,
            f"I've matched {source_email} with your account.\n"
            f"Next, verify your email with cloudflare (use the button below).",
            actions=actions
        )

    async def send_message_verify_or_done(self, source_email, target_email, user_id):
        if not cf_check_validation(target_email):
            nix_url = await self.send_verification_request(source_email, user_id)
        else:
            cf_create_email_forward(source_email, target_email)
            nix_url = await self.send_forward_complete(source_email, user_id=user_id)
        return nix_url

    async def send_forward_complete(self, source_email, event=None, user_id=None):
        message = f"Emails to {source_email} will now be forwarded to your email :tada:"
        if event:
            self.driver.respond_to_web(
                event,
                {
                    "update": {
                        "message": message,
                        "props": {},
                    },
                },
            )
        else:
            return send_message(self.driver, user_id, message)


def get_bot():
    return setup_routes(Bot(plugins=[EmailManagerBot()]))
