"""Provide a tkinter widget for project collection management.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from nvcollectionlib.nvcollection_globals import *


class CollectionManager(tk.Toplevel):
    _KEY_QUIT_PROGRAM = ('<Control-q>', 'Ctrl-Q')
    _SERIES_PREFIX = 'sr'
    _BOOK_PREFIX = 'bk'

    def __init__(self, title, ui, size, collection, **kw):
        self._ui = ui
        super().__init__(**kw)
        self.title(title)
        self.geometry(size)
        self.lift()
        self.focus()
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.bind(self._KEY_QUIT_PROGRAM[0], self.on_quit)

        #--- Main menu.
        self.mainMenu = tk.Menu(self)
        self.config(menu=self.mainMenu)

        #--- File menu.
        self.fileMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('File'), menu=self.fileMenu)
        # self.fileMenu.add_command(label=_('Open...'), accelerator=self._KEY_OPEN_PROJECT[1], command=lambda: self.open_project(''))
        # self.fileMenu.add_command(label=_('Close'), command=self.close_project)
        # self.fileMenu.entryconfig(_('Close'), state='disabled')
        self.fileMenu.add_command(label=_('Exit'), accelerator=self._KEY_QUIT_PROGRAM[1], command=self.on_quit)

        #--- Series menu.
        self.seriesMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Series'), menu=self.seriesMenu)
        self.seriesMenu.add_command(label=_('Remove selected series from collection'), command=self._remove_series)

        #--- Book menu.
        self.bookMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Book'), menu=self.bookMenu)
        self.bookMenu.add_command(label=_('Update book data from current project'), command=self._update_book)
        self.bookMenu.add_command(label=_('Add current project to collection'), command=self._add_current_project)
        self.bookMenu.add_command(label=_('Remove selected book from collection'), command=self._remove_book)

        #--- Main window.
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill=tk.BOTH, padx=2, pady=2)
        self.collection = collection

        #--- Tree for book selection.
        columns = 'Title'
        self._tv = ttk.Treeview(self.mainWindow, columns=columns, show='headings', selectmode='browse')
        self._tv.column('Title', width=250, minwidth=120, stretch=False)
        self._tv.heading('Title', text=_('Title'), anchor='w')
        self._tv.pack(side=tk.LEFT, fill=tk.Y)
        self._tv.bind('<<TreeviewSelect>>', self._on_select_node)
        self._tv.bind('<<TreeviewSelect>>', self._on_select_node)
        self._tv.bind('<Double-1>', self._open_project)
        self._tv.bind('<Return>', self._open_project)
        self._tv.bind('<Delete>', self._remove_node)

        #--- Viewer window for the description.
        self._viewer = tk.Text(self.mainWindow, wrap='word')
        self._viewer.pack()

        self._build_tree()
        self.isOpen = True

    def _build_tree(self):
        self._reset_tree()
        for bkId in self.collection.books:
            item = f'{self._BOOK_PREFIX}{bkId}'
            columns = [self.collection.books[bkId].title]
            self._tv.insert('', tk.END, item, values=columns)

    def _reset_tree(self):
        """Clear the displayed tree."""
        for child in self._tv.get_children(''):
            self._tv.delete(child)

    def _on_select_node(self, event=None):
        """View the selected element's description."""
        self._viewer.delete('1.0', tk.END)
        try:
            nodeId = self._tv.selection()[0]
            elemId = nodeId[2:]
            if nodeId.startswith(self._BOOK_PREFIX):
                desc = self.collection.books[elemId].desc
            elif nodeId.startswith(self._SERIES_PREFIX):
                desc = self.collection.series[elemId].desc
            if desc:
                self._viewer.insert(tk.END, desc)
        except IndexError:
            pass

    def _open_project(self, event=None):
        """Make the application open the selected book's project."""
        try:
            nodeId = self._tv.selection()[0]
            if nodeId.startswith(self._BOOK_PREFIX):
                bkId = nodeId[2:]
                self._ui.open_project(self.collection.books[bkId].filePath)
        except IndexError:
            pass

    def _add_current_project(self, event=None):
        novel = self._ui.ywPrj
        if novel is not None:
            try:
                bkId = self.collection.add_book(novel)
            except Error as ex:
                self._show_info(str(ex))
            else:
                if bkId is not None:
                    item = f'{self._BOOK_PREFIX}{bkId}'
                    columns = [self.collection.books[bkId].title]
                    self._tv.insert('', tk.END, item, values=columns)
                    self._show_info(f'"{novel.title}" added to the collection.')
                else:
                    self._show_info(f'!"{novel.title}" already exists.')

    def _update_book(self, event=None):
        novel = self._ui.ywPrj
        if novel is not None:
            for bkId in self.collection.books:
                if novel.title == self.collection.books[bkId].title:
                    self.collection.books[bkId].pull_metadata(novel)

    def _remove_book(self, event=None):
        try:
            nodeId = self._tv.selection()[0]
            elemId = nodeId[2:]
            message = ''
            try:
                if nodeId.startswith(self._BOOK_PREFIX):
                    message = self.collection.remove_book(elemId)
                    if self._tv.prev(nodeId):
                        self._tv.selection_set(self._tv.prev(nodeId))
                    elif self._tv.parent(nodeId):
                        self._tv.selection_set(self._tv.parent(nodeId))
                    self._build_tree()
            except Error as ex:
                self._show_info(str(ex))
            else:
                if message:
                    self._show_info(message)
        except IndexError:
            pass

    def _remove_series(self, event=None):
        try:
            nodeId = self._tv.selection()[0]
            elemId = nodeId[2:]
            message = ''
            try:
                if nodeId.startswith(self._SERIES_PREFIX):
                    message = self.collection.remove_series(elemId)
                    if self._tv.prev(nodeId):
                        self._tv.selection_set(self._tv.prev(nodeId))
                    elif self._tv.parent(nodeId):
                        self._tv.selection_set(self._tv.parent(nodeId))
                    self._build_tree()
            except Error as ex:
                self._show_info(str(ex))
            else:
                if message:
                    self._show_info(message)
        except IndexError:
            pass

    def _remove_node(self, event=None):
        try:
            nodeId = self._tv.selection()[0]
            if nodeId.startswith(self._SERIES_PREFIX):
                self._remove_series()
            elif nodeId.startswith(self._BOOK_PREFIX):
                self._remove_book()
        except IndexError:
            pass

    def _show_info(self, message):
        if message.startswith('!'):
            message = message.split('!', maxsplit=1)[1].strip()
            messagebox.showerror(message=message)
        else:
            messagebox.showinfo(message=message)
        self.lift()
        self.focus()

    def on_quit(self, event=None):
        try:
            self.collection.write()
        except Exception as ex:
            self._show_info(str(ex))
        finally:
            self.destroy()
            self.isOpen = False
