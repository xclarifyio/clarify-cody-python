"""
.. module:: clarify_cody
   : synopsis: 'Clarify Conversation Dynamics API client'
"""

import sys
import collections
import json
import urllib3
import certifi
try:
    from urllib.parse import urlparse, parse_qs
except ImportError:
    from urlparse import urlparse, parse_qs

from .errors import APIRequestException, APIDataException

from clarify_cody.constants import __version__
from clarify_cody.constants import __api_version__
from clarify_cody.constants import __api_lib_name__
from clarify_cody.constants import __host__


CONVERSATIONS_PATH = 'conversations'
PYTHON_VERSION = '.'.join(str(i) for i in sys.version_info[:3])

#
# Client.
#


class Client(object):
    """Holds the environment."""

    def __init__(self, key, host=None, tls=True):
        """
        host can be a hostname or host:port or https://host:port
        """
        self.key = key

        if host is None:
            host = __host__

        if host.find('http://') == 0:
            host = host[7:]
            tls = False
        elif host.find('https://') == 0:
            host = host[8:]
            tls = True

        if tls:
            self.conn = urllib3.HTTPSConnectionPool(host, maxsize=1,
                                                    cert_reqs='CERT_REQUIRED',
                                                    ca_certs=certifi.where())
        else:
            self.conn = urllib3.HTTPConnectionPool(host, maxsize=1)

        self._last_status = None
        self.user_agent = (__api_lib_name__ + '/' + __version__ + '/' + PYTHON_VERSION)

    def get_conversation_list(self, href=None, limit=None):

        """Get a list of conversations.
        'href' the relative href to the conversation list to retriev. If None,
        the first conversation list will be returned.
        'limit' the maximum number of conversations to include in the result.

        NB: providing values for 'limit', 'embed_*' will override either
        the API default or the values in the provided href.

        Returns a dict equivalent to the JSON returned by the API.
        If the response status is not 2xx, throws an APIRequestException.
        If the JSON to python data struct conversion fails, throws an
        APIDataException."""

        # Argument error checking.
        assert limit is None or limit > 0

        j = None
        if href is None:
            j = self._get_conversation_list_first(limit)
        else:
            j = self._get_conversation_list_next(href, limit)

        return self._parse_json(j)

    def _get_conversation_list_first(self, limit=None):
        """Get a list of conversations.
        'limit' may be None, which implies API default.  If not None,
        must be > 1.
        'embed' a list of entities to embed in the result.

        Returns the raw JSON returned by the API.
        If the response status is not 2xx, throws an APIRequestException."""

        # Prepare the data we're going to include in our query.
        path = '/' + __api_version__ + '/' + CONVERSATIONS_PATH

        data = None
        fields = {}
        if limit is not None:
            fields['limit'] = limit

        if len(fields) > 0:
            data = fields

        raw_result = self.get(path, data)

        if raw_result.status < 200 or raw_result.status > 202:
            raise APIRequestException(raw_result.status, raw_result.json)
        else:
            result = raw_result.json

        return result

    def _get_conversation_list_next(self, href=None, limit=None):
        """Get next, previous, first, last list (page) of conversations.
        'href' the href to retrieve the conversations.
        All other arguments override arguments in the href.

        Returns the raw JSON returned by the API.
        If the response status is not 2xx, throws an APIRequestException."""

        url_components = urlparse(href)
        path = url_components.path
        data = parse_qs(url_components.query)

        # Change all lists into discrete values.
        for key in data.keys():
            data[key] = data[key][0]

        # Deal with limit overriding.
        if limit is not None:
            data['limit'] = limit

        raw_result = self.get(path, data)

        if raw_result.status < 200 or raw_result.status > 202:
            raise APIRequestException(raw_result.status, raw_result.json)
        else:
            result = raw_result.json

        return result

    def conversation_list_map(self, func, conversation_collection=None):
        """
        Execute func on every conversation in a collection.

        Func will be called as func(client, conversation_href).

        If conversation_collection is None, all conversations will be
        iterated.
        Otherwise, conversation_collection can be the model returned from
        a call to get_conversation_list().

        If func returns False, the iteration is stopped.

        Returns the number of conversations iterated.
        """
        has_next = True
        next_href = None  # if None, retrieves first page
        stopped = False
        total = 0

        while has_next and not stopped:
            # Get a page and perform the requested function.
            if conversation_collection is None:
                conversation_collection = self.get_conversation_list(next_href)

            for i in conversation_collection['_links']['items']:
                href = i['href']
                total += 1
                if func(self, href) is False:
                    stopped = True
                    break
            # Check for following page.
            if not stopped:
                next_href = None
                if 'next' in conversation_collection['_links']:
                    next_href = conversation_collection['_links']['next']['href']
                    conversation_collection = None
                if next_href is None:
                    has_next = False
        return total

    def get_last_status(self):
        """Returns the HTTP status code of the most recent request made
        by the client."""
        return self._last_status

    def create_conversation(self, external_id=None, participants=None, options=None, notify_url=None):
        """Create a new conversation.
        'external_id' can be any id
        'participants' is an array of dicts: 'name' (identifier for participant) and 'media'
        (an array of a dict: 'url' (url to the media file), 'audio_channel' ('left' | 'right' | '')
        'options' is a dict of options
        notify_url - a webhook url to post to when processing is complete.

        Returns a data structure equivalent to the JSON returned by the API.
        If the response status is not 2xx, throws an APIRequestException.
        If the JSON to python data struct conversion fails, throws an
        APIDataException."""

        path = '/' + __api_version__ + '/' + CONVERSATIONS_PATH

        data = None

        fields = {}
        if external_id is not None:
            fields['external_id'] = external_id
        if participants is not None:
            fields['participants'] = participants
        if options is not None:
            fields['options'] = options
        if notify_url is not None:
            fields['notify_url'] = notify_url

        if len(fields) > 0:
            data = fields

        raw_result = self.post(path, data)

        if raw_result.status < 200 or raw_result.status > 202:
            raise APIRequestException(raw_result.status, raw_result.json)

        return self._parse_json(raw_result.json)

    def get_conversation(self, href=None, embed=None):
        """Get a conversation.
        'href' the relative href to the conversation. May not be None.
        'embed' a list of entities to embed in the result.

        Returns a data structure equivalent to the JSON returned by the API.
        If the response status is not 2xx, throws an APIRequestException.
        If the JSON to python data struct conversion fails, throws an
        APIDataException."""

        # Argument error checking.
        assert href is not None

        data = None
        fields = {}

        if embed is not None:
            fields['embed'] = '+'.join(embed)

        if len(fields) > 0:
            data = fields

        raw_result = self.get(href, data)

        if raw_result.status < 200 or raw_result.status > 202:
            raise APIRequestException(raw_result.status, raw_result.json)

        return self._parse_json(raw_result.json)

    def get_conversation_for_external_id(self, external_id, embed=None):
        """Get a conversation.
        'external_id' an external_id for the conversation
        'embed' a list of entities to embed in the result.

        Returns a data structure equivalent to the JSON returned by the API.
        If the response status is not 2xx, throws an APIRequestException.
        If the JSON to python data struct conversion fails, throws an
        APIDataException."""

        # Argument error checking.
        assert external_id is not None

        path = '/' + __api_version__ + '/' + CONVERSATIONS_PATH

        data = None
        fields = {
            'external_id': external_id
        }

        if embed is not None:
            fields['embed'] = '+'.join(embed)

        if len(fields) > 0:
            data = fields

        raw_result = self.get(path, data)

        if raw_result.status < 200 or raw_result.status > 202:
            raise APIRequestException(raw_result.status, raw_result.json)

        return self._parse_json(raw_result.json)

    def delete_conversation(self, href=None):
        """
        Delete a conversation.
        :param href: the relative href to the conversation.
        :type href: string, may not be None
        :return: nothing
        :raises APIRequestException: If the response code is not 204.
        """

        # Argument error checking.
        assert href is not None

        raw_result = self.delete(href)

        if raw_result.status != 204:
            raise APIRequestException(raw_result.status, raw_result.json)

    def _get_simple_model(self, href=None):
        """Get a model
        'href' the relative href to the model. May not be None.

        Returns a data structure equivalent to the JSON returned by the
        API.

        If the response status is not 2xx, throws an APIRequestException.
        If the JSON to python data struct conversion fails, throws an
        APIDataException."""

        # Argument error checking.
        assert href is not None

        raw_result = self.get(href)

        if raw_result.status < 200 or raw_result.status > 202:
            raise APIRequestException(raw_result.status, raw_result.json)

        return self._parse_json(raw_result.json)

    def _get_headers(self):
        """Get all the headers we're going to need:
        1. Authorization
        2. Content-Type
        3. User-agent
        Note that the User-agent string contains the library name, the
        libary version, and the python version. This will help us track
        what people are using, and where we should concentrate our
        development efforts."""

        headers = {'User-Agent': self.user_agent,
                   'Content-Type': 'application/json'}
        if self.key:
            headers['Authorization'] = 'Bearer ' + self.key
        return headers

    def get(self, path, data=None):
        """Executes a GET.
        'path' may not be None. Should include the full path to the
        resource.
        'data' may be None or a dictionary. These values will be
        appended to the path as key/value pairs.

        Returns a named tuple that includes:
        status: the HTTP status code
        json: the returned JSON-HAL
        """

        # Argument error checking.
        assert path is not None

        response = self.conn.request('GET', path, data, self._get_headers())

        # Extract the result.
        self._last_status = response_status = response.status
        response_content = response.data.decode()

        return Result(status=response_status, json=response_content)

    def post(self, path, data):
        """Executes a POST.
        'path' may not be None, should not inlude a version number, and
        should not include a leading '/'
        'data' may be None or a dictionary.

        Returns a named tuple that includes:
        status: the HTTP status code
        json: the returned JSON-HAL
        """

        # Argument error checking.
        assert path is not None
        assert data is None or isinstance(data, dict)

        # Execute the request.
        if data is None:
            data = '{}'
        else:
            data = json.dumps(data)

        response = self.conn.request('POST', path, body=data, headers=self._get_headers())

        # Extract the result.
        self._last_status = response_status = response.status
        response_content = response.data.decode()

        return Result(status=response_status, json=response_content)

    def delete(self, path):
        """Executes a DELETE.
        'path' may not be None. Should include the full path to the
        resoure.

        Returns a named tuple that includes:
        status: the HTTP status code
        json: the returned JSON-HAL
        """

        # Argument error checking.
        assert path is not None

        # Execute the request.
        response = self.conn.request('DELETE', path, None,
                                     self._get_headers())

        # Extract the result.
        self._last_status = response_status = response.status
        response_content = response.data.decode()

        # return (status, json)
        return Result(status=response_status, json=response_content)

    def put(self, path, data):
        """Executes a PUT.
        'path' may not be None. Should include the full path to the
        resoure.
        'data' may be None or a dictionary.

        Returns a named tuple that includes:
        status: the HTTP status code
        json: the returned JSON-HAL
        """

        # Argument error checking.
        assert path is not None
        assert data is None or isinstance(data, dict)

        # Execute the request.
        if data is None:
            data = '{}'
        else:
            data = json.dumps(data)

        response = self.conn.request('PUT', path, body=data, headers=self._get_headers())

        # Extract the result.
        self._last_status = response_status = response.status
        response_content = response.data.decode()

        return Result(status=response_status, json=response_content)

    def _parse_json(self, jstring=None):
        """Parse jstring and return a Python data structure.
        'jstring' a string of JSON. May not be None.
        Returns a dict/array/string.
        If jstring couldn't be parsed, raises an APIDataException."""

        # Argument error checking.
        assert jstring is not None

        result = None

        try:
            result = json.loads(jstring)
        except (ValueError) as exception:
            msg = 'Unable to parse JSON.'
            raise APIDataException(exception, jstring, msg)

        return result


# This named tuple is returned by get(), put(), post(), delete()
# functions and consumed by the REST cover functions.
Result = collections.namedtuple('Result', ['status', 'json'])
