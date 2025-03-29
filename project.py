import sqlite3 as sql

conn = sql.connect("library.db")
cursor = conn.cursor()

ITEMS_PER_PAGE = 5  

def main_menu():
    while True:
        print("Library System")
        print("1. Find an item in the library")
        print("2. Borrow an item from the library")
        print("3. Return a borrowed item")
        print("4. Donate an item to the library")
        print("5. Find an event in the library")
        print("6. Register for an event")
        print("7. Volunteer for the library")
        print("8. Ask for help from a librarian")
        print("9. Exit")
        
        choice = input("Select an option: ")
        if choice == '9':
            print("Exiting system. Goodbye!")
            break
        elif choice == '1':
            find_item()
        elif choice == '2':
            borrow_item()
        elif choice == '3':
            return_item()
        elif choice == '4':
            donate_item()
        elif choice == '5':
            find_event()
        elif choice == '6':
            register_event()
        elif choice == '7':
            volunteer()
        elif choice == '8':
            ask_help()
        else:
            print("Invalid choice. Try again.")

def find_item():
    title = input("Enter title of the item: ")
    cursor.execute("SELECT * FROM LibraryItem WHERE Title LIKE ?", (f"%{title}%",))
    items = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    if not items:
        print("\nItem not found.")
        return
    
    page = 0
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_items = items[start:end]

        print("---------    Search Results    ---------------")
        print(f"{'No.':<4} " + " | ".join([f"{col:<15}" for col in columns]))
        print("-" * 40)

        for i, item in enumerate(current_items, start=1 + start):
            print(f"{i:<4} " + " | ".join([str(val)[:15].ljust(15) for val in item]))

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu | [Select Number]")
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "n" and end < len(items):
            page += 1
        elif choice == "p" and page > 0:
            page -= 1
        elif choice == "m":
            return
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(items):
                view_book_details(items[index])
            else:
                print("Invalid selection.")
        else:
            print("Invalid choice. Try again.")



def borrow_item(item_id=None, copy_id=None):
    borrower_id = input("Enter your Borrower ID: ")
    
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?", (borrower_id,))
    borrower = cursor.fetchone()
    if not borrower:
        print("Invalid Borrower ID.")
        return
    
    if not item_id:
        item_id = input("Enter the Item ID you want to borrow: ")
        cursor.execute("SELECT CopyID FROM LibraryCopy WHERE ItemID=? AND Status='onShelf'", (item_id,))
        copy = cursor.fetchone()
        if not copy:
            print("No available copies.")
            return
        copy_id = copy[0]

    cursor.execute(
        "INSERT INTO BorrowingTransactions (BorrowerID, CopyID, BorrowDate, DueDate, ReturnDate, FineAmount, PaidStatus) "
        "VALUES (?, ?, DATE('now'), DATE('now', '+14 days'), NULL, 0, 'Unpaid')",
        (borrower_id, copy_id)
    )
    
    cursor.execute("UPDATE LibraryCopy SET Status='Borrow' WHERE CopyID=?", (copy_id,))
    conn.commit()
    
    print("\nItem borrowed successfully! Due in 14 days.")


def donate_item():
    title = input("Enter title of the item: ")
    item_type = input("Enter item type: ")
    author = input("Enter author/creator: ")
    year = input("Enter year published: ")

    cursor.execute("SELECT ItemID FROM LibraryItem WHERE Title=? AND AuthorCreator=?", (title, author))
    item = cursor.fetchone()

    if item:
        item_id = item[0]
        print("\nThis item already exists in the library catalog. Adding a new copy...")
    else:
        cursor.execute("INSERT INTO LibraryItem (Title, ItemType, AuthorCreator, YearPublished) VALUES (?, ?, ?, ?)",
                       (title, item_type, author, year))
        item_id = cursor.lastrowid
        print("\nNew item added to the library catalog!")

    # Add a physical copy to the library
    cursor.execute("INSERT INTO LibraryCopy (ItemID, Status) VALUES (?, 'onShelf')", (item_id,))
    conn.commit()

    print("A new copy has been added and is now available in the library!")



if __name__ == "__main__":
    main_menu()

conn.close()
