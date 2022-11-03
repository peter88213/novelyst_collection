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

    def __init__(self, ui, windowGeometry, collection, **kw):
        self._ui = ui
        super().__init__(**kw)
        self.geometry(windowGeometry)
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

        #--- Book menu.
        self.bookMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Book'), menu=self.bookMenu)
        self.bookMenu.add_command(label=_('Update book data from current project'), command=self._update_book)
        self.bookMenu.add_command(label=_('Add current project to collection'), command=self._add_current_project)
        self.bookMenu.add_command(label=_('Remove selected book from collection'), command=self._remove_selected_book)

        #--- Main window.
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill=tk.BOTH, padx=2, pady=2)
        self.collection = collection

        #--- Listbox for book selection.
        self.listbox = tk.Listbox(self.mainWindow, selectmode=tk.SINGLE)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.bind('<<ListboxSelect>>', self._show_desc)
        self.listbox.bind('<Double-1>', self._open_project)
        self.listbox.bind('<Return>', self._open_project)

        #--- Viewer window for the description.
        self.viewer = tk.Text(self.mainWindow, wrap='word')
        self.viewer.pack()

        self._build_tree()

    def _build_tree(self):
        self.listbox.delete(0, tk.END)
        self.booklist = []
        for bkId in self.collection.books:
            self.booklist.append(bkId)
            self.listbox.insert(tk.END, self.collection.books[bkId].title)

    def _show_desc(self, event=None):
        """View the selected book's description."""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self.viewer.delete('1.0', tk.END)
            desc = self.collection.books[self.booklist[index]].desc
            if desc:
                self.viewer.insert(tk.END, desc)

    def _open_project(self, event=None):
        """Make the application open the selected book's project."""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            self._ui.open_project(self.collection.books[self.booklist[index]].filePath)

    def _add_current_project(self, event=None):
        novel = self._ui.ywPrj
        if novel is not None:
            try:
                bkId = self.collection.add_book(novel)
            except Error as ex:
                self._show_info(str(ex))
            else:
                if bkId is not None:
                    self.booklist.append(bkId)
                    self.listbox.insert(tk.END, self.collection.books[bkId].title)
                    self._show_info(f'"{novel.title}" added to the collection.')
                else:
                    self._show_info(f'!"{novel.title}" already exists.')

    def _update_book(self, event=None):
        novel = self._ui.ywPrj
        if novel is not None:
            for bkId in self.collection.books:
                if novel.title == self.collection.books[bkId].title:
                    self.collection.books[bkId].pull_metadata(novel)

    def _remove_selected_book(self, event=None):
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            bkId = self.booklist.pop(index)
            message = ''
            try:
                message = self.collection.remove_book(bkId)
                self.listbox.delete(index)
            except Error as ex:
                self._show_info(str(ex))
            else:
                if message:
                    self._show_info(message)

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
