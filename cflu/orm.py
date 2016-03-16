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
import re
import base64


# config
# ------
open_instance = None


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
# -------
class Instance(object):

    def __init__(self, url, username, password):
        global open_instance
        self.url = url
        self.api = '{}/rest/api'.format(self.url)
        self.headers = {
            'Authorization': 'Basic {}'.format(base64.b64encode(str.encode('{}:{}'.format(username, password))).decode('utf-8')),
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self._data = None
        open_instance = self
        return

    def update(self):
        req = urllib.request.Request(
            '{}/space'.format(self.api),
            headers=self.headers,
            method='GET'
        )
        data = {}
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        self._data = data['results']
        return

    @property
    def spaces(self):
        if self._data is None:
            self.update()
        return [Space(d['key'], d['name']) for d in self._data]


class Space(object):

    def __init__(self, key, name=None):
        global open_instance
        self.key = key
        self.name = name
        self.instance = open_instance
        self._data = None
        return

    def update(self):
        req = urllib.request.Request(
            '{}/space/{}/content'.format(self.instance.api, self.key),
            headers=self.instance.headers,
            method='GET'
        )
        data = {}
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        self._data = data['page']['results']
        return

    @property
    def pages(self):
        if self._data is None:
            self.update()
        return [Page(d['id']) for d in self._data]


class Page(object):

    def __init__(self, ident):
        global open_instance
        self.ident = ident
        self.instance = open_instance
        self._data = None
        self._children = None
        self._body_cache = None
        return

    @classmethod
    def create_new(cls, space, title, ident=None):
        tdata = {
            "type": "page",
            "title": title,
            "space": {
                "key": space
            },
            "body":{
                "storage":{
                    "representation":"storage",
                    "value":"<p>This is a new page</p>"
                }
            }
        }
        if ident is not None:
            tdata['space']['id'] = ident
        req = urllib.request.Request(
            '{}/content'.format(open_instance.api),
            data=bytes(json.dumps(tdata), 'utf-8'),
            headers=open_instance.headers,
            method='POST'
        )
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        return cls(data['id'])

    def update(self):
        req = urllib.request.Request(
            '{}/content/{}?expand=body.view,version,space'.format(self.instance.api, self.ident),
            headers=self.instance.headers,
            method='GET'
        )
        data = {}
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        self._data = data
        return

    def update_children(self):
        req = urllib.request.Request(
            '{}/content/{}/child/page'.format(self.instance.api, self.ident),
            headers=self.instance.headers,
            method='GET'
        )
        data = {}
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        self._children = data['results']
        return

    @property
    def body(self):
        if self._data is None:
            self.update()
        return self._data['body']['view']['value'] if self._body_cache is None else self._body_cache

    @body.setter
    def body(self, value):
        self._body_cache = value
        return

    @property
    def name(self):
        if self._data is None:
            self.update()
        return self._data['title']

    @property
    def space(self):
        if self._data is None:
            self.update()
        return self._data['space']['key']

    @property
    def children(self):
        if self._children is None:
            self.update_children()
        return [Page(d['id']) for d in self._children]

    def push(self):
        if self._data is None:
            self.update()
        # STOPPED HERE .. NEED TO INCREMENT VERSION NUMBER
        self._data['version']['number'] += 1
        tdata = {
            "id": str(self.ident),
            "type": "page",
            "title": self._data['title'],
            "version": { "number": str(self._data['version']['number']) },
            "body": {
                "storage": {
                    "representation": "storage",
                    "value": re.sub(r"[\n\t]", "", self._body_cache),
                }
            }
        }
        req = urllib.request.Request(
            '{}/content/{}'.format(self.instance.api, self.ident),
            data=bytes(json.dumps(tdata), 'utf-8'),
            headers=self.instance.headers,
            method='PUT'
        )
        urllib.request.urlopen(req)
        return

    def delete(self):
        req = urllib.request.Request(
            '{}/content/{}'.format(open_instance.api, self.ident),
            headers=open_instance.headers,
            method='DELETE'
        )
        with urllib.request.urlopen(req) as rdata:
            data = json.loads(rdata.read().decode('utf-8'))
        return

