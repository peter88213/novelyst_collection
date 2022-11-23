"""Provide a tkinter widget for project collection management.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from novelystlib.widgets.text_box import TextBox
from nvcollectionlib.nvcollection_globals import *
from nvcollectionlib.collection import Collection
from nvcollectionlib.configuration import Configuration

SETTINGS = dict(
    last_open='',
)
OPTIONS = {}


class CollectionManager(tk.Toplevel):
    _KEY_QUIT_PROGRAM = ('<Control-q>', 'Ctrl-Q')
    _SERIES_PREFIX = 'sr'
    _BOOK_PREFIX = 'bk'

    def __init__(self, title, ui, size, configDir):
        self._ui = ui
        super().__init__()
        self.title(title)
        self._statusText = ''

        self.geometry(size)
        self.lift()
        self.focus()
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.bind(self._KEY_QUIT_PROGRAM[0], self.on_quit)

        #--- Load configuration.
        self.iniFile = f'{configDir}/collection.ini'
        self.configuration = Configuration(SETTINGS, OPTIONS)
        self.configuration.read(self.iniFile)
        self.kwargs = {}
        self.kwargs.update(self.configuration.settings)
        # Read the file path from the configuration file.

        #--- Main menu.
        self.mainMenu = tk.Menu(self)
        self.config(menu=self.mainMenu)

        #--- Main window.
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill=tk.BOTH, padx=2, pady=2)

        #--- The collection itself.
        self.collection = None
        self._fileTypes = [(_('novelyst collection'), '.pwc')]

        #--- Tree for book selection.
        self.treeView = ttk.Treeview(self.mainWindow, selectmode='extended')
        self.treeView.pack(side=tk.LEFT, fill=tk.Y)
        self.treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self.treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self.treeView.bind('<Double-1>', self._open_book)
        self.treeView.bind('<Return>', self._open_book)
        self.treeView.bind('<Delete>', self._remove_node)
        self.treeView.bind('<Shift-Delete>', self._remove_series_with_books)
        self.treeView.bind('<Alt-B1-Motion>', self._move_node)

        # Create an "index card" in the right frame.
        self.indexCard = tk.Frame(self.mainWindow, bd=2, relief=tk.RIDGE)
        self.indexCard.pack(expand=False, fill=tk.BOTH)

        # Title label.
        self.elementTitle = tk.StringVar(value='')
        titleEntry = tk.Entry(self.indexCard, bd=0, textvariable=self.elementTitle, relief=tk.FLAT)
        titleEntry.config({'background': self._ui.kwargs['color_text_bg'],
                           'foreground': self._ui.kwargs['color_text_fg'],
                           'insertbackground': self._ui.kwargs['color_text_fg'],
                           })
        titleEntry.pack(fill=tk.X, ipady=6)

        tk.Frame(self.indexCard, bg='red', height=1, bd=0).pack(fill=tk.X)
        tk.Frame(self.indexCard, bg='white', height=1, bd=0).pack(fill=tk.X)

        # Description window.
        self._viewer = TextBox(self.indexCard,
                wrap='word',
                undo=True,
                autoseparators=True,
                maxundo=-1,
                padx=5,
                pady=5,
                bg=self._ui.kwargs['color_text_bg'],
                fg=self._ui.kwargs['color_text_fg'],
                insertbackground=self._ui.kwargs['color_text_fg'],
                )
        self._viewer.pack(fill=tk.X)

        # Status bar.
        self.statusBar = tk.Label(self, text='', anchor='w', padx=5, pady=2)
        self.statusBar.pack(expand=False, fill='both')

        # Path bar.
        self.pathBar = tk.Label(self, text='', anchor='w', padx=5, pady=3)
        self.pathBar.pack(expand=False, fill='both')

        self.bind('<Escape>', self.restore_status)
        self._build_main_menu()

        self.open_collection(self.kwargs['last_open'])
        self.isOpen = True

    def _build_main_menu(self):
        """Add main menu entries."""
        #--- File menu.
        self.fileMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('File'), menu=self.fileMenu)
        self.fileMenu.add_command(label=_('Open...'), command=lambda: self.open_collection(''))
        self.fileMenu.add_command(label=_('Close'), command=self.close_collection)
        self.fileMenu.entryconfig(_('Close'), state='disabled')
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

    def _on_select_node(self, event=None):
        """View the selected element's description."""
        self._viewer.clear()
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
                self._viewer.set_text(desc)
            if title:
                self.elementTitle.set(title)
        except IndexError:
            pass
        except AttributeError:
            pass

    def _open_book(self, event=None):
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
        novel = self._ui.prjFile
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
        #--- Save project specific configuration
        for keyword in self.kwargs:
            if keyword in self.configuration.options:
                self.configuration.options[keyword] = self.kwargs[keyword]
            elif keyword in self.configuration.settings:
                self.configuration.settings[keyword] = self.kwargs[keyword]
        self.configuration.write(self.iniFile)
        try:
            if self.collection is not None:
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

    def show_path(self, message):
        """Put text on the path bar."""
        self._pathText = message
        self.pathBar.config(text=message)

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

    def select_collection(self, fileName):
        """Return a collection file path.

        Positional arguments:
            fileName -- str: collection file path.
            
        Optional arguments:
            fileTypes -- list of tuples for file selection (display text, extension).

        Priority:
        1. use file name argument
        2. open file select dialog

        On error, return an empty string.
        """
        initDir = os.path.dirname(self.kwargs['last_open'])
        if not initDir:
            initDir = './'
        if not fileName or not os.path.isfile(fileName):
            fileName = filedialog.askopenfilename(filetypes=self._fileTypes, defaultextension='.pwc', initialdir=initDir)
        if not fileName:
            return ''

        return fileName

    def open_collection(self, fileName):
        """Create a Collection instance and read the file.

        Positional arguments:
            fileName -- str: collection file path.
            
        Display collection title and file path.
        Return True on success, otherwise return False.
        To be extended by subclasses.
        """
        self.show_status(self._statusText)
        fileName = self.select_collection(fileName)
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self.collection is not None:
            self.close_collection()

        self.kwargs['last_open'] = fileName
        self.collection = Collection(fileName, self.treeView)
        try:
            self.collection.read()
        except Error as ex:
            self.close_collection()
            self.set_info_how(f'!{str(ex)}')
            return False

        self.show_path(f'{norm_path(self.collection.filePath)}')
        self.set_title()
        self.fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def close_collection(self, event=None):
        """Close the collection without saving and reset the user interface.
        
        To be extended by subclasses.
        """
        self.elementTitle.set('')
        self._viewer.clear()
        self.collection.reset_tree()
        self.collection = None
        self.title('')
        self.show_status('')
        self.show_path('')
        self.fileMenu.entryconfig(_('Close'), state='disabled')

    def set_title(self):
        """Set the main window title. 
        
        'Collection title - application'
        """
        if self.collection.title:
            titleView = self.collection.title
        else:
            titleView = _('Untitled collection')
        self.title(titleView)

