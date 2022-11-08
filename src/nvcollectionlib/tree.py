

class Node:

    def __init__(self, label):
        self.label = label
        self.children = {}

    def append(self, label):
        if not label in self.children:
            self.children[label] = Node(label)

    def get_children(self, item):
        if item == self.label:
            return tuple(self.children)
        else:
            for child in self.children:
                result = child.get_children(item)
                if result is not None:
                    return result


class Tree:
    """A hierarchical collection of items.

    Each item has a textual label
    """
    self.root = Node('')

    def get_children(self, item=None):
        """Returns a tuple of children belonging to item.

        If item is not specified, returns root children."""
        if item is None:
            label = ''
        return self.root.get_children(label)

    def delete(self, *items):
        """Delete all specified items and all their descendants. The root
        item may not be deleted."""

    def exists(self, item):
        """Returns True if the specified item is present in the tree,
        False otherwise."""

    def index(self, item):
        """Returns the integer index of item within its parent's list
        of children."""

    def insert(self, parent, index, iid=None, **kw):
        """Creates a new item and return the item identifier of the newly
        created item.

        parent is the item ID of the parent item, or the empty string
        to create a new top-level item. index is an integer, or the value
        end, specifying where in the list of parent's children to insert
        the new item. If index is less than or equal to zero, the new node
        is inserted at the beginning, if index is greater than or equal to
        the current number of children, it is inserted at the end. If iid
        is specified, it is used as the item identifier, iid must not
        already exist in the tree. Otherwise, a new unique identifier
        is generated."""

    def next(self, item):
        """Returns the identifier of item's next sibling, or '' if item
        is the last child of its parent."""

    def parent(self, item):
        """Returns the ID of the parent of item, or '' if item is at the
        top level of the hierarchy."""

    def prev(self, item):
        """Returns the identifier of item's previous sibling, or '' if
        item is the first child of its parent."""
        return self.tk.call(self._w, "prev", item)

