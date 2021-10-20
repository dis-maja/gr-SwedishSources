#
# Gramps - a GTK+/GNOME based genealogy program
#
# Copyright (C) 2018      Mats O Jansson
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
#
register(GRAMPLET,
         id="SwedishSources",
         name=_("Swedish Sources"),
         description = _("Gramplet for fetching Swedish Sources"),
         status = STABLE,
         version = '0.4.0',
         fname="SwedishSources.py",
         authors=['Mats O Jansson'],
         authors_email=["maja@dis-maja.se"],
         height=400,
         gramplet = "SwedishSources",
         gramps_target_version = "5.1",
         gramplet_title=_("Swedish Sources"),
         help_url = "SwedishSources",
         )

