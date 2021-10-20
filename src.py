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
#
# $Id$
"""
Source Page module
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
from gramps.gen.lib import RepoRef
from gramps.gen.lib import Source
from gramps.gen.lib import SourceMediaType
from gramps.gen.lib import SrcAttribute
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

PAGE_UNKNOWN = 0
PAGE_CHURCH = 1
PAGE_SCB = 2
PAGE_DB = 3
PAGE_DEFAULT = PAGE_UNKNOWN

class SourcePage():
    """
    Class for deciding behaviour of the gramplet
    """

    __config = None
    __debug = True
    __fields = {'arch': None, 'book': None,
                'cnty': None, 'type': None,
                'add_btn': None, 'add_label': None}
    __gramplet = None
    __values = {'arch': 0, 'arch_name': None,
                'book': 0,
                'book_list': [[PAGE_UNKNOWN, _('Choose Book Type')],
                              [PAGE_CHURCH, _('Church Books')],
                              [PAGE_SCB, _('SCB Extracts from Church Books 1860-1949')]],
#                              [PAGE_DB, _('Databases, local or online')]],
                'book_name': None,
                'book_sel': [],
                'cnty': 0,
                'cnty_list': [[0, _('Choose County')]],
                'cnty_name': None,
                'cnty_page': {PAGE_CHURCH: 0, PAGE_SCB: 0},
                'page': None,
                'rin': {},
                'type': PAGE_DEFAULT, 'type_name': None}
    trans = None

    def __init__(self, gramplet, config):
        """
        Fix callback to gramplet
        """
        self.__print('SourcePage::__init__')

        self.__gramplet = gramplet
        self.__config = config

    def __add_book(self):
        """
        Add a book
        """
        self.__print('SourcePage::__add_book')

        if self.__values['type'] == PAGE_CHURCH:
            self.__add_chur_book()
        if self.__values['type'] == PAGE_SCB:
            self.__add_scb_book()

    def __add_book__create_ad_repo_ref(self, bk_info):
        """
        Add a AD repo ref
        """
        self.__print('SourcePage::__add_book__create_ad_repo_ref')
        from gramps.gui.dialog import ErrorDialog

        rref = RepoRef()

        rin = self.__gramplet.pages['repo'].get_rin_by_ref('AD')
        gramps_id = self.__gramplet.pages['repo'].get_gramps_id_by_ref('AD')
        if gramps_id == "":
            ErrorDialog(_("bookDB repository missing"), 
                        self.__gramplet.pages['repo'].get_name(rin))
            return None

        repo = self.__gramplet.dbstate.db.get_repository_from_gramps_id(gramps_id)
        rref.set_reference_handle(repo.get_handle())
        callno = 'AID %s, https://www.arkivdigital.se/aid/info/%s (%s)' % \
                 (bk_info['adBKvol'], bk_info['adBKvol'], bk_info['adACchkBK'])
        rref.set_call_number(callno)
        rref.set_media_type(SourceMediaType.ELECTRONIC)

        return rref

    def __add_book__create_nad_repo_ref(self, bk_info):
        """
        Add a NAD repo ref
        """
        self.__print('SourcePage::__add_book__create_nad_repo_ref')
        from gramps.gui.dialog import ErrorDialog

        rrefs = []

        rin = self.__gramplet.pages['repo'].get_rin_by_ref('SVAR')
        gramps_id = self.__gramplet.pages['repo'].get_gramps_id_by_ref('SVAR')
        if gramps_id == "":
            ErrorDialog(_("bookDB repository missing"), 
                        self.__gramplet.pages['repo'].get_name(rin))
            return None

        br_info = self.__gramplet.pages['bookdb'].query_bookrefs(bk_info['nadBKid'])
        print(br_info)
        for entry in br_info:
            rref = RepoRef()
            repo = self.__gramplet.dbstate.db.get_repository_from_gramps_id(gramps_id)
            rref.set_reference_handle(repo.get_handle())

            if entry['nadBRtype'] == 'bildfil':
                pos = entry['nadBRref'].find(' ')
                if pos != -1:
                    callno = 'Bildid %s, https://sok.riksarkivet.se/bildid?Bildid=%s (%s)' % \
                             (entry['nadBRref'][pos+1:].strip(), entry['nadBRref'][pos+1:].strip(),
                              bk_info['nadBKchkBr'])
                    rref.set_call_number(callno)
                    rref.set_media_type(SourceMediaType.ELECTRONIC)
                    rrefs.append(rref)

            if entry['nadBRtype'] == 'microfilm':
                callno = 'Microfilm %s' % entry['nadBRref'].strip();
                rref.set_call_number(callno);
                rref.set_media_type(SourceMediaType.FICHE)
                rrefs.append(rref)

        return rrefs

    def __add_book__create_repo_ref(self, ac_info, bk_info):
        """
        Add a repo ref
        """
        self.__print('SourcePage::__add_book__create_repo_ref')
        from gramps.gui.dialog import ErrorDialog

        rref = RepoRef()

        gramps_id = self.__gramplet.pages['repo'].get_gramps_id(ac_info['bdbREid'])
        if gramps_id == "":
            ErrorDialog(_("bookDB repository missing"), 
                        self.__gramplet.pages['repo'].get_name(ac_info['bdbREid']))
            return None

        repo = self.__gramplet.dbstate.db.get_repository_from_gramps_id(gramps_id)
        rref.set_reference_handle(repo.get_handle())

        callno = '%s/%s/%s (%s)' % (ac_info['bdbACref'], bk_info['nadSTsignum'],
                                    bk_info['nadBKvol'], ac_info['bdbBKchk'])
        rref.set_call_number(callno)
        rref.set_media_type(SourceMediaType.BOOK)

        return rref

    def __add_book__title_prefix(self):
        """
        Add title prefix
        """

        prefix = ""

        #
        # TO DO: control for caseing
        #
#        if self.__config.get('behavior.sour_country'):
#            if self.__config.get('behaviour.sour_i8n'):
        if self.__gramplet.pages['behave'].get('sour_country'):
            if self.__gramplet.pages['behave'].get('sour_i8n'):
                prefix += "Sverige, "
            else:
                prefix += "SWEDEN, "

        prefix += "%s, " % self.__cnty_name(self.__values['cnty'])

        return prefix

    def __add_chur_book(self):
        """
        Add a church book
        """
        self.__print("SourcePage::__add_chur_book")

        ac_info = self.__gramplet.pages['bookdb'].query_archive(self.__values['arch'])

        bk_info = self.__gramplet.pages['bookdb'].query_book(self.__values['book_sel'][0])

        sour = Source()

        prefix = self.__add_book__title_prefix()

#        if self.__config.get('behaviour.sour_avoid_signum'):

        title = prefix + ac_info['bdbACname'] + ', ' + self.__values['book_sel'][1].strip()
        sour.set_title(title)
        sour.set_abbreviation(title)

        author = prefix + ac_info['bdbACauthor']
        sour.set_author(author)

        attr = SrcAttribute()
        attr.set_type('BDBRIN')
        attr.set_value(str(self.__values['book_sel'][0]))
        sour.add_attribute(attr)

        rref = self.__add_book__create_repo_ref(ac_info, bk_info)
        if rref is None:
            return
        sour.add_repo_reference(rref)

        if bk_info['nadBKid'] != '0':
            rrefs = self.__add_book__create_nad_repo_ref(bk_info)
            if rrefs is None:
                return
            for rref in rrefs:
                sour.add_repo_reference(rref)

        if bk_info['adBKid'] != '0':
            rref = self.__add_book__create_ad_repo_ref(bk_info)
            if rref is None:
                return
            sour.add_repo_reference(rref)

        # begin transaction
        with DbTxn("SwedishSources", self.__gramplet.dbstate.db, batch=False) as self.trans:
            self.__gramplet.dbstate.db.add_source(sour, self.trans)
            self.__gramplet.dbstate.db.commit_source(sour, self.trans)

        self.sour_update_index()
        self.update_book_store()

    def __add_scb_book(self):
        """
        Add a SCB book
        """
        self.__print("SourcePage::__add_scb_book")

        ac_info = self.__gramplet.pages['bookdb'].query_scb_archive()

        bk_info = self.__gramplet.pages['bookdb'].query_book(self.__values['book_sel'][0])

        bt_info = self.__gramplet.pages['bookdb'].query_scb_booktypes()

        sour = Source()

        prefix = self.__add_book__title_prefix()

#        if self.__config.get('behaviour.sour_avoid_signum'):

        title = '%s%s, %s' % (prefix, bt_info[bk_info['nadBTidReal']], bk_info['nadBKperiod'])
        title = '%s (%s)' % (title, bk_info['bdbBKsignum'])

        sour.set_title(title)
        sour.set_abbreviation(title)

        author = ac_info['bdbACauthor']
        sour.set_author(author)

        attr = SrcAttribute()
        attr.set_type('BDBRIN')
        attr.set_value(str(self.__values['book_sel'][0]))
        sour.add_attribute(attr)

        rref = self.__add_book__create_repo_ref(ac_info, bk_info)
        if rref is None:
            return
        sour.add_repo_reference(rref)

        if bk_info['nadBKid'] != '0':
            rrefs = self.__add_book__create_nad_repo_ref(bk_info)
            if rrefs is None:
                return
            for rref in rrefs:
                sour.add_repo_reference(rref)

        if bk_info['adBKid'] != '0':
            rref = self.__add_book__create_ad_repo_ref(bk_info)
            if rref is None:
                return
            sour.add_repo_reference(rref)

        # begin transaction
        with DbTxn("SwedishSources", self.__gramplet.dbstate.db, batch=False) as self.trans:
            self.__gramplet.dbstate.db.add_source(sour, self.trans)
            self.__gramplet.dbstate.db.commit_source(sour, self.trans)

        self.sour_update_index()
        self.update_book_store()

    def __btn_clicked(self, button):
        """
        handle button clicked
        """
        self.__print('SourcePage::__btn_clicked')

        btn = button.get_name()
        if btn == 'Add':
            self.__add_book()

    def __changed_book(self, selection):
        """
        Action when a row in chur_book view is clicked
        """
        self.__print('SourcePage::__changed_book')

        (model, row) = selection.get_selected()
        if row is not None:
            self.__values['book_sel'] = model[row][:]
        else:
            self.__values['book_sel'] = []
        if len(self.__values['book_sel']) == 0:
            self.__fields['add_btn'].set_sensitive(False)
            self.__fields['add_label'].set_text("")
        elif self.__values['book_sel'][2] != "" or self.__values['book_sel'][3] == 1:
            self.__fields['add_btn'].set_sensitive(False)
            self.__fields['add_label'].set_text("")
        else:
            self.__fields['add_btn'].set_sensitive(True)
            self.__fields['add_label'].set_text(self.__values['book_sel'][1])
        self.update_book_store()

    def __changed_combo(self, combo):
        """
        Handle change of combo
        """
        tree_iter = combo.get_active_iter()
        if tree_iter is None:
            return

        self.__print('SourcePage::__changed_combo')
        model = combo.get_model()
        cname = combo.get_name()
        row_id, name = model[tree_iter][:2]

        if cname == 'type':
            if row_id != self.__values[cname]:
                if row_id in self.__values['cnty_page']:
                    self.__values['cnty'] = self.__values['cnty_page'][row_id]
                self.__fields['cnty'].set_active(self.__cnty_idx(self.__values['cnty']))
                self.__values['book_name'].clear()
                self.__values[cname] = row_id
                if self.__values['type'] == PAGE_DB and row_id != 0:
                    self.__update_db_book()
                self.update_visibility()
        elif cname == 'cnty':
            if row_id != self.__values[cname]:
                self.__values[cname] = row_id
                self.__values['cnty_page'][self.__values['type']] = row_id
                self.__values['book_name'].clear()
                if self.__values['type'] == PAGE_CHURCH:
                    self.__values['arch'] = 0
                    self.__update_chur_arch(row_id)
#                if self.__values['type'] == PAGE_CHURCH and row_id != 0:
#                    self.__update_chur_arch(row_id)
                if self.__values['type'] == PAGE_SCB and row_id != 0:
                    self.__update_scb_book(row_id)
                self.update_visibility()
        elif cname == 'arch':
            if row_id != self.__values[cname]:
                self.__values[cname] = row_id
                if self.__values['type'] == PAGE_CHURCH and row_id != 0:
                    self.chur_book_update(row_id)
                    self.update_book_store()

    def __cnty_idx(self, value):
        """
        Convert county number to index into cnty_name
        """

        i = 0
        for entry in list(self.__values['cnty_name']):
            if entry[0] == value:
                return i
            i += 1
        return 0

    def __cnty_name(self, value):
        """
        Convert county number to a name
        """
        name = ""
        for entry in list(self.__values['cnty_name']):
            if entry[0] == value:
                name = entry[1]
        return name

    def __create_combobox(self, name, value):
        """
        Create a combobox for the SourcePage
        """
        self.__print('SourcePage::__create_combobox')

        box = Gtk.ComboBox.new_with_model(self.__values[name])
        box.set_name(value)
        box.connect("changed", self.__changed_combo)
        box_text = Gtk.CellRendererText()
        box.pack_start(box_text, True)
        box.add_attribute(box_text, "markup", 1)
        box.set_active(self.__values[value])
        if len(self.__values[name]) <= 2 and self.__values[value] != 0:
            box.set_button_sensitivity(Gtk.SensitivityType.OFF)
        return box

    def __create_liststore(self, default):
        """
        Create a liststore fro the SourcePage
        """
        self.__print('SourcePage::__create_liststore')

        store = Gtk.ListStore(int, str)
        for item in default:
            store.append(list(item))

        return store

    def __print(self, str):
        """
        print debug info
        """
        if self.__debug:
            print(str)

    def __update_chur_arch(self, cid):
        """
        Update arch_name
        """
        self.__print('SourcePage::__update_chur_arch')

        #
        # Remove all but the first entry (Choose archive)
        #
        self.__values['arch_name'].clear()
        self.__values['arch_name'].append([0, _('Choose Archive')])

        #
        # If county is given, query for all archives
        #
        if cid != 0:

            #
            # Refill arch_name with information again
            #
            archives = self.__gramplet.pages['bookdb'].query_archives(cid)
            for entry in archives:
                name = entry['bdbACname']
                if entry['bdbCTid'] != str(cid):
                    name = '%s <i>(%s)</i>' % (name, self.__cnty_name(int(entry['bdbCTid'])))
                self.__values['arch_name'].append([int(entry['bdbACid']), name])

            #
            # Select witch entry to make active
            #
            if len(self.__values['arch_name']) == 2:
                self.__values['arch'] = 1
            else:
                self.__values['arch'] = 0
            self.__fields['arch'].set_active(self.__values['arch'])

        #
        # If only one chooise, disable the button
        #
        if len(self.__values['arch_name']) < 2:
            self.__fields['arch'].set_button_sensitivity(Gtk.SensitivityType.OFF)
        else:
            self.__fields['arch'].set_button_sensitivity(Gtk.SensitivityType.ON)

    def __update_db_book(self):
        """
        Update book_name
        """
        self.__print('SourcePage::__update_db_book')

        #
        # Remove all books
        #
        self.__values['book_name'].clear()

#        btypes = self.__gramplet.pages['bookdb'].query_scb_booktypes()
#
#        books = self.__gramplet.pages['bookdb'].query_scb_books(cid)
#
#        self.__values['book_name'].append([0, '<b>%s</b>' % btypes[list(btypes.keys())[0]],
#                                           '', 1, ''])
#
#        for entry in books:
#            btype = entry['nadBTid']
#            boki = int(entry['bdbBKid'])
#            bokn = '  %s %s (%s)' % (btypes[btype], entry['nadBKperiod'], entry['bdbBKsignum'])
#            self.__values['book_name'].append([boki, bokn, '', 0, entry['nadBKextra']])

    def __update_scb_book(self, cid):
        """
        Update book_name
        """
        self.__print('SourcePage::__update_scb_book')

        #
        # Remove all books
        #
        self.__values['book_name'].clear()

        btypes = self.__gramplet.pages['bookdb'].query_scb_booktypes()

        books = self.__gramplet.pages['bookdb'].query_scb_books(cid)

        self.__values['book_name'].append([0, '<b>%s</b>' % btypes[list(btypes.keys())[0]],
                                           '', 1, ''])

        for entry in books:
            btype = entry['nadBTid']
            boki = int(entry['bdbBKid'])
            bokn = '  %s %s (%s)' % (btypes[btype], entry['nadBKperiod'], entry['bdbBKsignum'])
            self.__values['book_name'].append([boki, bokn, '', 0, entry['nadBKextra']])

    def build_page(self):
        """
        Build the source page
        """
        self.__print('SourcePage::build_page')

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2, name='Sources')

        if self.__values['type_name'] is None:
            self.__values['type_name'] = self.__create_liststore(self.__values['book_list'])

        if self.__fields['type'] is None:
            self.__fields['type'] = self.__create_combobox('type_name', 'type')
        page.add(self.__fields['type'])

        if self.__values['cnty_name'] is None:
            self.__values['cnty_name'] = self.__create_liststore(self.__values['cnty_list'])
            counties = self.__gramplet.pages['bookdb'].query_counties()
            for entry in counties:
                self.__values['cnty_name'].append([int(entry['bdbCTid']), entry['bdbCTname']])

        if self.__fields['cnty'] is None:
            self.__fields['cnty'] = self.__create_combobox('cnty_name', 'cnty')
        self.__fields['cnty'].set_visible(False)
        self.__fields['cnty'].set_button_sensitivity(Gtk.SensitivityType.OFF)

        page.add(self.__fields['cnty'])

        if self.__values['arch_name'] is None:
            self.__values['arch_name'] = Gtk.ListStore(int, str)
            self.__values['arch_name'].append([0, _('Choose Archive')])

        if self.__fields['arch'] is None:
            self.__fields['arch'] = self.__create_combobox('arch_name', 'arch')
        self.__fields['arch'].set_visible(False)
        self.__fields['arch'].set_button_sensitivity(Gtk.SensitivityType.OFF)

        page.add(self.__fields['arch'])

        if self.__values['book_name'] is None:
            self.__values['book_name'] = Gtk.ListStore(int, str, str, int, str)

        if self.__fields['book'] is None:

            book_box = Gtk.Box(spacing=6)

            add_btn = Gtk.Button.new_with_label(_('Add'))
            add_btn.set_name('Add')
            add_btn.connect('clicked', self.__btn_clicked)
            self.__fields['add_btn'] = add_btn
            self.__fields['add_btn'].set_visible(False)
            self.__fields['add_btn'].set_sensitive(False)
            book_box.pack_start(add_btn, True, True, 0)
##            if len(self.__values['book_sel']) == 0:
##                self.__values['book_add'].set_sensitive(False)
##            else:
##                self.__values['book_add'].set_sensitive(True)

            add_label = Gtk.Label()
            add_label.set_property('width-request', 200)
            add_label.set_xalign(0.0)
            self.__fields['add_label'] = add_label
            self.__fields['add_label'].set_visible(False)
            book_box.pack_start(add_label, True, True, 0)
##            if len(self.__values['book_sel']) == 0:
##                self.__values['book_label'].set_text("")
##            else:
##                self.__values['book_label'].set_text(self.chur_book_sel[1])
#            self.__fields['book'] = book_box

            page.add(book_box)

            tree = Gtk.TreeView(self.__values['book_name'])
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(_('Name'), renderer, markup=1)
            tree.append_column(column)
            column = Gtk.TreeViewColumn(_('Extra'), renderer, text=4)
            tree.append_column(column)
            column = Gtk.TreeViewColumn(_('ID'), renderer, text=2)
            tree.append_column(column)

            select = tree.get_selection()
            select.connect("changed", self.__changed_book)

            scr = Gtk.ScrolledWindow()
            scr.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
            scr.add(tree)
#            scr.set_min_content_height(330)

            self.__fields['book'] = scr
            page.add(scr)

            self.__fields['book'].set_visible(False)
            self.__fields['book'].set_sensitive(False)
#
        self.update_visibility()

        return page

    def chur_book_update(self, aid):
        """
        Update book_name
        """
        self.__print('SourcePage::chur_book_update')

        #
        # Remove all books
        #
        self.__values['book_name'].clear()

        #
        # If archive is given, query for all books
        #
        if aid != 0:

            btypes = self.__gramplet.pages['bookdb'].query_booktypes_arch(aid)

            books = self.__gramplet.pages['bookdb'].query_books(aid)

            btype = '0'
            for entry in books:
                if entry['nadBTid'] != btype:
                    btype = entry['nadBTid']
                    self.__values['book_name'].append([0, '<b>%s</b>' % btypes[btype], '', 1, ''])
                bokt = btype
                if entry['nadBTidSpec'] != '0':
                    bokt = entry['nadBTidSpec']
                boki = int(entry['bdbBKid'])
                bokn = '  %s %s (%s)' % (btypes[bokt], entry['nadBKperiod'], entry['bdbBKsignum'])
                self.__values['book_name'].append([boki, bokn, '', 0, ''])

        self.update_visibility()

    def sour_update_index(self):
        """
        update index
        """

        dbstate = self.__gramplet.dbstate

        # check all sources for RIN information
        for handle in dbstate.db.get_source_handles():

            # fetch a source
            sour = dbstate.db.get_source_from_handle(handle)

            # check if source has any attributes, if not skip the rest
            attr = sour.get_attribute_list()
            if len(attr) == 0:
                continue

            # only check attributes of type BDBRIN
            for i in attr:
                if i.get_type() != 'BDBRIN':
                    continue
                # Save rin and gramps id
                self.__values['rin'][i.get_value()] = sour.get_gramps_id()

    def update(self, obj):
        """
        called from Swedish Sources on db changes
        """
        print(obj)

    def update_book_store(self):
        """
        Update gramps_id in book_store
        """
        self.__print("SourcePage::update_book_store")

        # Check if it is in repo_store
        for row in list(self.__values['book_name']):
            if str(row[0]) in self.__values['rin']:
                row[2] = self.__values['rin'][str(row[0])]
            else:
                row[2] = ''

    def update_visibility(self):
        """
        Set the visibility
        """
        self.__print('SourcePage::update_visibility')

        # Don't show anything by default
        show = False

        # Only set visibility for PAGE_CHURCH and PAGE_SCB
        if self.__values['type'] in self.__values['cnty_page']:
            show = True

        # Show County
        self.__fields['cnty'].set_visible(show)
        if show:
            self.__fields['cnty'].set_button_sensitivity(Gtk.SensitivityType.ON)

        if show:
            if self.__values['cnty_page'][self.__values['type']] == 0:
                # No county choosen, don't show any more
                show = False

        # Show Archive
        if show and self.__values['type'] == PAGE_CHURCH:
            self.__fields['arch'].set_visible(show)
            self.__fields['arch'].set_button_sensitivity(Gtk.SensitivityType.ON)

            if self.__values['arch'] == 0:
                # No archive choosen, do't show any more
                show = False
        else:
            self.__fields['arch'].set_visible(False)

        # Show Archive
        if self.__values['type'] == PAGE_DB:
            show = True

        # Show Add button, Add label and books
        self.__fields['add_btn'].set_visible(show)
        if show:
            self.__fields['add_btn'].set_sensitive(show)

        self.__fields['add_label'].set_visible(show)

        self.__fields['book'].set_visible(show)
        if show:
            self.__fields['book'].set_sensitive(show)
            if self.__values['type'] == PAGE_CHURCH:
                self.__fields['book'].set_min_content_height(210)
            if self.__values['type'] == PAGE_SCB:
                self.__fields['book'].set_min_content_height(250)

