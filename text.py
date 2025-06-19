import time
from main import *
from sqlalchemy import create_engine, text
import mysql.connector
import pandas as pd



welcome_art = r"""      __...--~~~~~-._   _.-~~~~~--...__
    //               `V'               \\ 
   //                 |                 \\ 
  //__...--~~~~~~-._  |  _.-~~~~~~--...__\\ 
 //__.....----~~~~._\ | /_.~~~~----.....__\\
====================\\|//====================
                    `---`"""

welcome_menu = """Hello, welcome to the Public Library!
Select the option that describes you best:
1. Sign up (Create a new user)
2. Sign in (Log in as an existing user)
3. Exit
"""


def slow_print(text, speed=45):
    for letter in text:
        time.sleep(1/speed)
        print(letter,end="", flush=True)

def main():
    
    library = Library()
    
    print(welcome_art)  # Print the ASCII art slower if you like
    while True:
        slow_print(welcome_menu, speed=50)
        choice = input("> ").strip()
        if choice == "1":
            library.add_user()
        elif choice == "2":
            sign_in(library)
        elif choice == "3":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

def sign_in(library):
    """
    Prompts for a user's name. If found in library.users, we check what type of user it is
    and direct to the appropriate menu (member or librarian).
    """
    name = input("Enter your full name: ").lower()
    user = library.users.get(name)

    if user is None:
        print(f"No user named '{name.title()}' found in the system. Please sign up first.")
        return

    if isinstance(user, Member):
        member_menu(library, user)
    elif isinstance(user, Librarian):
        librarian_menu(library, user)
    else:
        print("Unknown user type. Cannot proceed.")

def member_menu(library, member):
    """
    Presents a menu of possible actions for a Member.
    """
    print(f"\nWelcome, {member.name.title()} (Member)!")
    while True:
        choice = input(
            "\nChoose an option:\n"
            "1. View Library Inventory\n"
            "2. Checkout Book\n"
            "3. Return Book\n"
            "4. View My Borrowed Books\n"
            "5. End Membership\n"
            "6. Log Out\n> "
        ).strip()

        if choice == "1":
            library.view_inventory()
        elif choice == "2":
            member.checkout_book(library)
        elif choice == "3":
            member.return_book(library)
        elif choice == "4":
            member.view_books()
        elif choice == "5":
            member.end_membership(library)
            break
        elif choice == "6":
            # Log out (back to main menu)
            break
        else:
            print("Invalid choice. Try again.")

def librarian_menu(library, librarian):
    """
    Presents a menu of possible actions for a Librarian.
    """
    print(f"\nWelcome, {librarian.name.title()} (Librarian)!")
    while True:
        choice = input(
            "\nChoose an option:\n"
            "1. Add Book\n"
            "2. Remove Book\n"
            "3. View Library Inventory\n"
            "4. Add Copies of Existing Book\n"
            "5. Get Books by Author\n"
            "6. Log Out\n> "
        ).strip()

        if choice == "1":
            librarian.add_book(library)
        elif choice == "2":
            librarian.remove_book(library)
        elif choice == "3":
            library.view_inventory()
        elif choice == "4":
            library.add_copies()
        elif choice == "5":
            library.get_books_by_author()
        elif choice == "6":
            # Log out (back to main menu)
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()