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
BookDB module
"""
#------------------------------------------------------------------------
#
# Python modules
#
#------------------------------------------------------------------------
import base64
import json
import urllib

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
from gramps.gen.const import GRAMPS_LOCALE as glocale
try:
    _trans = glocale.get_addon_translator(__file__)
except ValueError:
    _trans = glocale.translation
_ = _trans.gettext
#------------------------------------------------------------------------
#
# Constants
#
#------------------------------------------------------------------------

SS_PROTOCOL_VERSION = '0.0.1'

SS_CMD_TEST = 0
SS_CMD_REPO = 1
SS_CMD_CNTY = 2
SS_CMD_ARCH = 3
SS_CMD_BTYP = 4
SS_CMD_BOOK = 5
SS_CMD_BREF = 6
SS_CMD_SCBK = 7
SS_CMD_SCBT = 8
SS_CMD_SCBA = 9

SS_CMD = ['TestSSPV', 'getRepositories',
          'getCounties', 'getArchives',
          'getBookTypes', 'getBooks',
          'getBookRefs', 'getSCBBooks',
          'getSCBBookTypes', 'getSCBArchive']

class BookdbPage():
    """
    Class for communication with the bookDB server
    """

    __config = None
    __debug = False
    __fields = {'url': Gtk.Entry(), 'username': Gtk.Entry(),
                'password': Gtk.Entry(), 'message': Gtk.Label()}
    __gramplet = None
    __values = {'url': "", 'username': "", 'password': "",
                'basic_auth': "", 'nothidden': False,
                'status': "", 'code': ""}
    answer = {}

    def __init__(self, gramplet, config):
        """
        init
        """
        self.__gramplet = gramplet
        self.__config = config

    def set_url(self, url):
        """
        Save url
        """
        self.__print('BookDB::set_url')

        self.__values['url'] = url

    def get_url(self):
        """
        Get url
        """
        self.__print('BookDB::get_url')

        return self.__values['url']

    def set_username(self, username):
        """
        Save username
        """
        self.__print('BookDB::set_username')

        self.__values['username'] = username

    def __get_username(self):
        """
        Get username
        """
        return self.__values['username']

    def set_password(self, password):
        """
        Save password
        """
        self.__print('BookDB::set_password')

        self.__values['password'] = password

    def __get_password(self):
        """
        Get password
        """
        return self.__values['password']

    def set_nothidden(self, value):
        """
        Save nothidden
        """
        self.__print('BookDB::set_nothidden')

        self.__values['nothidden'] = value

    def __get_nothidden(self):
        """
        Get not hidden
        """
        return self.__values['nothidden']

    def get_status(self):
        """
        Get status
        """
        self.__print('BookDB::get_status')

        return self.__values['status']

    def update_basic_auth(self):
        """
        Update basic authentication
        """
        self.__print('BookDB::update_basic_auth')

        if self.check_bookdb():
            auth = '%s:%s' % (self.__get_username(), self.__get_password())
            if auth.strip() == ':':
                self.__values['basic_auth'] = ''
            else:
                b64str = base64.standard_b64encode(auth.encode('utf-8'))
                self.__values['basic_auth'] = 'Basic %s' % b64str.decode('utf-8')
        else:
            self.__values['basic_auth'] = ''

    def check_bookdb(self):
        """
        Check if all components exists
        """
        self.__print('BookDB::check_bookdb')

        ret = self.get_url().strip() != ''
        ret = ret and self.__get_username().strip() != ''
        ret = ret and self.__get_password().strip() != ''

        return ret

    def __build_url(self, cmd, params):
        """
        Create an url string
        """
        url = self.__values['url'] + '?do=' + str(SS_CMD[cmd])
        url += "&sspv=" + SS_PROTOCOL_VERSION
        for key, val in params.items():
            url += "&" + key + "=" + val
        return url

    def __query(self, url):
        """
        Generic code for query to bookDB server
        """

        self.__values['status'] = ""
        self.__values['code'] = 0
        self.answer = {}

        try:
            req = urllib.request.Request(url)
        except ValueError as err:
            self.__values['status'] = _('Incomplete configuration')
            self.__values['code'] = -1
            return True

        if self.__values['basic_auth'] != '':
            req.add_header("Authorization", self.__values['basic_auth'])
        try:
            resp = urllib.request.urlopen(req)
            j = json.load(resp)
            if 'status' in j:
                if j['status'] != 'OK':
                    self.__values['code'] = -1
                self.__values['status'] = j['status']
        except urllib.error.HTTPError as err:
            if err.code == 401:
                self.__values['status'] = _('Authentication Required')
                self.__values['code'] = err.code
                j = {'status': self.__values['status'], 'code': self.__values['code']}
            elif err.code == 404:
                self.__values['status'] = _('Unknown Page')
                self.__values['code'] = err.code
                j = {'status': self.__values['status'], 'code': self.__values['code']}
            elif err.code == 500 or err.code == 503:
                self.__values['status'] = err.reason
                self.__values['code'] = err.code
                j = {'status': self.__values['status'], 'code': self.__values['code']}
            else:
                raise

        self.answer = j

        return self.__values['code'] != 0

    def query_archive(self, aid):
        """
        Make a query about an archive
        """
        self.__print('BookDB::query_archive')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_ARCH, {'aid': str(aid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_archives(self, cid):
        """
        Make a query about all known counties
        """
        self.__print('BookDB::query_archives')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_ARCH, {'cid': str(cid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_book(self, bid):
        """
        Make a query about a book
        """
        self.__print('BookDB::query_book')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_BOOK, {'bid': str(bid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_bookrefs(self, bid):
        """
        Make a query about all known book ref in NAD
        """
        self.__print('BookDB::query_bookrefs')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_BREF, {'bid': str(bid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_books(self, aid):
        """
        Make a query about all known books in an archive
        """
        self.__print('BookDB::query_books')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_BOOK, {'aid': str(aid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_booktypes_arch(self, aid):
        """
        Make a query about all known booktypes in an archive
        """
        self.__print('BookDB::query_booktypes_arch')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_BTYP, {'aid': str(aid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_counties(self):
        """
        Make a query about all known counties
        """
        self.__print('BookDB::query_counties')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_CNTY, {})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_repositories(self):
        """
        Make a query about all known counties
        """
        self.__print('BookDB::query_repositories')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_REPO, {})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_repository(self, rin):
        """
        Make a query about all known counties
        """
        self.__print('BookDB::query_repository')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_REPO, {'rin': rin})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_scb_archive(self):
        """
        Make a query about an archive
        """
        self.__print('BookDB::query_scb_archive')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_SCBA, {})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_scb_booktypes(self):
        """
        Make a query about all known booktypes in an archive
        """
        self.__print('BookDB::query_scb_booktypes')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_SCBT, {})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_scb_books(self, cid):
        """
        Make a query about all known books in an archive
        """
        self.__print('BookDB::query_scb_books')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_SCBK, {'cid': str(cid)})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return {}
        else:
            return self.answer

    def query_test(self):
        """
        Make a simpel ping to the server to check connection
        """
        self.__print('BookDB::query_test')

        self.__values['status'] = ""
        self.__values['code'] = -1
        url = self.__build_url(SS_CMD_TEST, {})

        if self.__query(url):
            print("Error: ", self.__values['status'], self.__values['code'])
            return None
        else:
            return self.answer

    @staticmethod
    def __create_label(field, xalign=None):
        """
        Create a label
        """
        label = Gtk.Label()
        label.set_markup('<b>%s</b>' % field)
        if not xalign is None:
            label.set_xalign(xalign)
        return label

    def build_page(self):
        """
        Add the bookDB notebook page
        """
        self.__print("BookDB::build_page:")

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                       spacing=6, border_width=10, name='bookDB')

        label1 = self.__create_label(_('bookDB settings'))
        page.add(label1)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)

        label1 = self.__create_label(_('URL'), 0.0)
        grid.add(label1)

        self.__fields['url'].set_width_chars(40)
        self.__fields['url'].set_text(self.get_url())
        self.__fields['url'].connect("activate", self.__changed_url)
        grid.attach_next_to(self.__fields['url'], label1, Gtk.PositionType.RIGHT, 2, 1)

        label2 = self.__create_label(_('Username'), 0.0)
        grid.attach_next_to(label2, label1, Gtk.PositionType.BOTTOM, 1, 1)

        self.__fields['username'].set_text(self.__get_username())
        self.__fields['username'].connect("activate", self.__changed_username)
        grid.attach_next_to(self.__fields['username'], label2, Gtk.PositionType.RIGHT, 1, 1)

        label1 = self.__create_label(_('Password'), 0.0)
        grid.attach_next_to(label1, label2, Gtk.PositionType.BOTTOM, 1, 1)

        self.__fields['password'].set_text(self.__get_password())
        self.__fields['password'].connect("activate", self.__changed_password)
        self.__fields['password'].set_visibility(self.__get_nothidden())
        grid.attach_next_to(self.__fields['password'], label1, Gtk.PositionType.RIGHT, 1, 1)

        button1 = Gtk.CheckButton(_("Visible"), name="Visible")
#        button1.set_name("Visible")
        button1.set_active(self.__get_nothidden())
        button1.connect("toggled", self.__button_clicked)
        grid.attach_next_to(button1, self.__fields['password'], Gtk.PositionType.RIGHT, 1, 1)

        hbox = Gtk.Box(spacing=6)

        button2 = Gtk.Button.new_with_label(_('Save'))
        button2.set_name("Save")
        button2.connect("clicked", self.__button_clicked)
        hbox.pack_start(button2, True, True, 0)

        button1 = Gtk.Button.new_with_label(_('Test'))
        button1.set_name("Test")
        button1.connect("clicked", self.__button_clicked)
        hbox.pack_start(button1, True, True, 0)

        self.__fields['message'].set_text("")
        self.__fields['message'].set_property("width-request", 150)
        self.__fields['message'].set_justify(Gtk.Justification.LEFT)
        self.__fields['message'].set_xalign(0.0)
        hbox.pack_start(self.__fields['message'], True, True, 0)

        grid.attach_next_to(hbox, label1, Gtk.PositionType.BOTTOM, 3, 1)

        page.add(grid)

        return page

    def __changed_url(self, field):
        """
        Save url if field has changed
        """

        fld = field.get_text().strip()
        if fld != self.get_url():
            self.__config.set('bookdb.url', fld)
            self.set_url(fld)

    def __changed_username(self, field):
        """
        Save username if field has changed
        """

        fld = field.get_text().strip()
        if fld != self.__get_username():
            self.__config.set('bookdb.username', fld)
            self.set_username(fld)
            self.update_basic_auth()

    def __changed_password(self, field):
        """
        Save password if field has changed
        """

        fld = field.get_text().strip()
        if fld != self.__get_password():
            self.__config.set('bookdb.password', fld)
            self.set_password(fld)
            self.update_basic_auth()

    def __button_update(self):
        """
        Update content in config if button is pressed
        """

        val = self.__fields['url'].get_text().strip()
        if val != self.get_url():
            self.set_url(val)
            self.__config.set('bookdb.url', val)
        val = self.__fields['username'].get_text().strip()
        if val != self.__get_username():
            self.set_username(val)
            self.__config.set('bookdb.username', val)
            self.update_basic_auth()
        val = self.__fields['password'].get_text().strip()
        if val != self.__get_password():
            self.set_password(val)
            self.__config.set('bookdb.password', val)
            self.update_basic_auth()

    def __button_clicked(self, button):
        """
        Handle buttons clicked in bookDB
        """

        btn = button.get_name()
        if btn == 'Save':
            self.__button_update()
            self.__gramplet.on_save()
        elif btn == 'Test':
            self.__button_update()
            status = ""
            if not self.query_test():
                status = self.__values['status']
            else:
                if 'status' in self.answer:
                    status = self.answer['status']
            self.__fields['message'].set_text(status)
        elif btn == 'Visible':
            self.__fields['password'].set_visibility(button.get_active())
            self.set_nothidden(button.get_active())

    def __print(self, str):
        """
        print debug info
        """
        if self.__debug:
            print(str)
