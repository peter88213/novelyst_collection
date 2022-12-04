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
    tree_width='300',
)
OPTIONS = {}


class CollectionManager(tk.Toplevel):
    _KEY_QUIT_PROGRAM = ('<Control-q>', 'Ctrl-Q')
    _SERIES_PREFIX = 'sr'
    _BOOK_PREFIX = 'bk'

    def __init__(self, ui, position, configDir):
        self._ui = ui
        super().__init__()

        #--- Load configuration.
        self.iniFile = f'{configDir}/collection.ini'
        self.configuration = Configuration(SETTINGS, OPTIONS)
        self.configuration.read(self.iniFile)
        self.kwargs = {}
        self.kwargs.update(self.configuration.settings)
        # Read the file path from the configuration file.

        self.title(PLUGIN)
        self._statusText = ''

        self.geometry(position)
        self.lift()
        self.focus()
        self.protocol("WM_DELETE_WINDOW", self.on_quit)
        self.bind(self._KEY_QUIT_PROGRAM[0], self.on_quit)

        #--- Main menu.
        self.mainMenu = tk.Menu(self)
        self.config(menu=self.mainMenu)

        #--- Main window.
        self.mainWindow = ttk.Frame(self)
        self.mainWindow.pack(fill=tk.BOTH, padx=2, pady=2)

        #--- Paned window displaying the tree and an "index card".
        self.treeWindow = ttk.Panedwindow(self.mainWindow, orient=tk.HORIZONTAL)
        self.treeWindow.pack(fill=tk.BOTH, expand=True)

        #--- The collection itself.
        self.collection = None
        self._fileTypes = [(_('novelyst collection'), '.pwc')]

        #--- Tree for book selection.
        self.treeView = ttk.Treeview(self.treeWindow, selectmode='browse')
        self.treeView.pack(side=tk.LEFT)
        self.treeWindow.add(self.treeView)
        self.treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self.treeView.bind('<<TreeviewSelect>>', self._on_select_node)
        self.treeView.bind('<Double-1>', self._open_book)
        self.treeView.bind('<Return>', self._open_book)
        self.treeView.bind('<Delete>', self._remove_node)
        self.treeView.bind('<Shift-Delete>', self._remove_series_with_books)
        self.treeView.bind('<Alt-B1-Motion>', self._move_node)

        #--- "Index card" in the right frame.
        self.indexCard = tk.Frame(self.treeWindow, bd=2, relief=tk.RIDGE)
        self.indexCard.pack(side=tk.RIGHT)
        self.treeWindow.add(self.indexCard)

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

        # Adjust the tree width.
        self.treeWindow.update()
        self.treeWindow.sashpos(0, self.kwargs['tree_width'])

        # Status bar.
        self.statusBar = tk.Label(self, text='', anchor='w', padx=5, pady=2)
        self.statusBar.pack(expand=False, fill='both')

        # Path bar.
        self.pathBar = tk.Label(self, text='', anchor='w', padx=5, pady=3)
        self.pathBar.pack(expand=False, fill='both')

        #--- Add menu entries.
        # File menu.
        self.fileMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('File'), menu=self.fileMenu)
        self.fileMenu.add_command(label=_('New'), command=self.new_collection)
        self.fileMenu.add_command(label=_('Open...'), command=lambda: self.open_collection(''))
        self.fileMenu.add_command(label=_('Close'), command=self.close_collection)
        self.fileMenu.entryconfig(_('Close'), state='disabled')
        self.fileMenu.add_command(label=_('Exit'), accelerator=self._KEY_QUIT_PROGRAM[1], command=self.on_quit)

        # Series menu.
        self.seriesMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Series'), menu=self.seriesMenu)
        self.seriesMenu.add_command(label=_('Add'), command=self._add_series)
        self.seriesMenu.add_command(label=_('Remove selected series but keep the books'), command=self._remove_series)
        self.seriesMenu.add_command(label=_('Remove selected series and books'), command=self._remove_series_with_books)

        # Book menu.
        self.bookMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Book'), menu=self.bookMenu)
        self.bookMenu.add_command(label=_('Add current project to the collection'), command=self._add_current_project)
        self.bookMenu.add_command(label=_('Remove selected book from the collection'), command=self._remove_book)
        self.bookMenu.add_command(label=_('Update book data from the current project'), command=self._update_book)

        #--- Event bindings.
        self.bind('<Escape>', self.restore_status)

        self.isModified = False
        self._element = None
        self._nodeId = None
        if self.open_collection(self.kwargs['last_open']):
            self.isOpen = True

    #--- Application related methods.

    def _on_select_node(self, event=None):
        self._get_element_view()
        try:
            self._nodeId = self.collection.tree.selection()[0]
            elemId = self._nodeId[2:]
            if self._nodeId.startswith(self._BOOK_PREFIX):
                self._element = self.collection.books[elemId]
            elif self._nodeId.startswith(self._SERIES_PREFIX):
                self._element = self.collection.series[elemId]
        except IndexError:
            pass
        except AttributeError:
            pass
        else:
            self._set_element_view()

    def _set_element_view(self, event=None):
        """View the selected element's title and description."""
        self._viewer.clear()
        if self._element.desc:
            self._viewer.set_text(self._element.desc)
        if self._element.title:
            self.elementTitle.set(self._element.title)

    def _get_element_view(self, event=None):
        """Apply changes."""
        try:
            title = self.elementTitle.get()
            if title or self._element.title:
                if self._element.title != title:
                    self._element.title = title.strip()
                    self.collection.tree.item(self._nodeId, text=self._element.title)
                    self.isModified = True
            if self._viewer.hasChanged:
                self._element.desc = self._viewer.get_text()
                self.isModified = True
        except AttributeError:
            pass

    def _show_info(self, message):
        if message.startswith('!'):
            message = message.split('!', maxsplit=1)[1].strip()
            messagebox.showerror(APPLICATION, message=message, parent=self)
        else:
            messagebox.showinfo(APPLICATION, message=message, parent=self)
        self.lift()
        self.focus()

    def on_quit(self, event=None):
        self._get_element_view()
        self.kwargs['tree_width'] = self.treeWindow.sashpos(0)

        #--- Save project specific configuration
        for keyword in self.kwargs:
            if keyword in self.configuration.options:
                self.configuration.options[keyword] = self.kwargs[keyword]
            elif keyword in self.configuration.settings:
                self.configuration.settings[keyword] = self.kwargs[keyword]
        self.configuration.write(self.iniFile)
        try:
            if self.collection is not None:
                if self.isModified:
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
            self.isModified = True
        elif node.startswith(self._BOOK_PREFIX) and targetNode.startswith(self._SERIES_PREFIX) and not tv.get_children(targetNode):
            tv.move(node, targetNode, 0)
            self.isModified = True

    #--- Project related methods.

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
        parent = ''
        if selection.startswith(self._BOOK_PREFIX):
            parent = self.collection.tree.parent(selection)
        elif selection.startswith(self._SERIES_PREFIX):
            parent = selection
        index = self.collection.tree.index(selection) + 1
        book = self._ui.prjFile
        if book is not None:
            try:
                bkId = self.collection.add_book(book, parent, index)
                self.isModified = True
            except Error as ex:
                self.set_info_how(str(ex))
            else:
                if bkId is not None:
                    self.set_info_how(f'"{book.novel.title}" added to the collection.')
                else:
                    self.set_info_how(f'!"{book.novel.title}" already exists.')

    def _update_book(self, event=None):
        novel = self._ui.novel
        if novel is not None:
            for bkId in self.collection.books:
                if novel.title == self.collection.books[bkId].title:
                    if self.collection.books[bkId].pull_metadata(novel):
                        self.isModified = True
                        if self._nodeId == f'{self._BOOK_PREFIX}{bkId}':
                            self._set_element_view()

    def _remove_book(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(self._BOOK_PREFIX):
                    if messagebox.askyesno(APPLICATION, message=f'{_("Remove selected book from the collection")}?', parent=self):
                        if self.collection.tree.prev(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                        elif self.collection.tree.parent(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                        message = self.collection.remove_book(nodeId)
                        self.isModified = True
                        self.lift()
                        self.focus()
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
            self.isModified = True
        except Error as ex:
            self.set_info_how(str(ex))

    def _remove_series(self, event=None):
        try:
            nodeId = self.collection.tree.selection()[0]
            message = ''
            try:
                if nodeId.startswith(self._SERIES_PREFIX):
                    if messagebox.askyesno(APPLICATION, message=f'{_("Remove selected series but keep the books")}?', parent=self):
                        if self.collection.tree.prev(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                        elif self.collection.tree.parent(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                        message = self.collection.remove_series(nodeId)
                        self.isModified = True
                        self.lift()
                        self.focus()
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
                    if messagebox.askyesno(APPLICATION, message=f'{_("Remove selected series and books")}?', parent=self):
                        if self.collection.tree.prev(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.prev(nodeId))
                        elif self.collection.tree.parent(nodeId):
                            self.collection.tree.selection_set(self.collection.tree.parent(nodeId))
                        message = self.collection.remove_series_with_books(nodeId)
                        self.isModified = True
                        self.lift()
                        self.focus()
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
            self.isModified = True
        except IndexError:
            pass

    #--- Collection related methods.

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
            fileName = filedialog.askopenfilename(filetypes=self._fileTypes, defaultextension=self._fileTypes[0][1], initialdir=initDir, parent=self)
        if not fileName:
            return ''

        return fileName

    def open_collection(self, fileName):
        """Create a Collection instance and read the file.

        Positional arguments:
            fileName -- str: collection file path.
            
        Display collection title and file path.
        Return True on success, otherwise return False.
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

    def new_collection(self, event=None):
        """Create a collection.

        Display collection title and file path.
        Return True on success, otherwise return False.
        """
        fileName = filedialog.asksaveasfilename(filetypes=self._fileTypes, defaultextension=self._fileTypes[0][1])
        self.lift()
        self.focus()
        if not fileName:
            return False

        if self.collection is not None:
            self.close_collection()

        self.collection = Collection(fileName, self.treeView)
        self.kwargs['last_open'] = fileName
        self.show_path(f'{norm_path(self.collection.filePath)}')
        self.set_title()
        self.fileMenu.entryconfig(_('Close'), state='normal')
        return True

    def close_collection(self, event=None):
        """Close the collection without saving and reset the user interface.
        
        To be extended by subclasses.
        """
        self._get_element_view()
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
            collectionTitle = self.collection.title
        else:
            collectionTitle = _('Untitled collection')
        self.title(f'{collectionTitle} - {PLUGIN}')

