import sys
import os

if sys.version_info[0] < 3:
    from io import open


host = 'https://cdapi.clarify.io'


def load_body(filename):
    text = None
    with open(os.path.join('.', 'tests', 'data', filename), encoding="utf-8") as f:
        text = f.read()
    return text if text else '{}'


def register_uris(httpretty):

    httpretty.register_uri('POST', host + '/v1/conversations',
                           body=load_body('conversation.json'), status=201,
                           content_type='application/json')
