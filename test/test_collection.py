"""Integration tests for the pyWriter project.

Test the Use Cases "manage the collection".

For further information see https://github.com/peter88213/PyWriter
License: GNU GPLv3 (https://www.gnu.org/licenses/gpl-3.0.en.html)
"""

import os
import unittest
from shutil import copyfile
from shutil import rmtree
from tkinter import ttk

from nvcollectionlib.collection import Collection
from pywriter.yw.yw7_file import Yw7File

DATA_PATH = '../data'
TEST_FILE = 'collection.pwc'

os.chdir('yw7')


def read_file(inputFile):
    with open(inputFile, 'r', encoding='utf-8') as f:
        return(f.read())


def remove_all_testfiles():
    try:
        os.remove(TEST_FILE)
        rmtree('yWriter Projects')
    except:
        pass


class NrmOpr(unittest.TestCase):
    """Test case: Normal operation
    """

    def tearDown(self):
        remove_all_testfiles()

    def setUp(self):
        remove_all_testfiles()
        try:
            os.mkdir('yWriter Projects')
        except:
            pass
        try:
            os.mkdir('yWriter Projects/The Gravity Monster.yw')
        except:
            pass
        copyfile(DATA_PATH + '/yWriter Projects/The Gravity Monster.yw/The Gravity Monster.yw7',
                 'yWriter Projects/The Gravity Monster.yw/The Gravity Monster.yw7')
        try:
            os.mkdir('yWriter Projects/The Refugee Ship.yw')
        except:
            pass

        copyfile(DATA_PATH + '/yWriter Projects/The Refugee Ship.yw/The Refugee Ship.yw7',
                 'yWriter Projects/The Refugee Ship.yw/The Refugee Ship.yw7')

    def test_read_write_configuration(self):
        """Read and write the configuration file. """
        copyfile(DATA_PATH + '/_collection/read_write.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '2 Books found in "' + TEST_FILE + '".')
        os.remove(TEST_FILE)
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/read_write.xml'))

    def test_create_collection(self):
        """Use Case: manage the collection/create the collection."""
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/create_collection.xml'))

    def test_add_book(self):
        """Use Case: manage the collection/add a book to the collection."""
        copyfile(DATA_PATH + '/_collection/create_collection.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '0 Books found in "' + TEST_FILE + '".')
        novel = Yw7File('yWriter Projects/The Gravity Monster.yw/The Gravity Monster.yw7')
        novel.read()
        self.assertEqual(myCollection.add_book(novel),
            '1')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/add_first_book.xml'))
        novel = Yw7File('yWriter Projects/The Refugee Ship.yw/The Refugee Ship.yw7')
        novel.read()
        self.assertEqual(myCollection.add_book(novel),
            '2')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/add_second_book.xml'))

    def test_remove_book(self):
        """Use Case: manage the collection/remove a book from the collection."""
        copyfile(DATA_PATH + '/_collection/add_second_book.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '2 Books found in "' + TEST_FILE + '".')
        myCollection.remove_book('bk1')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/remove_book.xml'))
        myCollection.remove_book('bk2')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/create_collection.xml'))

    def test_create_series(self):
        """Use Case: manage book series/create a series."""
        copyfile(DATA_PATH + '/_collection/add_first_book.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '1 Books found in "' + TEST_FILE + '".')
        myCollection.add_series('Rick Starlift')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/empty_series.xml'))

    def test_remove_series(self):
        """Use Case: manage book series/remove a series."""
        copyfile(DATA_PATH + '/_collection/empty_series.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '1 Books found in "' + TEST_FILE + '".')
        myCollection.remove_series('sr1')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/add_first_book.xml'))

    def test_add_book_to_series(self):
        """Use Case: manage book series/add a book to a series."""
        copyfile(DATA_PATH + '/_collection/empty_series.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '1 Books found in "' + TEST_FILE + '".')
        myCollection.tree.move('bk1', 'sr1', 'end')
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/add_book_to_series.xml'))

    def test_remove_book_from_series(self):
        """Use Case: manage book series/remove a book from a series."""
        copyfile(DATA_PATH + '/_collection/add_book_to_series.xml', TEST_FILE)
        myCollection = Collection(TEST_FILE, ttk.Treeview())
        self.assertEqual(myCollection.read(),
                         '1 Books found in "' + TEST_FILE + '".')
        myCollection.tree.move('bk1', '', 0)
        self.assertEqual(myCollection.write(),
                         '"' + TEST_FILE + '" written.')
        self.assertEqual(read_file(TEST_FILE),
                         read_file(DATA_PATH + '/_collection/empty_series.xml'))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
