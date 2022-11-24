"""A test application for the novelyst_collection plugin.

For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from pywriter.ui.main_tk import MainTk
from novelyst_collection import Plugin

APPLICATION = 'Collection'


class CollectionTk(MainTk):

    def __init__(self):
        kwargs = {
                'root_geometry': '800x500',
                'yw_last_open': '',
                'color_text_bg':'white',
                'color_text_fg':'black',
                }
        super().__init__(APPLICATION, **kwargs)
        plugin = Plugin()
        plugin.install(self)


if __name__ == '__main__':
    ui = CollectionTk()
    ui.start()

