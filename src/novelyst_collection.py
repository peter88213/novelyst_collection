"""A project collection manager plugin for novelyst.

Requires Python 3.6+
Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from pathlib import Path
from nvcollectionlib.nvcollection_globals import *
from nvcollectionlib.collection_manager import CollectionManager

APPLICATION = _('Collection')
DEFAULT_FILE = 'collection.pwc'


class Plugin:
    """novelyst collection manager plugin class.
    
    Public methods:
        disable_menu() -- disable menu entries when no project is open.
        enable_menu() -- enable menu entries when a project is open.    
    """
    VERSION = '@release'
    NOVELYST_API = '3.0'
    DESCRIPTION = 'A book/series collection manager'
    URL = 'https://peter88213.github.io/novelyst_collection'

    def install(self, ui):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            ui -- reference to the NovelystTk instance of the application.
        """
        self._ui = ui
        self._collectionManager = None

        # Create a submenu
        self._ui.fileMenu.insert_command(0, label=APPLICATION, command=self._start_manager)
        self._ui.fileMenu.insert_separator(1)
        self._ui.fileMenu.entryconfig(APPLICATION, state='normal')

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
        self._collectionManager = CollectionManager(APPLICATION, self._ui, windowGeometry, configDir)

    def on_quit(self):
        """Write back the configuration file."""
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.on_quit()
