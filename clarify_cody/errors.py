import json

#
# Exceptions.
#

KEY_STATUS = 'status'
KEY_MESSAGE = 'message'
KEY_CODE = 'code'


class APIException(Exception):
    def get_message(self):
        return 'API Exception'


class APIRequestException(APIException):
    """Thown when we don't receive the expected sucess response from an
    API call."""

    _data_struct = None
    http_response = None
    json_response = None

    def __init__(self, http_response, json_response):
        APIException.__init__(self)

        self.http_response = http_response
        self.json_response = json_response

        #  Try to turn the JSON and turn it into something we can use.
        #  Could be garbage, in which case we should just ignore it.
        try:
            self._data_struct = json.loads(json_response)
        except ValueError:
            pass

    def get_http_response(self):
        """Return the HTTP response that caused this exception to be
        thrown."""
        return self.http_response

    def get_status(self):
        """Return the status embedded in the JSON error response body,
        or an empty string if the JSON couldn't be parsed."""

        result = ''
        if self._data_struct is not None:
            result = self._data_struct[KEY_STATUS]
        return result

    def get_message(self):
        """Return the message embedded in the JSON error response body,
        or an empty string if the JSON couldn't be parsed."""

        result = ''
        if self._data_struct is not None:
            result = self._data_struct[KEY_MESSAGE]
        return result

    def get_code(self):
        """Return the code embedded in the JSON error response body,
        or an empty string if the JSON couldn't be parsed. This
        should always match the 'http_response'."""

        result = ''
        if self._data_struct is not None:
            result = self._data_struct[KEY_CODE]
        return result


class APIDataException(APIException):
    """Thown when we can't parse the data returned by an API call."""

    base_exception = None
    offending_data = None
    msg = None

    def __init__(self, e=Exception, offending_data=None, msg=None):
        """Initializer.
        'msg' is additional information that might be valuable for
        determining the root cause of the exception."""

        APIException.__init__(self)

        self.base_exception = e
        self.offending_data = offending_data
        self.msg = msg

    def get_offending_data(self):
        """Returns the JSON data that caused the exception to be thrown
        in the first place."""

        return self.offending_data

    def get_base_exception(self):
        """Returns the exception that was oritinally thrown and caught
        which in turn generated this one. Unlikely to be useful."""

        return self.base_exception

    def get_message(self):
        """Return whateve message the application programmer might have
        considered useful when throwing this exception."""

        return self.msg
