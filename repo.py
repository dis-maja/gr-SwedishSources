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
Repository Page module
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
from gramps.gen.db import DbTxn
from gramps.gen.lib import Address
from gramps.gen.lib import Repository, RepositoryType
from gramps.gen.lib import Url, UrlType
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

class RepoPage():
    """
    Class for deciding behaviour of the gramplet
    """

    __config = None
    __debug = False
    __fields = {'repo': None,
                'add_btn': None, 'add_label': None}
    __gramplet = None
    __values = {'repo': 0, 'repo_name': None, 'repo_sel': [],
                'page': None}
    trans = None

    def __init__(self, gramplet, config):
        """
        Fix callback to gramplet
        """
        self.__print('RepoPage::__init__')

        self.__gramplet = gramplet
        self.__config = config

    def __add_repo_rin(self):
        """
        Create a RIN record to be added to the url list
        """
        self.__print("RepoPage::__add_repo_rin")

        rin = Url()
        rin.set_path(self.__gramplet.pages['bookdb'].get_url())
        rin.set_description('RIN ' + self.__values['repo_sel'][0])
        rin.set_type(UrlType.UNKNOWN)

        return rin

    def __add_repo_url(self, info, urltype):
        """
        Create an url record for the url list
        """
        self.__print("RepoPage::__add_repo_rin")

        url = Url()
        url.set_path(info)
        url.set_description('')
        url.set_type(urltype)

        return url

    def __add_repo(self):
        """
        Save current configuration
        """
        self.__print("RepoPage::__add_repo")

        bdb_info = self.__gramplet.pages['bookdb'].query_repository(self.__values['repo_sel'][0])

        repo = Repository()
        repo.set_type(self.get_type(self.__values['repo_sel'][0]))

        repo.add_url(self.__add_repo_rin())

        inter = self.__config.get('behavior.repo_i8n')

        adr = Address()
        if inter:
            adr.set_country('Sweden')
        else:
            adr.set_country("Sverige")

        addr = {}

        for row in bdb_info:
            if row['bdbRItype'] == 'NAME':
                repo.set_name(row['bdbRIinfo'])
            elif row['bdbRItype'] == 'EMAIL':
                repo.add_url(self.__add_repo_url(row['bdbRIinfo'], UrlType.EMAIL))
            elif row['bdbRItype'] == 'WWW':
                repo.add_url(self.__add_repo_url(row['bdbRIinfo'], UrlType.WEB_HOME))
            elif row['bdbRItype'] == "PHON":
                if inter:
                    adr.set_phone(row['bdbRIinfo'])
                else:
                    adr.set_phone(self.__fix_phone(row['bdbRIinfo']))
            elif row['bdbRItype'] == "ADDR":
                addr.update({row['bdbRIrow']: row['bdbRIinfo']})
#            else:
#                print(row['bdbRItype'])

        last = ''
        pcode = ''
        if '1' in addr:
            del addr['1']
        for key, val in addr.items():
            last = key
        if last != '':
            pcode = addr[last]
            del addr[last]

        i = 0
        for key, val in addr.items():
            if i == 0:
                adr.set_street(val)
            elif i == 1:
                adr.set_locality(val)

        pos = pcode.find(' ', pcode.find(' ')+1)
        adr.set_city(pcode[pos+1:])

        if inter:
            adr.set_postal_code(pcode[:pos])
        else:
            adr.set_postal_code(self.__fix_postal(pcode[:pos]))

        repo.add_address(adr)

        # begin transaction
        with DbTxn("SwedishSources", self.__gramplet.dbstate.db, batch=False) as self.trans:
            self.__gramplet.dbstate.db.add_repository(repo, self.trans)
            self.__gramplet.dbstate.db.commit_repository(repo, self.trans)

    def __btn_clicked(self, button):
        """
        handle button clicked
        """
        self.__print('RepoPage::__btn_clicked')
        btn = button.get_name()
        if btn == 'Add':
            self.__add_repo()

    def __changed_repo(self, selection):
        """
        Action when a row in repo_name view is clicked
        """
        self.__print('RepoPage::__changed_repo')

        (model, row) = selection.get_selected()
        if row is not None:
            self.__values['repo_sel'] = model[row][:]
        else:
            self.__values['repo_sel'] = []
        if len(self.__values['repo_sel']) == 0:
            self.__fields['add_btn'].set_sensitive(False)
            self.__fields['add_label'].set_text("")
        elif self.__values['repo_sel'][2] != "" or self.__values['repo_sel'][3] == 1:
            self.__fields['add_btn'].set_sensitive(False)
            self.__fields['add_label'].set_text("")
        else:
#            print(self.__values['repo_sel'][:])
            self.__fields['add_btn'].set_sensitive(True)
            self.__fields['add_label'].set_text(self.__values['repo_sel'][1])
        self.update_store()

    @staticmethod
    def __fix_phone(phone):
        """
        Remove Country code
        """
        pos = phone.find('(')
        if pos < 0:
            return phone
        tmp = phone[pos+1:]
        pos = tmp.find(')')
        ret = tmp[:pos] + tmp[pos+1:]
        return ret

    @staticmethod
    def __fix_postal(postal):
        """
        Remove Country prefix on postcode
        """
        pos = postal.find('-')
        if pos < 0:
            return postal
        return postal[pos+1:]

    def __print(self, str):
        """
        print debug information
        """
        if self.__debug:
            print(str)

    def build_page(self):
        """
        Build the source page
        """
        self.__print('RepoPage::build_page')

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, name='Repositories')

        if self.__values['repo_name'] is None:
            self.__values['repo_name'] = Gtk.ListStore(int, str, str, int, str)

        if self.__fields['repo'] is None:

            repo_box = Gtk.Box(spacing=6)

            add_btn = Gtk.Button.new_with_label(_('Add'))
            add_btn.set_name('Add')
            add_btn.connect('clicked', self.__btn_clicked)
            self.__fields['add_btn'] = add_btn
            self.__fields['add_btn'].set_visible(False)
            repo_box.pack_start(add_btn, True, True, 0)
            if len(self.__values['repo_sel']) == 0:
                self.__fields['add_btn'].set_sensitive(False)
            else:
                self.__fields['add_btn'].set_sensitive(True)

            add_label = Gtk.Label()
            add_label.set_property('width-request', 200)
            add_label.set_xalign(0.0)
            self.__fields['add_label'] = add_label
            self.__fields['add_label'].set_visible(False)
            repo_box.pack_start(add_label, True, True, 0)
            if len(self.__values['repo_sel']) == 0:
                self.__fields['add_label'].set_text("")
            else:
                self.__fields['add_label'].set_text(self.__values['book_sel'][1])
            self.__fields['repo'] = repo_box

            page.add(repo_box)

            repos = self.__gramplet.pages['bookdb'].query_repositories()
            self.__values['repo_name'] = Gtk.ListStore(str, str, str, str, str)
            for entry in repos:
                self.__values['repo_name'].append([entry['rin'], entry['name'],
                                                   entry['gramps_id'], entry['type'],
                                                   entry['ref']])
            self.update_store()

            tree = Gtk.TreeView(self.__values['repo_name'])
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(_('Name'), renderer, markup=1)
            tree.append_column(column)
            column = Gtk.TreeViewColumn(_('ID'), renderer, text=2)
            tree.append_column(column)

            select = tree.get_selection()
            select.connect("changed", self.__changed_repo)

            scr = Gtk.ScrolledWindow()
            scr.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scr.add(tree)
            scr.set_min_content_height(330)

            self.__fields['book'] = scr
            page.add(scr)

            self.__fields['book'].set_visible(True)

        return page

    def get_gramps_id(self, rin):
        """
        Return gramps_id for Repository
        """
        for entry in list(self.__values['repo_name']):
            if entry[0] == rin:
                return entry[2]
        return ''

    def get_gramps_id_by_ref(self, ref):
        """
        Return gramps_id for Repository by ref
        """
        for entry in list(self.__values['repo_name']):
            if entry[4] == ref:
                return entry[2]
        return ''

    def get_rin_by_ref(self, ref):
        """
        Return rin for Repository by ref
        """
        for entry in list(self.__values['repo_name']):
            if entry[4] == ref:
                return entry[0]
        return 0

    def get_type(self, rin):
        """
        Return gramps RepoType for Repository
        """
        for entry in list(self.__values['repo_name']):
            if entry[0] == rin:
                return int(entry[3])
        return 4

    def get_name(self, rin):
        """
        Return gramps RepoType for Repository
        """
        for entry in list(self.__values['repo_name']):
            if entry[0] == rin:
                return entry[1]
        return ''

    def update(self, obj):
        """
        called from Swedish Sources on db changes
        """
#        print(obj)
        self.update_store()

    def update_store(self):
        """
        Update gramps_id and type in repo_name

        The connection between a repository in the gramps database and
        the corresponding in bookDB is stored in an url of type UNKNOWN.

        The path of the url should be the one bookDB points out.

        In the description of the url the text constant "RIN "
        is followed by the internal id for the repository in bookDB.
        """
        self.__print("RepoPage::update_store")

        found = []
        url = self.__gramplet.pages['bookdb'].get_url()

        # check all repositories for RIN information
        for handle in self.__gramplet.dbstate.db.get_repository_handles():

            # fetch a repository
            repo = self.__gramplet.dbstate.db.get_repository_from_handle(handle)

            # if no urls, skip this repositoy
            if len(repo.urls) == 0:
                continue

            # For each url, check if it contains RIN information
            for post in repo.urls:
                if post.type != UrlType.UNKNOWN:
                    continue
                if post.path != url:
                    continue
                if post.get_description()[:4] != "RIN ":
                    continue

                # Yes, extract bookDB RIN
                rin = post.get_description()[4:].strip()

                # Check if it is in repo_name
                for row in list(self.__values['repo_name']):
                    if row[0] == rin:
                        row[2] = repo.get_gramps_id()
                        row[3] = str(repo.get_type())
                        found.append(rin)

        # clear the gramps id and type for every repository not found
        if not self.__values['repo_name'] is None:
            for row in list(self.__values['repo_name']):
                if row[0] in found:
                    continue
                row[2] = ""
