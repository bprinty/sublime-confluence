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
import json
import re


# config
# ------
active_window = None
current_instance = None
existing_instances = []

pwd = os.path.dirname(os.path.realpath(__file__))
server_path = os.path.join(os.path.join(pwd, '..'), 'servers')
log_path = os.path.join(os.path.join(pwd, '..'), 'confluence.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG)


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
        return func(*args, **kwargs)
    return wrapper


# functions
# ---------
def load_config(name):
    with open(os.path.join(server_path, name + '.json'), 'r') as fi:
        content = re.sub(r'[^:]//.+?\n', '', ''.join(fi.readlines()))
        content = re.sub(r'\s+', '', content)
        data = json.loads(content)
    return data


def validate_instance(name):
    
    def store_pass(passwd):
        data['password'] = passwd
        return data

    data = load_config(name)
    assert data.get('url') is not None, 'No URL defined!'
    assert data.get('username') is not None, 'No username defined!'
    if data.get('password') is None:
        return show_input_panel('Enter Password:', '', store_pass)
    return data


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
