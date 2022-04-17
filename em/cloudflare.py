import json
from os import environ

from CloudFlare import CloudFlare

CLOUDFLARE_TOKEN = environ.get('CLOUDFLARE_TOKEN', '')
CLOUDFLARE_ACCOUNT = environ.get('CLOUDFLARE_ACCOUNT', '')
CLOUDFLARE_EMAIL = environ.get('CLOUDFLARE_EMAIL', '')

cf = CloudFlare(email=CLOUDFLARE_EMAIL, token=CLOUDFLARE_TOKEN)


def cf_send_validation(email):
    data = json.dumps({"email": email})
    # noinspection PyUnresolvedReferences
    cf.accounts.email_fwdr.addresses.post(CLOUDFLARE_ACCOUNT, data=data)
