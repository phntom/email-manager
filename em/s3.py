import json
import re
from os import environ

from boto3.session import Session

S3_ENDPOINT_URL = environ.get('S3_ENDPOINT_URL', None)
S3_BUCKET_NAME = environ.get('S3_BUCKET_NAME', '')

s3_session = Session().resource(service_name='s3', endpoint_url=S3_ENDPOINT_URL)


def get_token(token):
    if not re.match('^[a-z0-9]+$', token):
        return {}
    response = s3_session.Object(bucket_name=S3_BUCKET_NAME, key=f'tokens/{token}').get()
    data = response['Body'].read()
    return json.loads(data)


def put_token(token, j):
    if not re.match('^[a-z0-9]+$', token):
        return
    content = json.dumps(j)
    s3_session.Object(bucket_name=S3_BUCKET_NAME, key=f'tokens/{token}').put(Body=content)

