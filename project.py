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
        print("10. Register for an account")
        
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
        elif choice=='10':
            register_account()
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
    transaction_id = cursor.lastrowid
    
    cursor.execute("UPDATE LibraryCopy SET Status='Borrow' WHERE CopyID=?", (copy_id,))
    conn.commit()
    
    print("\nItem borrowed successfully! Due in 14 days.")
    print(f"Your Transaction ID is: {transaction_id}")



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

def return_item():
    borrower_id = input("Enter your Borrower ID: ")
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?",(borrower_id,))
    borrower=cursor.fetchone()
    if not borrower:
        print("Invalid Borrower ID.")
        return
    transaction_id=input("Enter the Transaction ID you want to return:")
    cursor.execute("""
        SELECT TransactionID,DueDate,ReturnDate,CopyID
        FROM BorrowingTransactions
        WHERE TransactionID=? AND BorrowerID=?
    """, (transaction_id, borrower_id))
    transaction=cursor.fetchone()
    if not transaction:
        print("No matching transaction found.")
        return
    db_transaction_id, db_due_date, db_return_date, db_copy_id = transaction

    if db_return_date:
        print("This item was already returned.")
        return
    
    cursor.execute("""
        UPDATE BorrowingTransactions
        SET ReturnDate=DATE('now')
        WHERE TransactionID=?""", (db_transaction_id,))
    
    cursor.execute("""
        UPDATE LibraryCopy
        SET Status='onShelf'
        WHERE CopyID=?""", (db_copy_id,)) 
    conn.commit()
    print("Return process complete! The item is now marked as returned.\n")

def register_account():
    print("\n--- Register a New Library Account ---")

    # Keep prompting until a valid (non-empty) name is entered
    while True:
        name = input("Enter your Name: ").strip()
        if name:
            break
        print("Name cannot be empty. Please try again.")

    while True:
        email = input("Enter your Email: ").strip()
        if email:
            break
        print("Email cannot be empty. Please try again.")


    phone = input("Enter your Phone Number: ").strip()
    address = input("Enter your Address: ").strip()
   

    # Insert into the database
    try:
        cursor.execute(
            """
            INSERT INTO Borrowers (Name, Email, PhoneNumber, Address)
            VALUES (?, ?, ?, ?)
            """,
            (name, email, phone, address)
        )
        conn.commit()
        borrower_id = cursor.lastrowid
        print(f"\nAccount created successfully! Your Borrower ID is: {borrower_id}")
    except sql.Error as e:
        print("Error registering account:", e)


def find_event():
    event_name = input("Enter the name of the event you're looking for: ")
    
    # 1) Query the Events table by partial match
    cursor.execute("SELECT * FROM Events WHERE EventName LIKE ?", (f"%{event_name}%",))
    events = cursor.fetchall()
    
    # 2) Column headers, if you want to display them
    columns = [desc[0] for desc in cursor.description]

    if not events:
        print("\nNo events found with that name.")
        return

    # 3) Paginate the results
    page = 0
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_events = events[start:end]

        print("\n---------    Search Results    ---------------")
        print(f"{'No.':<4} " + " | ".join([f"{col:<15}" for col in columns]))
        print("-" * 50)

        for i, event in enumerate(current_events, start=start + 1):
            # Show each row truncated to 15 chars
            print(f"{i:<4} " + " | ".join([str(val)[:15].ljust(15) for val in event]))

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu | [Select Number]")
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "n":
            # Go to next page if possible
            if end < len(events):
                page += 1
            else:
                print("Already on the last page.")
        elif choice == "p":
            # Go to previous page if possible
            if page > 0:
                page -= 1
            else:
                print("Already on the first page.")
        elif choice == "m":
            # Return to main menu
            return
        elif choice.isdigit():
            # User selected a specific event by index
            index = int(choice) - 1
            if 0 <= index < len(events):
                selected_event = events[index]
                view_event_details(selected_event)
            else:
                print("Invalid selection.")
        else:
            print("Invalid choice. Try again.")

    
def register_event(event_id=None):
    """
    Registers a borrower for an event in the Events table
    by adding a row to the EventRegistration table.
    """
    print("\n--- Register for an Event ---")
    
    # 1) Prompt for Borrower ID
    borrower_id = input("Enter your Borrower ID: ")
    
    # Confirm borrower exists
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?", (borrower_id,))
    borrower = cursor.fetchone()
    if not borrower:
        print("Invalid Borrower ID. Please create an account first or recheck your ID.")
        return

    # 2) Prompt for Event ID if not provided
    if not event_id:
        event_id = input("Enter the Event ID you want to register for: ")

    # Check if the event exists
    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event_row = cursor.fetchone()
    if not event_row:
        print("No event found with that ID.")
        return

    # 3) Check if already registered (optional check for user-friendly message)
    cursor.execute("""
        SELECT *
        FROM EventRegistration
        WHERE EventID=? AND BorrowerID=?
    """, (event_id, borrower_id))
    existing_registration = cursor.fetchone()
    if existing_registration:
        print("You are already registered for this event.")
        return

    # 4) Insert new row into EventRegistration
    try:
        cursor.execute("""
            INSERT INTO EventRegistration (EventID, BorrowerID, RegistrationDate)
            VALUES (?, ?, DATE('now'))
        """, (event_id, borrower_id))
        conn.commit()

        registration_id = cursor.lastrowid
        print(f"Successfully registered for the event!")
        print(f"Your Event Registration ID is: {registration_id}")

    except sql.IntegrityError as e:
        # This handles any UNIQUE constraint errors, etc.
        print("Error registering for the event (duplicate or constraint issue).")
        print("Details:", e)
def volunteer():
    print("\n--- Volunteer for the Library ---")

    name=input("Enter your Name: ")
    email=input("Enter your Email: ")
    phone=input("Enter your Phone Number: ")

    cursor.execute(
        """
        SELECT * FROM Personnel
        WHERE Name=? AND Email=? AND Role='Volunteer'
        """,(name,email)
    )
    existing=cursor.fetchone()
    if existing:
        print("You are already a registered volunteer.")
        return

    try:
        cursor.execute("""
            INSERT INTO Personnel (Name,Role,Email,PhoneNumber)
            VALUES (?,'Volunteer',?,?)
        """, (name,email,phone))
        conn.commit()

        staff_id=cursor.lastrowid
        print("Successfully registered as a volunteer!")
        print(f"Your Volunteer ID is: {staff_id}")
    except sql.IntegrityError as e:
        print("Error registering as a volunteer (duplicate or constraint issue).")
        
def ask_help():
    print("\n--- Ask a Librarian for Help ---")

    # Search for all personnel with 'Librarian' in their role
    cursor.execute("SELECT * FROM Personnel WHERE Role LIKE '%Librarian%'")
    librarians = cursor.fetchall()

    if not librarians:
        print("No librarians found.")
        return

    columns = [desc[0] for desc in cursor.description]
    page = 0

    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current = librarians[start:end]

        print("\n--------- Available Librarians ---------")
        print(f"{'No.':<4} " + " | ".join([f"{col:<15}" for col in columns]))
        print("-" * 60)

        for i, librarian in enumerate(current, start=start + 1):
            print(f"{i:<4} " + " | ".join([str(val)[:15].ljust(15) for val in librarian]))

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu | [Select Number]")
        choice = input("Choose an option: ").strip().lower()

        if choice == "n":
            if end < len(librarians):
                page += 1
            else:
                print("Already on the last page.")
        elif choice == "p":
            if page > 0:
                page -= 1
            else:
                print("Already on the first page.")
        elif choice == "m":
            return
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(librarians):
                librarian = librarians[index]
                print("\n--- Librarian Contact Info ---")
                print(f"Name:         {librarian[1]}")
                print(f"Email:        {librarian[3]}")
                print(f"Phone Number: {librarian[4]}\n")
                input("Press Enter to return to the librarian list...")
            else:
                print("Invalid selection.")
        else:
            print("Invalid choice. Try again.")

        
        


if __name__ == "__main__":
    main_menu()

conn.close()
