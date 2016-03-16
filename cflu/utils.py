# -*- coding: utf-8 -*-
#
# utilities for confluence plugin
#
# @author <bprinty@gmail.com>
# ----------------------------------------------------------


# imports
# -------
import sublime
import os
import logging
import urllib # python 2/3 problems
import base64
import json
import re
from html.parser import HTMLParser


# config
# ------
active_window = None
current_instance = None
current_config = {}
existing_instances = []
page_cache = None

pwd = os.path.dirname(os.path.realpath(__file__))
server_path = os.path.join(os.path.join(pwd, '..'), 'servers')
tmp_path = os.path.join(pwd, '..', '.tmp')
if not os.path.exists(tmp_path):
    os.makedirs(tmp_path)

log_file = os.path.join(tmp_path, 'confluence.log')
logging.basicConfig(filename=log_file, level=logging.DEBUG)


# decorators
# ----------
def update_instancelist(func):
    def wrapper(*args, **kwargs):
        # read file list and update
        global existing_instances
        global server_path
        existing_instances = list(map(
            lambda x: x.replace('.json', ''),
            os.listdir(server_path)
        ))
        load_state()
        save_state()
        return func(*args, **kwargs)
    return wrapper


# functions
# ---------
def load_config(name):
    global current_config
    with open(os.path.join(server_path, name + '.json'), 'r') as fi:
        content = re.sub(r'[^:]//.+?\n', '', ''.join(fi.readlines()))
        content = re.sub(r'\s+', '', content)
        data = json.loads(content)
    current_config = data
    return

def save_state():
    global current_instance
    with open(os.path.join(tmp_path, 'state.json'), 'w') as fi:
        json.dump({'current_instance': current_instance}, fi)
    return

def load_state():
    global current_instance
    if current_instance is None:
        sfile = os.path.join(tmp_path, 'state.json')
        if os.path.exists(sfile):
            with open(sfile, 'r') as fi:
                current_instance = json.load(fi)['current_instance']
    return

def validate_config(config):
    if config.get('url') is None:
        return False
    if config.get('username') is None:
        return False
    if config.get('password') is None:
        return False
    try:
        req = urllib.request.Request(
            '{}/rest/api/space'.format(config.get('url')),
            headers={
                'Authorization': 'Basic {}'.format(base64.b64encode(
                    str.encode('{}:{}'.format(
                        config.get('username'),
                        config.get('password')
                    ))
                ).decode('utf-8')),
                'Accept': 'application/json'
            },
            method='GET'
        )
        urllib.request.urlopen(req)
    except urllib.error.HTTPError:
        return False
    return True


def show_quick_panel(items, callback, monospace=False):
    global active_window
    if active_window is not None:
        sublime.set_timeout(lambda: active_window.show_quick_panel(
            items,
            callback,
            monospace,
            -1
        ), 0)
    return


def show_input_panel(caption, text, callback):
  global active_window
  if active_window is not None:
    sublime.set_timeout(lambda: active_window.show_input_panel(
        caption,
        text,
        callback, None, None
    ), 0)
  return


# editors
# -------
class HTMLEditor(HTMLParser):
    _cache = ''
    _tabs = 0

    def handle_starttag(self, tag, attrs):
        self._cache += '\t'*self._tabs
        self._cache += '<{}'.format(tag)
        self._cache += ''.join([' {}="{}"'.format(i[0], i[1]) for i in attrs])
        self._cache += '>\n'
        self._tabs += 1

    def handle_endtag(self, tag):
        self._tabs -= 1
        self._cache += '\t'*self._tabs
        self._cache += '</{}>\n'.format(tag)

    def handle_data(self, data):
        self._cache += '\t'*self._tabs
        self._cache += '{}\n'.format(data)

    def parse(self, html):
        self._cache = ''
        self.feed(html)
        return re.sub("\n\s+\n", "\n", self._cache)


class MarkdownEditor(HTMLParser):
    pass


class Editors():
    html = HTMLEditor()
    markdown = MarkdownEditor()

editors = Editors()