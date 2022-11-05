"""Provide a class for yWriter book series representation.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
from nvcollectionlib.nvcollection_globals import *


class Series:
    """Book series representation for the collection.
    
    A series has a title, a description, and a list of book IDs. 
    """

    def __init__(self):
        self.title = None
        self.desc = None
        self.srtBooks = []

    def add_book(self, bkId):
        """Add a new book ID to the list. 
        
        Avoid multiple entries.
        Return True on success, 
        return False, if the book is already a member.  
        """
        if (bkId in self.srtBooks):
            return False
        else:
            self.srtBooks.append(bkId)
            return True

    def remove_book(self, bkId):
        """Remove an existing book ID from the list.       

        Return a message.
        Raise the "Error" exception in case of error.
        """
        try:
            self.srtBooks.remove(bkId)
            return 'Book removed from series.'
        except:
            raise Error(f'Cannot remove book from the list.')
