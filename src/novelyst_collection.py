"""A project collection manager plugin for novelyst.

Compatibility: novelyst v2.0 API 
Requires Python 3.6+
Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
from pathlib import Path
from nvcollectionlib.collection import Collection
from nvcollectionlib.collection_manager import CollectionManager

APPLICATION = 'Collection'
DEFAULT_FILE = 'collection.pwc'


class Plugin:
    """novelyst collection manager plugin class.
    
    Public methods:
        disable_menu() -- disable menu entries when no project is open.
        enable_menu() -- enable menu entries when a project is open.    
    """
    VERSION = '2.0.0'
    NOVELYST_API = '2.0'
    DESCRIPTION = 'A book/series collection manager'
    URL = 'https://peter88213.github.io/novelyst_collection'

    def install(self, ui):
        """Add a submenu to the 'File' menu.
        
        Positional arguments:
            ui -- reference to the NovelystTk instance of the application.
        """
        self._ui = ui
        self._collectionManager = None

        try:
            homeDir = str(Path.home()).replace('\\', '/')
            installDir = f'{homeDir}/.pywriter/collection'
        except:
            installDir = '.'
        os.makedirs(installDir, exist_ok=True)
        filePath = f'{installDir}/{DEFAULT_FILE}'
        self.collection = Collection(filePath)
        if os.path.isfile(filePath):
            self.collection.read()

        # Create a submenu
        self._ui.fileMenu.add_command(label=APPLICATION, command=self._start_manager)
        self._ui.fileMenu.entryconfig(APPLICATION, state='normal')

    def _start_manager(self):
        __, x, y = self._ui.root.geometry().split('+')
        offset = 300
        windowGeometry = f'+{int(x)+offset}+{int(y)+offset}'
        if self._collectionManager:
            if self._collectionManager.isOpen:
                self._collectionManager.lift()
                self._collectionManager.focus()
                return

        self._collectionManager = CollectionManager(self._ui, windowGeometry, self.collection)
