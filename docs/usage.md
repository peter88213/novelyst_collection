[Project homepage](https://peter88213.github.io/novelyst_collection)

--- 

A [novelyst](https://peter88213.github.io/novelyst/) plugin providing a book/series collection manager. 

---

# Installation

If [novelyst](https://peter88213.github.io/novelyst/) is installed, the setup script auto-installs the *novelyst_collection* plugin in the *novelyst* plugin directory.

The plugin adds a **Collection** entry to the *novelyst* **File** menu, and an **Editor plugin Online Help** entry to the **Help** menu. 

---

# Operation

---

## Launch the program

- Open the collection manager from the main menu: **File > Collection**.

---

## Open a collection

- By default, the latest collection selected is preset. You can change it with **File > Open**.

---

## Create a new collection

- You can create a new collection with **File > New**. This will close the current collection
  and open a file dialog asking for the location and file name of the collection to create.
- Once you specified a valid file path, a blank collection appears.

---

## Create a new series

- You can add a new series with **Series > Add**. Edit the series' title and description in the right window.

---

## Add books to the collection

- You can add the current novelyst project as a book to the collection. Use **Book > Add current project to collection**.
- If a series is selected, the book is added as a part of this series.

---

## Update book description

- You can update the book description from the current project. Use **Book > Update book data from current project**. 
  Be sure not to change the book title, because it is used as identifier. 

---

## Remove books from the collection

- You can remove the selected book from the collection. Use **Book > Remove selected book from the collection**.

---

## Move series and books

Drag and drop while pressing the **Alt** key. Be aware, there is no "Undo" feature. 

---

## Remove books

Either select item and hit the **Del** key, or use **Book > Remove selected book from the collection**.

- When removing a book from the collection, the project file associated is kept on disc. 

---

## Delete a series

Either select series and hit the **Del** key, or use **Series > Remove selected series but keep the books**.

- When deleting a collection, the books are kept by default.
- Use **Series > Remove selected series** to delete the selected series and remove all its books from the collection. 

---

## Exit

- You can exit via **File > Exit**, or with **Ctrl-Q**.
- When exiting the program, you will be asked for applying changes.


---

# License

This is Open Source software, and the *novelyst_collection* plugin is licensed under GPLv3. See the
[GNU General Public License website](https://www.gnu.org/licenses/gpl-3.0.en.html) for more
details, or consult the [LICENSE](https://github.com/peter88213/novelyst_collection/blob/main/LICENSE) file.
