"""Provide a tkinter widget for project collection management.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from nvcollectionlib.nvcollection_globals import *
from nvcollectionlib.collection import Collection


class CollectionManager(tk.Toplevel):
    _KEY_QUIT_PROGRAM = ('<Control-q>', 'Ctrl-Q')
    _SERIES_PREFIX = 'sr'
    _BOOK_PREFIX = 'bk'

    def __init__(self, title, ui, size, filePath, **kw):
        self._ui = ui
        super().__init__(**kw)
        self.title(title)
        self._statusText = ''

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
        self.seriesMenu.add_command(label=_('Add'), command=self._add_series)
        self.seriesMenu.add_command(label=_('Remove selected series but keep the books'), command=self._remove_series)
        self.seriesMenu.add_command(label=_('Remove selected series'), command=self._remove_series_with_books)

        #--- Book menu.
        self.bookMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Book'), menu=self.bookMenu)
        self.bookMenu.add_command(label=_('Add current project to collection'), command=self._add_current_project)
        self.bookMenu.add_command(label=_('Remove selected book from collection'), command=self._remove_book)
        self.bookMenu.add_command(label=_('Update book data from current project'), command=self._update_book)

        #--- Main window.
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill=tk.BOTH, padx=2, pady=2)

        #--- Tree for book selection.
        treeView = ttk.Treeview(self.mainWindow, selectmode='extended')
        treeView.pack(side=tk.LEFT, fill=tk.Y)
        treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        treeView.bind('<Double-1>', self._open_project)
        treeView.bind('<Return>', self._open_project)
        treeView.bind('<Delete>', self._remove_node)
        treeView.bind('<Shift-Delete>', self._remove_series_with_books)
        treeView.bind('<Alt-B1-Motion>', self._move_node)

        #--- The collection itself.
        self.collection = Collection(filePath, treeView)
        self.collection.read()

        # Create an "index card" in the right frame.
        self.indexCard = tk.Frame(self.mainWindow, bd=2, relief=tk.RIDGE)
        self.indexCard.pack(expand=False, fill=tk.BOTH)

        # Title label.
        self.elementTitle = tk.StringVar(value='')
        tk.Entry(self.indexCard, bd=0, textvariable=self.elementTitle, relief=tk.FLAT).pack(fill=tk.X, ipady=6)

        tk.Frame(self.indexCard, bg='red', height=1, bd=0).pack(fill=tk.X)
        tk.Frame(self.indexCard, bg='white', height=1, bd=0).pack(fill=tk.X)

        # Description window.
        self._viewer = ScrolledText(self.indexCard, wrap='word', undo=True, autoseparators=True, maxundo=-1, padx=5, pady=5)
        self._viewer.pack(fill=tk.X)

        #--- Status bar.
        self.statusBar = tk.Label(self, text='', anchor='w', padx=5, pady=2)
        self.statusBar.pack(expand=False, fill='both')

        self.bind('<Escape>', self.restore_status)
        self.isOpen = True

    def _on_select_node(self, event=None):
        """View the selected element's description."""
        self._viewer.delete('1.0', tk.END)
        try:
            nodeId = self.collection.tree.selection()[0]
            elemId = nodeId[2:]
            if nodeId.startswith(self._BOOK_PREFIX):
                title = self.collection.books[elemId].title
                desc = self.collection.books[elemId].desc
            elif nodeId.startswith(self._SERIES_PREFIX):
                title = self.collection.series[elemId].title
                desc = self.collection.series[elemId].desc
            if desc:
                self._viewer.insert(tk.END, desc)
            if title:
                self.elementTitle.set(title)
        except IndexError:
            pass

    def _open_project(self, event=None):
        """Make the application open the selected book's project."""
        try:
            nodeId = self.collection.tree.selection()[0]
            if nodeId.startswith(self._BOOK_PREFIX):
                bkId = nodeId[2:]
                self._ui.open_project(self.collection.books[bkId].filePath)
        except IndexError:
            pass

    def _add_current_project(self, event=None):
        try:
            selection = self.collection.tree.selection()[0]
        except:
            selection = ''
        if selection.startswith(self._BOOK_PREFIX):
            parent = self.collection.tree.parent(selection)
        elif selection.startswith(self._SERIES_PREFIX):
            parent = selection
        index = self.collection.tree.index(selection) + 1
        novel = self._ui.ywPrj
        if novel is not None:
            try:
                bkId = self.collection.add_book(novel, parent, index)
            except Error as ex:
                self.set_info_how(str(ex))
            else:
                if bkId is not None:
                    self.set_info_how(f'"{novel.title}" added to the collection.')
                else:
                    self.set_info_how(f'!"{novel.title}" already exists.')

    def _update_book(self, event=None):
        novel = self._ui.novel
        if novel is not None:
            for bkId in self.collection.books:
                if novel.title == self.collection.books[bkId].title:
                    self.collection.books[bkId].pull_metadata(novel)

    def _remove_book(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(self._BOOK_PREFIX):
                    if self.collection.tree.prev(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                    elif self.collection.tree.parent(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                    message = self.collection.remove_book(nodeId)
            except Error as ex:
                self.set_info_how(str(ex))
            else:
                if message:
                    self.set_info_how(message)
        except IndexError:
            pass

    def _add_series(self, event=None):
        try:
            selection = self.collection.tree.selection()[0]
        except:
            selection = ''
        title = 'New Series'
        index = 0
        if selection.startswith(self._SERIES_PREFIX):
            index = self.collection.tree.index(selection) + 1
        try:
            self.collection.add_series(title, index)
        except Error as ex:
            self.set_info_how(str(ex))

    def _remove_series(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(self._SERIES_PREFIX):
                    if self.collection.tree.prev(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                    elif self.collection.tree.parent(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                    message = self.collection.remove_series(nodeId)
            except Error as ex:
                self.set_info_how(str(ex))
            else:
                if message:
                    self.set_info_how(message)
        except IndexError:
            pass

    def _remove_series_with_books(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(self._SERIES_PREFIX):
                    if self.collection.tree.prev(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                    elif self.collection.tree.parent(nodeId):
                        self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                    message = self.collection.remove_series_with_books(nodeId)
            except Error as ex:
                self.set_info_how(str(ex))
            else:
                if message:
                    self.set_info_how(message)
        except IndexError:
            pass

    def _remove_node(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
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

    def set_info_how(self, message):
        """Show how the converter is doing.
        
        Positional arguments:
            message -- message to be displayed. 
            
        Display the message at the status bar.
        Overrides the superclass method.
        """
        if message.startswith('!'):
            self.statusBar.config(bg='red')
            self.statusBar.config(fg='white')
            self.infoHowText = message.split('!', maxsplit=1)[1].strip()
        else:
            self.statusBar.config(bg='green')
            self.statusBar.config(fg='white')
            self.infoHowText = message
        self.statusBar.config(text=self.infoHowText)

    def show_status(self, message):
        """Put text on the status bar."""
        self._statusText = message
        self.statusBar.config(bg=self.cget('background'))
        self.statusBar.config(fg='black')
        self.statusBar.config(text=message)

    def restore_status(self, event=None):
        """Overwrite error message with the status before."""
        self.show_status(self._statusText)

    def _move_node(self, event):
        """Move a selected node in the collection tree."""
        tv = event.widget
        node = tv.selection()[0]
        targetNode = tv.identify_row(event.y)

        if node[:2] == targetNode[:2]:
            tv.move(node, tv.parent(targetNode), tv.index(targetNode))
        elif node.startswith(self._BOOK_PREFIX) and targetNode.startswith(self._SERIES_PREFIX) and not tv.get_children(targetNode):
            tv.move(node, targetNode, 0)

