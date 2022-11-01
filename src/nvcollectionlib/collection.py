"""Provide a class representing a collection of yWriter projects.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import re
import xml.etree.ElementTree as ET
from html import unescape

from nvcollectionlib.nvcollection_globals import *
from pywriter.yw.xml_indent import indent

from nvcollectionlib.series import Series
from nvcollectionlib.book import Book


class Collection:
    """Represent a collection of yWriter projects. 
    
    - A collection has books and series.
    - Books can be members of a series.
    
    The collection data is saved in an XML file.
    """
    _FILE_EXTENSION = 'pwc'

    _CDATA_TAGS = ['Title', 'Desc', 'Path']
    # Names of xml elements containing CDATA.
    # ElementTree.write omits CDATA tags, so they have to be inserted afterwards.

    def __init__(self, filePath):
        """Initialize the instance variables.
        
        Positional argument:
            filePath -- str: path to xml file.
        """
        self.books = {}
        # Dictionary:
        #   keyword -- book ID
        #   value -- Book instance

        self.srtSeries = []
        # List of series IDs

        self._filePath = None
        # Location of the collection XML file.

        self.filePath = filePath

    @property
    def filePath(self):
        return self._filePath

    @filePath.setter
    def filePath(self, filePath):
        """Accept only filenames with the right extension. """
        if filePath.lower().endswith(self._FILE_EXTENSION):
            self._filePath = filePath

    def read(self):
        """Parse the pwc XML file located at filePath, fetching the Collection attributes.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """

        # Open the file and let ElementTree parse its xml structure.
        try:
            tree = ET.parse(self._filePath)
            root = tree.getroot()
        except:
            raise Error(f'Can not process "{self._filePath}".')

        for series in root.iter('SERIES'):
            newSeries = Series(series.find('Title').text)
            if series.find('Desc') is not None:
                newSeries.desc = series.find('Desc').text
            newSeries.srtBooks = []
            if series.find('Books') is not None:
                for book in series.find('Books').findall('BkID'):
                    bkId = book.text
                    newSeries.srtBooks.append(bkId)
            self.srtSeries.append(newSeries)
        for book in root.iter('BOOK'):
            bkId = book.find('ID').text
            bookPath = book.find('Path').text
            if os.path.isfile(bookPath):
                self.books[bkId] = Book(bookPath)
                if book.find('Title') is not None:
                    self.books[bkId].title = book.find('Title').text
                if book.find('Desc') is not None:
                    self.books[bkId].desc = book.find('Desc').text
        return f'{len(self.books)} Books found in "{self._filePath}".'

    def write(self):
        """Write the collection's attributes to a pwc XML file located at filePath. 
        
        Overwrite existing file without confirmation.
        Return a message.
        Raise the "Error" exception in case of error.
        """
        root = ET.Element('COLLECTION')
        bkSection = ET.SubElement(root, 'BOOKS')
        for bookId in self.books:
            newBook = ET.SubElement(bkSection, 'BOOK')
            bkId = ET.SubElement(newBook, 'ID')
            bkId.text = bookId
            bkPath = ET.SubElement(newBook, 'Path')
            bkPath.text = self.books[bookId].filePath
            bkTitle = ET.SubElement(newBook, 'Title')
            bkTitle.text = self.books[bookId].title
            bkDesc = ET.SubElement(newBook, 'Desc')
            bkDesc.text = self.books[bookId].desc
        srSection = ET.SubElement(root, 'SRT_SERIES')
        for series in self.srtSeries:
            newSeries = ET.SubElement(srSection, 'SERIES')
            serTitle = ET.SubElement(newSeries, 'Title')
            serTitle.text = series.title
            serDesc = ET.SubElement(newSeries, 'Desc')
            serDesc.text = series.desc
            serBooks = ET.SubElement(newSeries, 'Books')
            for bookId in series.srtBooks:
                bkId = ET.SubElement(serBooks, 'BkID')
                bkId.text = bookId
        indent(root)
        tree = ET.ElementTree(root)
        try:
            tree.write(self._filePath, encoding='utf-8')
        except(PermissionError):
            raise Error(f'"{self._filePath}" is write protected.')

        # Postprocess the xml file created by ElementTree
        self._postprocess_xml_file(self.filePath)
        return f'"{os.path.normpath(self.filePath)}" written.'

    def add_book(self, novel):
        """Add an existing yw7 file as book to the collection. 
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        if os.path.isfile(novel.filePath):
            i = 1
            while str(i) in self.books:
                i += 1
            bkId = str(i)
            self.books[bkId] = Book(novel.filePath)
            self.books[bkId].pull_metadata(novel)
            return f'"{novel.title}" added to the collection.'

        else:
            raise Error(f'"{os.path.normpath(novel.filePath)}" not found.')

    def remove_book(self, bkId):
        """Remove a book from the collection and from the series.

        Return a message.
        Raise the "Error" exception in case of error.
        """
        try:
            bookTitle = self.books[bkId].title
            del self.books[bkId]
            for series in self.srtSeries:
                try:
                    series.remove_book(bkId)
                except Error:
                    pass
                else:
                    return f'Book "{bookTitle}" removed from "{series.title}" series.'

        except:
            raise Error(f'Cannot remove "{bookTitle}".')

    def add_series(self, serTitle):
        """Instantiate a Series object and append it to the srtSeries list.
        
        Avoid multiple entries.
        Return True on success, 
        return False, if the series is already a member.         
        """
        for series in self.srtSeries:
            if series.title == serTitle:
                return False

        newSeries = Series(serTitle)
        self.srtSeries.append(newSeries)
        return True

    def remove_series(self, serTitle):
        """Delete a Series object and remove it from the srtSeries list.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        for series in self.srtSeries:
            if series.title == serTitle:
                self.srtSeries.remove(series)
                return f'"{serTitle}" series removed from the collection.'

        raise Error(f'Cannot remove "{serTitle}" series from the collection.')

    def _postprocess_xml_file(self, filePath):
        '''Postprocess an xml file created by ElementTree.
        
        Positional argument:
            filePath -- str: path to xml file.
        
        Read the xml file, put a header on top, insert the missing CDATA tags,
        and replace xml entities by plain text (unescape). Overwrite the .yw7 xml file.
        Raise the "Error" exception in case of error. 
        
        Note: The path is given as an argument rather than using self.filePath. 
        So this routine can be used for yWriter-generated xml files other than .yw7 as well. 
        '''
        with open(filePath, 'r', encoding='utf-8') as f:
            text = f.read()
        lines = text.split('\n')
        newlines = ['<?xml version="1.0" encoding="utf-8"?>']
        for line in lines:
            for tag in self._CDATA_TAGS:
                line = re.sub(f'\<{tag}\>', f'<{tag}><![CDATA[', line)
                line = re.sub(f'\<\/{tag}\>', f']]></{tag}>', line)
            newlines.append(line)
        text = '\n'.join(newlines)
        text = text.replace('[CDATA[ \n', '[CDATA[')
        text = text.replace('\n]]', ']]')
        text = unescape(text)
        try:
            with open(filePath, 'w', encoding='utf-8') as f:
                f.write(text)
        except:
            raise Error(f'{_("Cannot write file")}: "{os.path.normpath(filePath)}".')

