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
Behaviour module
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

class BehaviourPage():
    """
    Class for deciding behaviour of the gramplet
    """

    __config = None
    __debug = False
    __fields = {'repo_i8n': Gtk.Switch(),
                'sour_i8n': Gtk.Switch(), 'sour_country': Gtk.Switch()}
    __gramplet = None
    __values = {'repo_i8n': False,
                'sour_avoid_signum': False, 'sour_i8n': False, 'sour_country': False}

    def __init__(self, gramplet, config):
        """
        Fix callback to gramplet
        """
        self.__print('Behaviour::__init__')

        self.__gramplet = gramplet
        self.__config = config

    def __print(self, str):
        """
        print debug info
        """
        if self.__debug:
            print(str)

    def get(self, field):
        """
        Get value
        """
        self.__print('Behaviour::get')

        return self.__values[field]

    def set_repo_i8n(self, value):
        """
        Set international state on repositories
        """
        self.__print('Behaviour::set_repo_i8n')

        self.__values['repo_i8n'] = value

    def set_sour_avoid_signum(self, value):
        """
        Set state deciding if signum should be shown
        """
        self.__print('Behaviour::set_sour_aviod_signum')

        self.__values['sour_avoid_signum'] = value

    def set_sour_country(self, value):
        """
        Set state deciding if country should be shown
        """
        self.__print('Behaviour::set_sour_country')

        self.__values['sour_country'] = value

    def set_sour_i8n(self, value):
        """
        Set international state on sources
        """
        self.__print('Behaviour::set_sour_i8n')

        self.__values['sour_i8n'] = value

    def __update_switches(self):
        """
        Update status of switches
        """
        state = self.__fields['sour_country'].get_active()
        self.__fields['sour_i8n'].set_sensitive(state)
#        print(dir(self.__fields['sour_country']))

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
        Add the Setting notebook page
        """
        self.__print("Behaviour::build_page")

        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,
                       spacing=6, border_width=10, name='Settings')

        label1 = Gtk.Label()
        label1.set_markup('<b>%s</b>' % _('Settings'))
        page.add(label1)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)

        label1 = self.__create_label(_('Repositories'), 0.0)
        grid.add(label1)

        label2 = self.__create_label(_('Swedish area- and postal-code'), 0.0)
        grid.attach_next_to(label2, label1, Gtk.PositionType.BOTTOM, 1, 2)

        self.__fields['repo_i8n'].set_name('behavior.repo_i8n')
        self.__fields['repo_i8n'].set_active(self.__values['repo_i8n'])
        self.__fields['repo_i8n'].connect("notify::active", self.behave_change_switch)
        grid.attach_next_to(self.__fields['repo_i8n'], label2, Gtk.PositionType.RIGHT, 2, 1)

        label1 = self.__create_label(_('Sources'), 0.0)
        grid.attach_next_to(label1, label2, Gtk.PositionType.BOTTOM, 1, 2)

        label2 = self.__create_label(_('Include country'), 0.0)
        grid.attach_next_to(label2, label1, Gtk.PositionType.BOTTOM, 1, 2)

        self.__fields['sour_country'].set_name('behavior.sour_country')
        self.__fields['sour_country'].set_active(self.__values['sour_country'])
        self.__fields['sour_country'].connect("notify::active", self.behave_change_switch)
        grid.attach_next_to(self.__fields['sour_country'], label2, Gtk.PositionType.RIGHT, 2, 1)

        grid.set_row_spacing(2)

        label1 = self.__create_label(_('Country in swedish'), 0.3)
        grid.attach_next_to(label1, label2, Gtk.PositionType.BOTTOM, 1, 2)

        self.__fields['sour_i8n'].set_name('behavior.sour_i8n')
        self.__fields['sour_i8n'].set_active(self.__values['sour_i8n'])
        self.__fields['sour_i8n'].connect("notify::active", self.behave_change_switch)
        grid.attach_next_to(self.__fields['sour_i8n'], label1, Gtk.PositionType.RIGHT, 2, 1)

        self.__update_switches()

        page.add(grid)

        return page

    def behave_change_switch(self, switch, gparam):
        """ behave_change_switch """
        self.__config.set(switch.get_name(), switch.get_active())
        self.__print(gparam)
        self.__update_switches()
