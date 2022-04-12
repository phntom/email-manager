import json
import re
from os import environ

import mattermost as mattermost
from CloudFlare import CloudFlare
from boto3.session import Session
from flask import Flask, redirect, request

app = Flask(__name__)

S3_ENDPOINT_URL = environ.get('S3_ENDPOINT_URL', None)
S3_BUCKET_NAME = environ.get('S3_BUCKET_NAME', '')
OP_SECRET = environ.get('OP_SECRET', '')
OP_URL_PREFIX = environ.get('OP_URL_PREFIX', '')
MATTERMOST_BOT_TOKEN = environ.get('MATTERMOST_BOT_TOKEN', '')
MATTERMOST_ENDPOINT = environ.get('MATTERMOST_ENDPOINT', 'https://kix.co.il')
MATTERMOST_TEAM_ID = environ.get('MATTERMOST_TEAM_ID', '')
CLOUDFLARE_TOKEN = environ.get('CLOUDFLARE_TOKEN', '')
CLOUDFLARE_ACCOUNT = environ.get('CLOUDFLARE_ACCOUNT', '')
CLOUDFLARE_EMAIL = environ.get('CLOUDFLARE_EMAIL', '')

s3 = Session().resource(service_name='s3', endpoint_url=S3_ENDPOINT_URL)
mm = mattermost.MMApi(f"{MATTERMOST_ENDPOINT}/api")
mm.login(bearer=MATTERMOST_BOT_TOKEN)


def get_token(token):
    if not re.match('^[a-z0-9]+$', token):
        return {}
    response = s3.Object(bucket_name=S3_BUCKET_NAME, key=f'tokens/{token}').get()
    data = response['Body'].read()
    return json.loads(data)


def put_token(token, j):
    if not re.match('^[a-z0-9]+$', token):
        return
    content = json.dumps(j)
    s3.Object(bucket_name=S3_BUCKET_NAME, key=f'tokens/{token}').put(Body=content)


def get_target_userid(email):
    # noinspection PyProtectedMember
    return mm._get("/v4/users/email/" + email)['id']


def get_current_email(user_id):
    return mm.get_user(user_id)['email']


def send_message(user_id, message, actions=None):
    target_channel = mm.create_dm_channel_with(user_id)
    if actions is None:
        actions = ()
    props = {
        "from_webhook": "false",
        "attachments": [{"actions": [action for action in actions]}],
    }
    mm.create_post(
        channel_id=target_channel['id'], message=message, props=props
    )
    team_name = mm.get_team(MATTERMOST_TEAM_ID)['name']
    return f"{MATTERMOST_ENDPOINT}/{team_name}/channels/{target_channel['name']}"


def add_to_my_team(user_id):
    mm.add_user_to_team(user_id=user_id, team_id=MATTERMOST_TEAM_ID)


@app.before_request
def before_request_func():
    if request.headers.get('X-Auth-Request-Email', ''):
        return
    if request.method == "POST":
        data = request.json()
        if "trigger_id" in data:
            return
    return "Request is not authorized"


@app.route("/")
def root():
    return redirect(MATTERMOST_ENDPOINT)


@app.route("/health")
def health():
    mm.get_user()
    return "OK"


@app.route('/match_email/<string:token>')
def match(token):
    j = get_token(token)
    email = request.headers['X-Auth-Request-Email']
    user_id = get_target_userid(email)
    if j.get('matched'):
        if user_id == j.get('user_id'):
            return redirect(send_message(user_id, "This link was already matched to your account."))
        else:
            return redirect(send_message(user_id, "This link was used from another account, "
                                                  "contact ~HELP to get this sorted."))

    add_to_my_team(user_id)
    alias = j['alias']
    j['matched'] = True
    j['user_id'] = user_id
    put_token(token, j)
    url = f"{OP_URL_PREFIX}/send_email/{token}"
    actions = [
        {
            "id": 'send_email',
            "name": f'Send cloudflare verification email',
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
        user_id,
        f"I've matched {alias}@nix.co.il with your account.\n"
        f"Next, click the button at the bottom of this message to get a verification email from cloudflare.\n"
        f"You will only be sent a single email per address. You must complete verification to receive emails.",
        actions=actions
    ))


@app.route('/send_email/<string:token>', methods=['GET', 'POST'])
def send(token):
    j = get_token(token)
    user_id = j.get('user_id')
    # noinspection PyBroadException
    try:
        email = get_current_email(user_id)
        cf = CloudFlare(email=CLOUDFLARE_EMAIL, token=CLOUDFLARE_TOKEN)
        cf.add('VOID', "accounts", "email-fwdr")
        cf.add('AUTH', "accounts", "email-fwdr", "addresses")
        # noinspection PyUnresolvedReferences
        cf.accounts.email_fwdr.addresses.post(CLOUDFLARE_ACCOUNT, data=json.dumps({"email": email}))
        j['validated'] = email
        put_token(token, j)
        return json.dumps({
            "update": {
                "message": "An email from Cloudflare was dispatched (once) to your email address, "
                           "please complete the process.",
                "props": {}
            },
        })
    except:
        return json.dumps({
            "ephemeral_text": "There was an error creating the validation request with cloudflare. "
                              "Please contact ~HELP to get this resolved.",
        })


@app.route('/create_token/<string:token>/<string:secret>/<string:alias>')
def create(token, secret, alias):
    if secret != OP_SECRET:
        return "wrong secret"
    if not re.match('^[a-z0-9]+$', token):
        return "bad token"
    j = {
        'matched': False,
        'alias': alias,
    }
    put_token(token, j)
    return token


if __name__ == '__main__':
    app.run(host="0.0.0.0")
