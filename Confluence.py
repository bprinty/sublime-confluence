# -*- coding: utf-8 -*-
#
# Object relational mapper for communicating with confluence.
#
# @author <bprinty@gmail.com>
# ----------------------------------------------------------


# imports
# -------
# external
import sublime, sublime_plugin
import logging
import imp
import os
import json

# internal
try:
    from .cflu import orm, utils
except (ImportError, ValueError):
    from cflu import orm, utils

utils = imp.reload(utils)
orm = imp.reload(orm)


# classes
# -------
class ConfluenceMenuCommand(sublime_plugin.WindowCommand):
    """
    Mode of interaction for package.
    """

    def run(self):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window
        
        def done(idx):
            if idx < 0:
                utils.logging.info('Done with menu')
            elif idx == 0:
                self.window.run_command('confluence_new')
            elif idx == 1:
                self.window.run_command('confluence_edit')
            elif idx == 2:
                self.window.run_command('confluence_select')
            return
        
        utils.show_quick_panel([
            ['Set Up Instance', 'set up a new confluence influence'],
            ['Edit Instance', 'edit configuration for existing confluence instance'],
            ['Select Server', 'select confluence instance to use']
        ], done)
        return


class ConfluenceNewCommand(sublime_plugin.WindowCommand):
    """
    Create new confluence instance configuration.
    """
    default_config = """
{
    // server
    "url": "http://user.atlassian.net",
    // "url": "http://host:port",

    // credentials
    "username": "user",
    "password": "password"
}
    """

    def run(self):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window

        def done(filename):
            if filename != '':
                if not os.path.exists(utils.server_path):
                    os.mkdir(utils.server_path)
                sfile = os.path.join(utils.server_path, filename + '.json')
                if not os.path.exists(sfile):
                    with open(sfile, 'w') as fi:
                        fi.write(self.default_config)
                self.window.open_file(sfile)
            return

        utils.show_input_panel("New server name:", '', done)
        return


class ConfluenceEditCommand(sublime_plugin.WindowCommand):
    """
    Edit existing confluence instance.
    """

    @utils.update_instancelist
    def run(self):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window

        def done(idx):
            if idx >= 0:
                self.window.open_file(os.path.join(
                    utils.server_path,
                    utils.existing_instances[idx] + '.json'
                ))
            return

        utils.show_quick_panel(utils.existing_instances, done)
        return


class ConfluenceSelectCommand(sublime_plugin.WindowCommand):
    """
    Select confluence instance for use.
    """

    @utils.update_instancelist
    def run(self):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window

        def done(idx):
            if idx >= 0:
                utils.current_instance = utils.existing_instances[idx]
                self.window.run_command('confluence_navigate')
            return

        utils.show_quick_panel(utils.existing_instances, done, monospace=True)
        return


class ConfluenceNavigateCommand(sublime_plugin.WindowCommand):
    """
    Mode of interaction for package.
    """

    def run(self):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window
        self.instance = orm.instance(utils.validate_instance(utils.current_instance))
        self.navigator()
        return

    def navigator(self):
        def done(idx):
            if idx < 0:
                utils.logging.info('Done navigating')
            else:
                utils.logging.info('Navigating to {}'.format(idx))
            return
        print(self.instance.content)
        utils.show_quick_panel(['..', 'page1', 'page2'], done, monospace=True)
        return

