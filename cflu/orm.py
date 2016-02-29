# -*- coding: utf-8 -*-
#
# object model for interacting with confluence
#
# @author <bprinty@gmail.com>
# ----------------------------------------------------------


# imports
# -------
import urllib # python 2/3 problems
import json
import base64


# decorators
# ----------
class cached_property(object):
    """
    Caching for class properties. This was taken from:

    https://github.com/pydanny/cached-property
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


# classes
# ---------
class Instance(object):

    def __init__(self, url, username, password):
        self.url = url
        self.api = '{}/rest/api'.format(self.url)
        self.headers = {
            'Authorization': 'Basic {}'.format(base64.b64encode(str.encode('{}:{}'.format(username, password))).decode('utf-8')),
            'Accept': 'application/json'
        }
        print(self.headers)
        return

    @cached_property
    def content(self):
        req = urllib.request.Request(
            '{}/content'.format(self.api),
            headers=self.headers,
            method='GET'
        )
        data = {}
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        return data


# functions
# ---------
def instance(config):
    print(config.get('username'))
    print(config.get('password'))
    return Instance(
        url='{}/confluence'.format(config.get('url')),
        username=config.get('username'),
        password=config.get('password')
    )

