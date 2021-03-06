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
import xml.etree.ElementTree as etree

# internal
try:
    from .cflu import orm, utils
except (ImportError, ValueError):
    from cflu import orm, utils

utils = imp.reload(utils)
orm = imp.reload(orm)


# classes
# -------
class ConfluencePushPage(sublime_plugin.EventListener):
    """
    Perform operations after page save/close events.
    """

    def on_post_save_async(self, view):
        base = os.path.basename(view.file_name())
        if '.sublime-confluence-' in base:
            ident = int(base.replace('.sublime-confluence-', '').replace('.html', ''))
            page = orm.Page(ident)
            with open(view.file_name()) as fi:
                contents = fi.read()
            page.body = contents
            page.push()
        return
    
    def on_post_close_async(self, view):
        base = os.path.basename(view.file_name())
        if '.sublime-confluence-' in base:
            os.remove(base)
        return



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
    "editor": "html",
    // "editor": "markdown",

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
            if isinstance(idx, str):
                utils.current_config['password'] = idx
                if not utils.validate_config(utils.current_config):
                    utils.show_input_panel('Enter Password:', '', done)
                else:
                    self.window.run_command('confluence_navigate')
            elif idx >= 0:
                utils.current_instance = utils.existing_instances[idx]
                utils.load_config(utils.current_instance)
                if not utils.validate_config(utils.current_config):
                    utils.show_input_panel('Enter Password:', '', done)
                else:
                    self.window.run_command('confluence_navigate')
            return

        utils.show_quick_panel(utils.existing_instances, done, monospace=True)
        return


class ConfluenceNavigateCommand(sublime_plugin.WindowCommand):
    """
    Mode of interaction for package.
    """

    @utils.update_instancelist
    def run(self):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window
        self.instance = orm.Instance(
            url=utils.current_config.get('url'),
            username=utils.current_config.get('username'),
            password=utils.current_config.get('password')
        )
        self.instance.update()
        if utils.page_cache is None:
            self.space_navigate()
        else:
            self.page_navigate(**utils.page_cache)
        return

    def space_navigate(self):
        def done(idx):
            if idx < 0:
                utils.logging.info('Done navigating')
            else:
                self.page_navigate(self.instance.spaces[idx].pages)
            return
        utils.show_quick_panel([[d.key, d.name] for d in self.instance.spaces], done, monospace=True)
        return

    def page_navigate(self, pages, prev=None):
        utils.page_cache = {
            'pages': pages,
            'prev': prev
        }
        def done(idx):
            def edit(eidx):
                if eidx < 0:
                    utils.logging.info('Done navigating')
                elif idx == 0:
                    self.page_navigate(**utils.page_cache)
                elif eidx == 1:
                    utils.logging.info('Creating new child page')
                    self.window.run_command('confluence_new_page', {
                        'space': pages[idx-1].space,
                        'ident': pages[idx-1].ident
                    })
                elif eidx == 2:
                    utils.logging.info('Editing page')
                    tfile = os.path.join(utils.tmp_path, '.sublime-confluence-{}.html'.format(pages[idx-1].ident))
                    if os.path.exists(tfile):
                        os.remove(tfile)
                    with open(tfile, 'w') as fi:
                        fi.write(utils.editors.html.parse(pages[idx-1].body))
                    self.window.open_file(tfile)
                elif eidx == 3:
                    utils.logging.info('Deleting page')
                    pages[idx-1].delete()
                    # TODO: INCLUDE DELETE LOGIC
                elif eidx == 4:
                    utils.logging.info('Renaming page')
                return
            if idx < 0:
                utils.logging.info('Done navigating')
            elif idx == 0:
                if prev is None:
                    self.space_navigate()
                else:
                    self.page_navigate(prev)
            else:
                if len(pages[idx-1].children) > 1:
                    self.page_navigate(pages[idx-1].children, prev=pages)
                else:
                    utils.show_quick_panel([
                        ['..'],
                        ['New Child Page', 'create new child page'],
                        ['Edit Page', 'edit existing page in new tab'],
                        ['Delete Page', 'delete page on confluence'],
                        ['Rename Page', 'rename current page']
                    ], edit, monospace=True)
        utils.show_quick_panel(['..'] + [d.name for d in pages], done, monospace=True)
        return


class ConfluenceNewPageCommand(sublime_plugin.WindowCommand):
    """
    Create new child page.
    """

    def run(self, space, ident):
        """
        Main logic for managing quick panel.
        """
        utils.active_window = self.window

        def done(name):
            if name != '':
                page = orm.Page.create_new(space=space, title=name, ident=ident)
                utils.logging.info('Editing page')
                tfile = os.path.join(utils.tmp_path, '.sublime-confluence-{}.html'.format(page.ident))
                if os.path.exists(tfile):
                    os.remove(tfile)
                with open(tfile, 'w') as fi:
                    fi.write(utils.editors.html.parse(page.body))
                self.window.open_file(tfile)
            return

        utils.show_input_panel('Enter Name of New Page:', '', done)
        return

