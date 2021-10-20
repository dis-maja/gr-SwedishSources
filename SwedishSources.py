# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2018       Mats O Jansson
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# $Id$
"""
Swedish Sources module
"""
#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------

#------------------------------------------------------------------------
#
# Gtk modules
#
#------------------------------------------------------------------------
from gi.repository import Gtk

#------------------------------------------------------------------------
#
# GRAMPS modules
#
#------------------------------------------------------------------------
#from gramps.gen.db import DbTxn
#from gramps.gen.lib import Address
#from gramps.gen.lib import RepoRef
#from gramps.gen.lib import Repository, RepositoryType
#from gramps.gen.lib import Url, UrlType
#from gramps.gen.lib import Source
#from gramps.gen.lib import SrcAttribute, SrcAttributeType
from gramps.gen.plug import Gramplet
from gramps.gen.config import config as configman
from gramps.gen.const import GRAMPS_LOCALE as glocale

from behave import BehaviourPage
from bookdb import BookdbPage
from repo import RepoPage
from src import SourcePage

try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext
config = configman.register_manager("SwedishSources")
config.register("bookdb.url", "")
config.register("bookdb.username", "")
config.register("bookdb.password", "")
config.register("behavior.repo_i8n", False)
config.register("behavior.sour_country", False)
config.register("behavior.sour_i8n", False)
config.register("behavior.sour_avoid_signum", False)
config.load()
config.save()

#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------

class SwedishSources(Gramplet):
    """
    Gramplet for fetching swedish sources
    """

    __debug = True
    pages = {'bookdb': None,
             'behave': None,
             'repo': None,
             'sour': None}

    def __print(self, str):
        """
        print debug info
        """
        if self.__debug:
            print(str)

    def init(self):
        """
        Set up the GUI
        """
        self.__print('SwedishSources::init')

        self.set_text(_('No Family Tree loaded.'))

        #
        # Get bookDB settings
        #
        self.pages['bookdb'] = BookdbPage(self, config)
        self.setup_bookdb()

        #
        # Get behaviour settings
        #
        self.pages['behave'] = BehaviourPage(self, config)
        self.setup_behave()

        #
        # Check if we can communicate with the server
        # If status is OK then we have connection
        #
        if self.pages['bookdb'].check_bookdb():
            status = ""
            if not self.pages['bookdb'].query_test():
                status = self.pages['bookdb'].get_status()
            else:
                if 'status' in self.pages['bookdb'].answer:
                    status = self.pages['bookdb'].answer['status']

                #
                #
                #
                self.pages['repo'] = RepoPage(self, config)
                self.pages['sour'] = SourcePage(self, config)

        else:
            status = _('Incomplete configuration')

        notebook = Gtk.Notebook()

        if status != 'OK':
            self.page_error = Gtk.Box()
            self.page_error.set_border_width(10)
            self.page_error.add(Gtk.Label(status))
            notebook.append_page(self.page_error, Gtk.Label(_('Error')))

            notebook.append_page(self.pages['bookdb'].build_page(),
                                 Gtk.Label(_('bookDB')))
        else:
            notebook.append_page(self.pages['sour'].build_page(),
                                 Gtk.Label(_('Sources')))

            notebook.append_page(self.pages['repo'].build_page(),
                                 Gtk.Label(_('Repositories')))

            notebook.append_page(self.pages['behave'].build_page(),
                                 Gtk.Label(_('Settings')))

            notebook.append_page(self.pages['bookdb'].build_page(),
                                 Gtk.Label(_('bookDB')))

        notebook.connect('switch-page', self.change_page)
#        notebook.set_scrollable(False)

        self.gui.get_container_widget().remove(self.gui.textview)
        self.gui.get_container_widget().add_with_viewport(notebook)

        self.__print('SwedishSources::init done')

    def setup_behave(self):
        """
        Setup variables used by behaviour
        """
        self.pages['behave'].set_repo_i8n(config.get('behavior.repo_i8n'))
        self.pages['behave'].set_sour_country(config.get('behavior.sour_country'))
        self.pages['behave'].set_sour_i8n(config.get('behavior.sour_i8n'))
        self.pages['behave'].set_sour_avoid_signum(config.get('behavior.sour_avoid_signum'))

    def setup_bookdb(self):
        """
        Setup variables used by server communication
        """
        self.pages['bookdb'].set_url(config.get('bookdb.url'))
        self.pages['bookdb'].set_username(config.get('bookdb.username'))
        self.pages['bookdb'].set_password(config.get('bookdb.password'))
        self.pages['bookdb'].update_basic_auth()
        self.pages['bookdb'].set_nothidden(False)

    def main(self):
        """
        main task
        """
        self.__print('SwedishSources::main')
        if not self.pages['repo'] is None:
            self.pages['repo'].update_store()
        if not self.pages['sour'] is None:
            self.pages['sour'].sour_update_index()
            self.pages['sour'].update_visibility()

    def db_changed(self):
        """
        Something changed in database
        """
        self.__print('SwedishSources::db_changed')
        if not self.pages['repo'] is None:
            self.dbstate.db.connect('repository-add', self.pages['repo'].update)
            self.dbstate.db.connect('repository-delete', self.pages['repo'].update)
            self.dbstate.db.connect('repository-update', self.pages['repo'].update)
        if not self.pages['sour'] is None:
            self.dbstate.db.connect('source-add', self.pages['sour'].update)
            self.dbstate.db.connect('source-delete', self.pages['sour'].update)
            self.dbstate.db.connect('source-update', self.pages['sour'].update)

        if not self.pages['sour'] is None:
            self.pages['sour'].sour_update_index()
            self.pages['sour'].update_visibility()


    def on_save(self):
        """
        Gramps is exiting
        """
        self.__print('SwedishSources::on_save')
        config.save()

    def change_page(self, notebook, page, pagenum):
        """
        Change notebook page
        """
        self.__print("SwedishSources::change_page " + page.get_name())
        if page.get_name() == "Repository":
            self.pages['repo'].update_store()

    def hidden_widgets(self):
        """
        """
        self.__print('SwedishSources::hidden_widgets')

        return []
