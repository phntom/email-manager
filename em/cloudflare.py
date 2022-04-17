import json
from datetime import datetime, timedelta
from os import environ

from CloudFlare import CloudFlare

CLOUDFLARE_TOKEN = environ['CLOUDFLARE_TOKEN']
CLOUDFLARE_EMAIL = environ['CLOUDFLARE_EMAIL']
CLOUDFLARE_ACCOUNT = environ['CLOUDFLARE_ACCOUNT']
CLOUDFLARE_ZONE_ID = {d[0]: d[1] for d in map(lambda x: x.split('=', 2), environ['CLOUDFLARE_ZONE_IDS'].split(','))}

cf = CloudFlare(email=CLOUDFLARE_EMAIL, token=CLOUDFLARE_TOKEN)
verification_cache = {}
rules_cache = {}
cf_verification_last_updated = datetime.utcfromtimestamp(0)
cf_rules_last_updated = datetime.utcfromtimestamp(0)


def cf_send_validation(email):
    data = json.dumps({"email": email})
    cf.accounts.email_fwdr.addresses.post(CLOUDFLARE_ACCOUNT, data=data)


def cf_get_all_verifications():
    global verification_cache, cf_verification_last_updated
    if (datetime.now() - cf_verification_last_updated) > timedelta(seconds=15):
        cf_verification_last_updated = datetime.now()
        verification_cache = {
            'verified': set(),
            'unverified': set(),
        }
        for line in cf.accounts.email_fwdr.addresses.get(CLOUDFLARE_ACCOUNT):
            if line['verified'] is None:
                verification_cache['unverified'].add(line['email'])
            else:
                verification_cache['verified'].add(line['email'])
    return verification_cache


def cf_get_all_rules():
    global rules_cache, cf_rules_last_updated
    if (datetime.now() - cf_rules_last_updated) > timedelta(seconds=15):
        cf_rules_last_updated = datetime.now()
        rules_cache = {}
        for domain, zone_id in CLOUDFLARE_ZONE_ID.items():
            d = rules_cache[domain] = {}
            for line in cf.zones.email_fwdr.rules.get(zone_id):
                for action in line['actions']:
                    if action['type'] == 'forward':
                        for matcher in line['matchers']:
                            if matcher['type'] == 'literal' and matcher['field'] == 'to':
                                e = matcher['value']
                                for v in action['value']:
                                    d[e] = v
    return rules_cache


def cf_check_validation(email):
    sets = cf_get_all_verifications()
    if email in sets['verified']:
        return True
    elif email in sets['unverified']:
        return False
    else:
        return None


def cf_create_email_forward(source, target):
    domain = source.split('@', 2)[1]
    zone_id = CLOUDFLARE_ZONE_ID[domain]
    data = json.dumps(
        {
            "enabled": True,
            "name": "Rule created at " + str(datetime.now()),
            "actions": [
                {
                    "type": "forward",
                    "value": [target],
                }
            ],
            "matchers": [
                {
                    "type": "literal",
                    "field": "to",
                    "value": source,
                }
            ]
        }
    )
    cf.zones.email_fwdr.rules.post(zone_id, data=data)
