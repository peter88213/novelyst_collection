"""Provide global variables and functions.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/nv_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import sys
import gettext
import locale

__all__ = ['Error',
           '_',
           'norm_path',
           'LOCALE_PATH',
           'CURRENT_LANGUAGE',
           'APPLICATION',
           'PLUGIN',
           'SERIES_PREFIX',
           'BOOK_PREFIX',
           ]


class Error(Exception):
    """Base class for exceptions."""


# Initialize localization.
LOCALE_PATH = f'{os.path.dirname(sys.argv[0])}/locale/'
CURRENT_LANGUAGE = locale.getlocale()[0][:2]
try:
    t = gettext.translation('novelyst_collection', LOCALE_PATH, languages=[CURRENT_LANGUAGE])
    _ = t.gettext
except:

    def _(message):
        return message

APPLICATION = _('Collection')
PLUGIN = f'{APPLICATION} plugin v@release'
SERIES_PREFIX = 'sr'
BOOK_PREFIX = 'bk'


def norm_path(path):
    if path is None:
        path = ''
    return os.path.normpath(path)

