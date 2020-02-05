#!/usr/bin/env python3
from clarify_cody import Client
from clarify_cody.helpers import get_embedded
from clarify_cody.errors import APIRequestException
import os
import sys
import argparse


API_KEY = os.environ['CODY_API_KEY']


def output_transcript(transcript):
    participants = transcript['participants']
    if len(participants):
        for p in participants:
            trans = p['transcript']
            for s, seg in enumerate(trans.get('segments', [])):
                if s > 0:
                    sys.stdout.write(' ')
                sentence = []
                for term in seg['terms']:
                    if len(sentence) > 0 and term.get('type') == 'mark':
                        sentence[-1] = sentence[-1] + term['term']
                    else:
                        sentence.append(term['term'])
                sys.stdout.write(' '.join(sentence))
            sys.stdout.write('\n\n')
        sys.stdout.write('\n')


def fetch_transcripts(url, count):
    processed = 0

    def process_conv(client, conversation_href):
        nonlocal processed
        processed += 1
        if processed > count:
            return False

        conv = client.get_conversation(conversation_href, embed=['insight:transcript'])
        transcript = get_embedded(conv, 'insight:transcript')
        if transcript is not None:
            output_transcript(transcript)

    try:
        client = Client(API_KEY, url)
        client.conversation_list_map(process_conv)
    except APIRequestException as e:
        sys.stderr.write("APIRequestException {}: {} {}\n".format(e.get_http_response(),
                                                                  e.get_message(),
                                                                  e.json_response))


def main():
    parser = argparse.ArgumentParser(description='Fetch all Cody transcripts. The number can be limited with the --max parameter.')
    parser.add_argument('--max', nargs='?', type=int, default=10, dest='count', metavar='N',
                        help='Max number of most recent transcripts to fetch')
    parser.add_argument('url', help='URL of the cody server, ex. https://cody.example.org')
    args = vars(parser.parse_args())

    count = args['count']
    url = args['url']

    fetch_transcripts(url, count)


if __name__ == "__main__":
    # execute only if run as a script
    main()
