"""A project collection manager plugin for novelyst.

Requires Python 3.6+
Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from pathlib import Path
from nvcollectionlib.configuration import Configuration
from nvcollectionlib.nvcollection_globals import *
from nvcollectionlib.collection_manager import CollectionManager

APPLICATION = _('Collection')
DEFAULT_FILE = 'collection.pwc'
SETTINGS = dict(
    last_open='',
)
OPTIONS = {}


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
            installDir = f'{homeDir}/.pywriter/collection'
        except:
            installDir = '.'
        os.makedirs(installDir, exist_ok=True)

        #--- Load configuration.
        self.iniFile = f'{installDir}/{APPLICATION}.ini'
        self.configuration = Configuration(SETTINGS, OPTIONS)
        self.configuration.read(self.iniFile)
        kwargs = {}
        kwargs.update(self.configuration.settings)
        # Read the file path from the configuration file.

        self._collectionManager = CollectionManager(APPLICATION, self._ui, windowGeometry, **kwargs)

    def on_quit(self):
        """Write back the configuration file."""
        #--- Save project specific configuration
        for keyword in self._collectionManager.kwargs:
            if keyword in self.configuration.options:
                self.configuration.options[keyword] = self._collectionManager.kwargs[keyword]
            elif keyword in self.configuration.settings:
                self.configuration.settings[keyword] = self._collectionManager.kwargs[keyword]
        self.configuration.write(self.iniFile)
