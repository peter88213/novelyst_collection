"""Provide a class for yWriter book series representation.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvcollectionlib.nvcollection_globals import *


class Series:
    """Book series representation for the collection.
    
    A series has a title and a description. 
    """

    def __init__(self):
        self.title = None
        self.desc = None
