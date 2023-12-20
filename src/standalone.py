"""A standalone application for the novelyst_collection plugin.

For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from novxlib.novx_globals import _
from novxlib.ui.main_tk import MainTk
from nv_collection import Plugin
import tkinter as tk

APPLICATION = 'Collection'


class CollectionTk(MainTk):

    def __init__(self):
        kwargs = {
                'root_geometry': '800x500',
                'last_open': '',
                'color_text_bg':'white',
                'color_text_fg':'black',
                }
        super().__init__(APPLICATION, **kwargs)
        self.helpMenu = tk.Menu(self.mainMenu, tearoff=0)
        self.mainMenu.add_cascade(label=_('Help'), menu=self.helpMenu)
        plugin = Plugin()
        plugin.install(self)


if __name__ == '__main__':
    ui = CollectionTk()
    ui.start()

