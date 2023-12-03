"""Provide a class for a book representation.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/noveltree_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""


class Book:
    """Book representation for the collection.
    
    This is a lightweight placeholder for a novelyst project file instance,
    holding only the necessary metadata. 
    """

    def __init__(self, filePath):
        self.filePath = filePath
        self.title = None
        self.desc = None

    def pull_metadata(self, novel):
        """Update metadata from novel.

        Return True, if the novel is modified, 
        otherwise return False. 
        """
        modified = False
        if self.title != novel.title:
            self.title = novel.title
            modified = True
        if self.desc != novel.desc:
            self.desc = novel.desc
            modified = True
        return modified

    def push_metadata(self, novel):
        """Update novel metadata.
        
        Return True, if the novel is modified, 
        otherwise return False. 
        """
        modified = False
        if novel.title != self.title:
            novel.title = self.title
        if novel.desc != self.desc:
            novel.desc = self.desc
            modified = True
        return modified

