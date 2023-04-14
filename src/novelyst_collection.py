"""A project collection manager plugin for novelyst.

Requires Python 3.6+
Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""
import os
from pathlib import Path
import webbrowser
from nvcollectionlib.nvcollection_globals import *
from nvcollectionlib.collection_manager import CollectionManager

DEFAULT_FILE = 'collection.pwc'


class Plugin:
    """novelyst collection manager plugin class.
    
    Public methods:
        disable_menu() -- disable menu entries when no project is open.
        enable_menu() -- enable menu entries when a project is open.    
    """
    VERSION = '@release'
    NOVELYST_API = '4.19'
    DESCRIPTION = 'A book/series collection manager'
    URL = 'https://peter88213.github.io/novelyst_collection'
    _HELP_URL = 'https://peter88213.github.io/novelyst_collection/usage'

    def install(self, ui):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            ui -- reference to the NovelystTk instance of the application.
        """
        self._ui = ui
        self._collectionManager = None

        # Create a submenu.
        self._ui.fileMenu.insert_command(0, label=APPLICATION, command=self._start_manager)
        self._ui.fileMenu.insert_separator(1)
        self._ui.fileMenu.entryconfig(APPLICATION, state='normal')

        # Add an entry to the Help menu.
        self._ui.helpMenu.add_command(label=_('Collection plugin Online help'), command=lambda: webbrowser.open(self._HELP_URL))

    def _start_manager(self):
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.lift()
                self._collectionManager.focus()
                return

        __, x, y = self._ui.root.geometry().split('+')
        offset = 300
        windowGeometry = f'+{int(x)+offset}+{int(y)+offset}'
        try:
            homeDir = str(Path.home()).replace('\\', '/')
            configDir = f'{homeDir}/.pywriter/novelyst/config'
        except:
            configDir = '.'
        self._collectionManager = CollectionManager(self._ui, windowGeometry, configDir)

    def on_quit(self):
        """Write back the configuration file."""
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.on_quit()
