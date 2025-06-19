# import mysql.connector
# import time
from db import fetchall, fetchone, execute
from datetime import datetime

class Book:
    def __init__(self, title, author, qty=1, book_id=None):
        self.id = book_id
        self.title = title.lower()
        self.author = author.lower()
        self.qty = qty
        self._available = qty > 0  

    def is_available(self):
        return self.qty > 0

    def __str__(self):
        return (f"Title: {self.title.title()}, "
                f"Author: {self.author.title()}, "
                f"Available: {self.is_available()} (Qty: {self.qty})")



class User:
    def __init__(self, name, user_id=None):
        self.name = name.lower()
        self.id = user_id

    def view_inventory(self, library):
        """View all books in the library."""
        library.view_inventory()



class Librarian(User):
    def __init__(self, name, user_id=None):
        super().__init__(name, user_id)

    #can add a book to the library's collection
    def add_book(self, library):
        library.add_book()

    #can remove book from the library's collection
    def remove_book(self, library):
        library.remove_book()

    


class Member(User):
    def __init__(self, name, user_id=None):
        super().__init__(name, user_id)
        self.borrowed_books = []

    #should return/print all the books the user currently has borrowed. limit should be 5. Later implement due dates.
    def view_books(self):
        """View all books this member currently has borrowed."""
        if not self.borrowed_books:
            print("You haven't borrowed any books yet.")
        else:
            print("You have borrowed the following books:")
            for bk in self.borrowed_books:
                print(bk)

    # checkout a book from the library if the user has borrowed less than 5 books. if the user has borrowed 5 books, print a message saying they have reached the limit.
    def checkout_book(self, library):
        if len(self.borrowed_books) == 5:
            print("Sorry, you have already borrowed the maximum limit of 5 books.")
        else:
            library.checkout_book(self)

    def return_book(self, library):
        library.return_book(self)

    def end_membership(self, library):
        library.end_membership(self)

class Library:
    def add_user(self):
        choice = input(
            "Enter the number corresponding to the type of user to create:\n"
            "1. Librarian\n"
            "2. Member\n"
            "3. Return to main menu\n> "
        )
        if choice not in {"1", "2"}:
            return
        name = input("Enter the full name: ").strip()
        user_type = "librarian" if choice == "1" else "member"
        execute("INSERT INTO users (name, user_type) VALUES (%s, %s)",
                (name.lower(), user_type))
        print(f"{user_type.title()} '{name}' added successfully.")

    def get_user(self, name:str):
        row = fetchone("SELECT * FROM users WHERE name=%s", (name.lower(),))
        if not row: return None
        if row["user_type"] == "member":
            return Member(row["name"], row["id"])
        return Librarian(row["name"], row["id"])

    def end_membership(self, member):
        execute("DELETE FROM users WHERE id=%s", (member.id,))
        print(f"Membership ended for '{member.name.title()}'.")


    def _upsert_book(self, title, author, delta):
        execute(
            """
            INSERT INTO books (title, author, qty)
            VALUES (%s,%s,%s)
            ON DUPLICATE KEY UPDATE qty = GREATEST(qty + VALUES(qty),0)
            """,
            (title, author, delta)
        )

    def add_book(self):
        title = input("Enter book title: ").lower()
        author = input("Enter author name: ").lower()
        self._upsert_book(title, author, 1)
        print(f"Added 1 copy of '{title.title()}' by {author.title()}.")

    def add_copies(self):
        title = input("Enter book title: ").lower()
        author = input("Enter author name: ").lower()
        try:
            qty_to_add = int(input("How many copies? "))
        except ValueError:
            print("Not a number."); return
        self._upsert_book(title, author, qty_to_add)
        print(f"Added {qty_to_add} copies of '{title.title()}'.")

    def remove_book(self):
        title = input("Enter book title to remove: ").lower()
        author = input("Enter author name: ").lower()
        try:
            qty_to_remove = int(input("How many copies? "))
        except ValueError:
            print("Not a number."); return
        self._upsert_book(title, author, -qty_to_remove)
        # clean up if qty hits 0
        execute("DELETE FROM books WHERE qty<=0")
        print(f"Removed {qty_to_remove} copies of '{title.title()}'.")


    def _make_book_objects(self, rows):
        return [Book(r["title"], r["author"], r["qty"], r["id"]) for r in rows]

    def view_inventory(self):
        rows = fetchall("SELECT * FROM books ORDER BY author,title")
        if not rows:
            print("No books in the library yet."); return
        print("Library Inventory:")
        for b in self._make_book_objects(rows):
            print("  ", b)

    def get_books_by_author(self):
        author = input("Author name: ").lower()
        rows = fetchall("SELECT * FROM books WHERE author=%s", (author,))
        if not rows:
            print(f"No books by '{author.title()}' found."); return
        for b in self._make_book_objects(rows):
            print(b)

    def _member_active_loans(self, member_id):
        return fetchall(
            "SELECT * FROM borrowed_books WHERE user_id=%s", (member_id,)
        )

    def checkout_book(self, member):
        if len(self._member_active_loans(member.id)) >= 5:
            print("You already have 5 books. Return one first."); return
        title  = input("Enter Book Title: ").lower()
        author = input("Enter Author Name: ").lower()

        book = fetchone(
            "SELECT * FROM books WHERE title=%s AND author=%s", (title,author)
        )
        if not book:
            print("Book not in catalog."); return
        if book["qty"] == 0:
            print("No available copies right now."); return

        execute("UPDATE books SET qty=qty-1 WHERE id=%s", (book["id"],))
        execute("INSERT INTO borrowed_books (user_id, book_id) VALUES (%s,%s)",
                (member.id, book["id"]))
        print(f"Checked out '{title.title()}' by {author.title()}.")

    def return_book(self, member):
        title  = input("Enter Book Title: ").lower()
        author = input("Enter Author Name: ").lower()

        book = fetchone(
            "SELECT * FROM books WHERE title=%s AND author=%s", (title,author)
        )
        if not book:
            print("Book not in catalog."); return
        loan = fetchone(
            "SELECT id FROM borrowed_books WHERE user_id=%s AND book_id=%s LIMIT 1",
            (member.id, book["id"])
        )
        if not loan:
            print("You did not borrow this book."); return

        execute("DELETE FROM borrowed_books WHERE id=%s", (loan["id"],))
        execute("UPDATE books SET qty=qty+1 WHERE id=%s", (book["id"],))
        print(f"Returned '{title.title()}' – thank you!")

    #sign in helper
    def user_lookup(self, name: str):
        return self.get_user(name)