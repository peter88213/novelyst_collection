"""Provide a tkinter widget for project collection management.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import tkinter as tk
from tkinter import ttk


class CollectionManager(tk.Toplevel):

    def __init__(self, ui, windowGeometry, collection, **kw):
        self._ui = ui
        super().__init__(**kw)
        self.geometry(windowGeometry)
        self.lift()
        self.focus()
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill=tk.BOTH)
        self.collection = collection

        #--- Listbox for book selection.
        self.listbox = tk.Listbox(self.mainWindow, selectmode=tk.SINGLE)
        self.booklist = []
        for bkId in self.collection.books:
            self.booklist.append(bkId)
            self.listbox.insert(tk.END, self.collection.books[bkId].title)
        self.listbox.pack(side=tk.LEFT, padx=10, pady=10)
        self.listbox.bind('<<ListboxSelect>>', self._show_desc)
        self.listbox.bind('<Double-1>', self._open_project)
        self.listbox.bind('<Return>', self._open_project)

        #--- Viewer window for the description.
        self.viewer = tk.Text(self.mainWindow, wrap='word')
        self.viewer.pack(padx=10, pady=10)

    def _show_desc(self, event):
        """View the selected book's description."""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.viewer.delete('1.0', tk.END)
            self.viewer.insert(tk.END, self.collection.books[self.booklist[index]].desc)

    def _open_project(self, event):
        """Make the application open the selected book's project."""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self._ui.open_project(self.collection.books[self.booklist[index]].filePath)

