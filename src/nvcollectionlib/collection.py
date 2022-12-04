"""Provide a class representing a collection of yWriter projects.

Copyright (c) 2022 Peter Triesberger
For further information see https://github.com/peter88213/novelyst_collection
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""
import os
import re
from html import unescape
import xml.etree.ElementTree as ET
import tkinter.font as tkFont

from nvcollectionlib.nvcollection_globals import *
from pywriter.yw.xml_indent import indent
from pywriter.model.id_generator import create_id

from nvcollectionlib.series import Series
from nvcollectionlib.book import Book


class Collection:
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

    def __init__(self, filePath, tree):
        """Initialize the instance variables.
        
        Positional arguments:
            filePath -- str: path to xml file.
            tree -- tree structure of series and book IDs.
        """
        self.title = None
        self.tree = tree
        fontSize = tkFont.nametofont('TkDefaultFont').actual()['size']
        self.tree.tag_configure('series', font=('', fontSize, 'bold'))

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
            self.title, __ = os.path.splitext(os.path.basename(self.filePath))

    def read(self):
        """Parse the pwc XML file located at filePath, fetching the Collection attributes.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """

        def get_book(parent, xmlBook):
            try:
                bkId = xmlBook.attrib['ID']
                item = f'{self._BOOK_PREFIX}{bkId}'
                bookPath = xmlBook.find('Path').text
                if os.path.isfile(bookPath):
                    self.books[bkId] = Book(bookPath)
                    if xmlBook.find('Title') is not None:
                        self.books[bkId].title = xmlBook.find('Title').text
                    else:
                        self.books[bkId].title = item
                    if xmlBook.find('Desc') is not None:
                        self.books[bkId].desc = xmlBook.find('Desc').text
            except:
                pass
            else:
                self.tree.insert(parent, 'end', item, text=self.books[bkId].title, open=True)

        # Open the file and let ElementTree parse its xml structure.
        try:
            xmlTree = ET.parse(self.filePath)
            xmlRoot = xmlTree.getroot()
        except:
            raise Error(f'Can not process "{norm_path(self.filePath)}".')

        self.reset_tree()
        self.books = {}
        self.series = {}
        for xmlElement in xmlRoot:
            if xmlElement.tag == 'BOOK':
                get_book('', xmlElement)
            elif xmlElement.tag == 'SERIES':
                srId = xmlElement.attrib['ID']
                item = f'{self._SERIES_PREFIX}{srId}'
                self.series[srId] = Series()
                if xmlElement.find('Title') is not None:
                    self.series[srId].title = xmlElement.find('Title').text
                else:
                    self.series[srId].title = item
                if xmlElement.find('Desc') is not None:
                    self.series[srId].desc = xmlElement.find('Desc').text
                self.tree.insert('', 'end', item, text=self.series[srId].title, tags='series', open=True)
                for xmlBook in xmlElement.iter('BOOK'):
                    get_book(item, xmlBook)

        return f'{len(self.books)} Books found in "{norm_path(self.filePath)}".'

    def write(self):
        """Write the collection's attributes to a pwc XML file located at filePath. 
        
        Overwrite existing file without confirmation.
        Return a message.
        Raise the "Error" exception in case of error.
        """

        def walk_tree(node, xmlNode):
            """Transform the Treeview nodes to XML Elementtree nodes."""
            for childNode in self.tree.get_children(node):
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
        backedUp = False
        if os.path.isfile(self.filePath):
            try:
                os.replace(self.filePath, f'{self.filePath}.bak')
            except:
                raise Error(f'{_("Cannot overwrite file")}: "{norm_path(self.filePath)}".')
            else:
                backedUp = True
            try:
                xmlTree.write(self.filePath, encoding='utf-8')

                # Postprocess the xml file created by ElementTree
                self._postprocess_xml_file(self.filePath)
            except:
                if backedUp:
                    os.replace(f'{self.filePath}.bak', self.filePath)
                raise Error(f'{_("Cannot write file")}: "{norm_path(self.filePath)}".')

            return f'"{norm_path(self.filePath)}" written.'

    def add_book(self, book, parent='', index='end'):
        """Add an existing project file as book to the collection. 
        
        Return the book ID, if book is added to the collection.
        Return None, if vovel is already a member.
        Raise the "Error" exception in case of error.
        """
        if os.path.isfile(book.filePath):
            for bkId in self.books:
                if book.filePath == self.books[bkId].filePath:
                    return None

            bkId = create_id(self.books)
            self.books[bkId] = Book(book.filePath)
            self.books[bkId].pull_metadata(book.novel)
            self.tree.insert(parent, index, f'{self._BOOK_PREFIX}{bkId}', text=self.books[bkId].title, open=True)
            return bkId

        else:
            raise Error(f'"{norm_path(book.filePath)}" not found.')

    def remove_book(self, nodeId):
        """Remove a book from the collection.

        Return a message.
        Raise the "Error" exception in case of error.
        """
        bkId = nodeId[2:]
        bookTitle = nodeId
        try:
            bookTitle = self.books[bkId].title
            del self.books[bkId]
            self.tree.delete(nodeId)
            message = f'Book "{bookTitle}" removed from the collection.'
            return message
        except:
            raise Error(f'Cannot remove "{bookTitle}".')

    def add_series(self, seriesTitle, index='end'):
        """Instantiate a Series object.
        """
        srId = create_id(self.series)
        self.series[srId] = Series()
        self.series[srId].title = seriesTitle
        self.tree.insert('', index, f'{self._SERIES_PREFIX}{srId}', text=self.series[srId].title, tags='series', open=True)

    def remove_series(self, nodeId):
        """Delete a Series object but keep the books.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        srId = nodeId[2:]
        seriesTitle = self.series[srId].title
        for bookNode in self.tree.get_children(nodeId):
            self.tree.move(bookNode, '', 'end')
        del(self.series[srId])
        self.tree.delete(nodeId)
        return f'"{seriesTitle}" series removed from the collection.'

        raise Error(f'Cannot remove "{seriesTitle}" series from the collection.')

    def remove_series_with_books(self, nodeId):
        """Delete a Series object with all its members.
        
        Return a message.
        Raise the "Error" exception in case of error.
        """
        srId = nodeId[2:]
        seriesTitle = self.series[srId].title
        for bookNode in self.tree.get_children(nodeId):
            bkId = bookNode[2:]
            del self.books[bkId]
        del(self.series[srId])
        self.tree.delete(nodeId)
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
            raise Error(f'{_("Cannot write file")}: "{norm_path(filePath)}".')

    def reset_tree(self):
        """Clear the displayed tree."""
        for child in self.tree.get_children(''):
            self.tree.delete(child)

