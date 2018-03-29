# Copyright 2014 Facebook, Inc.

# You are hereby granted a non-exclusive, worldwide, royalty-free license to
# use, copy, modify, and distribute this software in source code or binary
# form for use in connection with the web services and APIs provided by
# Facebook.

# As with any software that integrates with the Facebook platform, your use
# of this software is subject to the Facebook Developer Principles and
# Policies [http://developers.facebook.com/policy/]. This copyright notice
# shall be included in all copies or substantial portions of the software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import warnings
from facebookads import apiconfig
from facebookads.exceptions import FacebookBadObjectError


def warning(message):
    if apiconfig.ads_api_config['STRICT_MODE']:
        raise FacebookBadObjectError(message)
    else:
        warnings.warn(message)


class ApiContainer:
    """
        Represents container for API instances
    """

    def __init__(self, api_list):
        self.api_list = api_list.copy()
        self.awaiting_apis = []

    def get_api(self):
        if not self.api_list:
            self.api_list = self.awaiting_apis
            self.awaiting_apis = []
        return self.api_list[0]

    def to_awaiting(self, api):
        self.awaiting_apis.append(api)
        if api in self.api_list:
            self.api_list.remove(api)


def request_execution_retry(cls, delay=6, backoff=2, exception=Exception):
    """
    A retry decorator with exponential backoff.
    Retries a function or method if Exception occurred

    Args:
        tries: number of times to retry, set to 0 to disable retry
        delay: initial delay in seconds(can be float, eg 0.01 as 10ms),
            if the first run failed, it would sleep 'delay' second and try again
        backoff: must be greater than 1,
            further failure would sleep delay *= backoff second
    """
    import time

    if backoff <= 1:
        raise ValueError("backoff must be greater than 1")

    if delay <= 0:
        raise ValueError("delay must be greater than 0")

    def decorator(func):
        def wrapper(*args, **kwargs):
            _delay = delay
            api_container = cls.get_default_api_container()
            while True:
                try:
                    ret = func(*args, **kwargs)
                    return ret
                except exception as e:
                    time.sleep(_delay)
                    # wait longer after each failure
                    _delay *= backoff
                    api_container.to_awaiting(args[0]._api)
                    args[0]._api = api_container.get_api()
        return wrapper

    return decorator
