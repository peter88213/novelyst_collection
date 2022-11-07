"""Provide a class representing a collection of yWriter projects.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import re
import xml.etree.ElementTree as ET
from html import unescape
import tkinter as tk
from tkinter import ttk

from nvcollectionlib.nvcollection_globals import *
from pywriter.yw.xml_indent import indent
from pywriter.model.id_generator import create_id

from nvcollectionlib.series import Series
from nvcollectionlib.book import Book


class Collection(ttk.Treeview):
    """Represent a collection of yWriter projects. 
    
    - A collection has books and series.
    - Books can be members of a series.
    
    The collection data is saved in an XML file.
    """
    _FILE_EXTENSION = 'pwc'
    _SERIES_PREFIX = 'sr'
    _BOOK_PREFIX = 'bk'

    _CDATA_TAGS = ['Title', 'Desc', 'Path']
    # Names of xml books containing CDATA.
    # ElementTree.write omits CDATA tags, so they have to be inserted afterwards.

    def __init__(self, filePath, master=None, **kw):
        """Initialize the instance variables.
        
        Positional argument:
            filePath -- str: path to xml file.
        """
        super().__init__(master, **kw)
        self.books = {}
        # Dictionary:
        #   keyword -- book ID
        #   value -- Book instance

        self.series = {}
        # Dictionary:
        #   keyword -- series ID
        #   value -- Series instance

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

        def get_book(parent, xmlBook):
            try:
                bkId = xmlBook.attrib['ID']
                bookPath = xmlBook.find('Path').text
                if os.path.isfile(bookPath):
                    self.books[bkId] = Book(bookPath)
                    if xmlBook.find('Title') is not None:
                        self.books[bkId].title = xmlBook.find('Title').text
                    if xmlBook.find('Desc') is not None:
                        self.books[bkId].desc = xmlBook.find('Desc').text
            except:
                pass
            else:
                item = f'{self._BOOK_PREFIX}{bkId}'
                self.insert(parent, tk.END, item, text=self.books[bkId].title, open=True)

        # Open the file and let ElementTree parse its xml structure.
        try:
            xmlTree = ET.parse(self._filePath)
            xmlRoot = xmlTree.getroot()
        except:
            raise Error(f'Can not process "{self._filePath}".')

        self._reset_tree()
        self.books = {}
        self.series = {}
        for xmlElement in xmlRoot:
            if xmlElement.tag == 'BOOK':
                get_book('', xmlElement)
            elif xmlElement.tag == 'SERIES':
                srId = xmlElement.attrib['ID']
                self.series[srId] = Series()
                if xmlElement.find('Title') is not None:
                    self.series[srId].title = xmlElement.find('Title').text
                if xmlElement.find('Desc') is not None:
                    self.series[srId].desc = xmlElement.find('Desc').text
                item = f'{self._SERIES_PREFIX}{srId}'
                self.insert('', tk.END, item, text=self.series[srId].title, open=True)
                for xmlBook in xmlElement.iter('BOOK'):
                    get_book(item, xmlBook)

        return f'{len(self.books)} Books found in "{self._filePath}".'

    def write(self):
        """Write the collection's attributes to a pwc XML file located at filePath. 
        
        Overwrite existing file without confirmation.
        Return a message.
        Raise the "Error" exception in case of error.
        """

        def walk_tree(node, xmlNode):
            """Transform the treeview nodes to XML Elementtree nodes."""
            for childNode in self.get_children(node):
                elementId = childNode[2:]
                if childNode.startswith(self._BOOK_PREFIX):
                    xmlBook = ET.SubElement(xmlNode, 'BOOK')
                    xmlBook.set('ID', elementId)
                    xmlBookPath = ET.SubElement(xmlBook, 'Path')
                    xmlBookPath.text = self.books[elementId].filePath
                    xmlBookTitle = ET.SubElement(xmlBook, 'Title')
                    if self.books[elementId].title:
                        xmlBookTitle.text = self.books[elementId].title
                    xmlBookDesc = ET.SubElement(xmlBook, 'Desc')
                    if self.books[elementId].desc:
                        xmlBookDesc.text = self.books[elementId].desc
                elif childNode.startswith(self._SERIES_PREFIX):
                    xmlSeries = ET.SubElement(xmlNode, 'SERIES')
                    xmlSeries.set('ID', elementId)
                    xmlSeriesTitle = ET.SubElement(xmlSeries, 'Title')
                    if self.series[elementId].title:
                        xmlSeriesTitle.text = self.series[elementId].title
                    xmlSeriesDesc = ET.SubElement(xmlSeries, 'Desc')
                    if self.series[elementId].desc:
                        xmlSeriesDesc.text = self.series[elementId].desc

                    walk_tree(childNode, xmlSeries)

        xmlRoot = ET.Element('COLLECTION')
        walk_tree('', xmlRoot)

        indent(xmlRoot)
        xmlTree = ET.ElementTree(xmlRoot)
        try:
            xmlTree.write(self._filePath, encoding='utf-8')
        except(PermissionError):
            raise Error(f'"{self._filePath}" is write protected.')

        # Postprocess the xml file created by ElementTree
        self._postprocess_xml_file(self.filePath)
        return f'"{os.path.normpath(self.filePath)}" written.'

    def add_book(self, novel):
        """Add an existing yw7 file as book to the collection. 
        
        Return the book ID, if novel is added to the collection.
        Return None, if vovel is already a member.
        Raise the "Error" exception in case of error.
        """
        if os.path.isfile(novel.filePath):
            for bkId in self.books:
                if novel.filePath == self.books[bkId].filePath:
                    return None

            i = 1
            while str(i) in self.books:
                i += 1
            bkId = str(i)
            self.books[bkId] = Book(novel.filePath)
            self.books[bkId].pull_metadata(novel)
            return bkId

        else:
            raise Error(f'"{os.path.normpath(novel.filePath)}" not found.')

    def remove_book(self, bkId):
        """Remove a book from the collection and from the series.

        Return a message.
        Raise the "Error" exception in case of error.
        """
        bookTitle = bkId
        try:
            bookTitle = self.books[bkId].title
            del self.books[bkId]
            message = f'Book "{bookTitle}" removed from the collection.'
            for srId in self.srtSeries:
                try:
                    self.series[srId].remove_book(bkId)
                except Error:
                    pass
                else:
                    message = f'Book "{bookTitle}" removed from "{self.series[srId].title}" series.'

            return message
        except:
            raise Error(f'Cannot remove "{bookTitle}".')

    def add_series(self, seriesTitle):
        """Instantiate a Series object and append it to the srtSeries list.
        
        Avoid multiple entries.
        Return True on success, 
        return False, if the series is already a member.         
        """
        for srId in self.series:
            if self.series[srId].title == seriesTitle:
                return False

        srId = create_id(self.series)
        self.series[srId] = Series()
        self.series[srId].title = seriesTitle
        self.srtSeries.append(srId)
        return True

    def remove_series(self, seriesTitle):
        """Delete a Series object and remove it from the srtSeries list.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        for srId in self.srtSeries:
            if self.series[srId].title == seriesTitle:
                self.srtSeries.remove(srId)
                del(self.series[srId])
                return f'"{seriesTitle}" series removed from the collection.'

        raise Error(f'Cannot remove "{seriesTitle}" series from the collection.')

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

    def _reset_tree(self):
        """Clear the displayed tree."""
        for child in self.get_children(''):
            self.delete(child)

