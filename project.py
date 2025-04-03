import sqlite3 as sql

conn = sql.connect("library.db")
cursor = conn.cursor()

ITEMS_PER_PAGE = 5  

def main_menu():
    """Main menu interface for the library system with all available options"""
    calculate_fines()
    while True:
        print("\nLibrary System")
        print("1. Find an item in the library")
        print("2. Borrow an item from the library")
        print("3. Return a borrowed item")
        print("4. Donate an item to the library")
        print("5. Find an event in the library")
        print("6. Register for an event")
        print("7. Volunteer for the library")
        print("8. Ask for help from a librarian")
        print("9. Register for an account")
        print("10. Exit")

        choice = input("\nSelect an option: ")
        if choice == '10':
            print("Exiting system. Goodbye!")
            break
        elif choice == '1':
            result = find_item()
            if result == 'main_menu':
                continue 
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
        elif choice=='9':
            register_account()
        else:
            print("Invalid choice. Try again.")

def find_item():
    """Provides options to list all items or search by title with pagination"""
    while True:
        print("\n--- Find Library Items ---")
        print("1. List all items")
        print("2. Search by title")
        print("3. Return to main menu")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            if list_all_items() == 'main_menu':
                return 'main_menu'
        elif choice == '2':
            if search_by_title() == 'main_menu':
                return 'main_menu'
        elif choice == '3':
            return
        else:
            print("Invalid choice. Please try again.")

def list_all_items():
    """Displays all library items with pagination"""
    cursor.execute("SELECT * FROM LibraryItem")
    items = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    
    if not items:
        print("\nNo items found in the library.")
        return
    
    result = display_items_with_pagination(items, columns, "All Library Items")
    if result == 'main_menu':
        return 'main_menu'

def search_by_title():
    """Searches for items by title with partial matching"""
    title = input("\nEnter title of the item (leave blank to return): ").strip()
    if not title:
        return
        
    cursor.execute("SELECT * FROM LibraryItem WHERE Title LIKE ?", (f"%{title}%",))
    items = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    if not items:
        print("\nNo items found matching that title.")
        return
    
    result = display_items_with_pagination(items, columns, f"Search Results for '{title}'")
    if result == 'main_menu':
        return 'main_menu'

def display_items_with_pagination(items, columns, title):
    """Displays items with pagination controls and selection options"""
    page = 0
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_items = items[start:end]

        print(f"\n---------    {title}    ---------------")
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
            return 'main_menu' 
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(items):
                view_book_details(items[index])
            else:
                print("Invalid selection.")
        else:
            print("Invalid choice. Try again.")

def view_book_details(item):
    """Displays detailed information about a specific library item"""
    columns = [desc[0] for desc in cursor.description]
    print("\n" + "="*50)
    print("ITEM DETAILS".center(50))
    print("="*50)
    
    for col, val in zip(columns, item):
        print(f"{col:<20}: {val}")
    
    item_id = item[0]
    cursor.execute("SELECT COUNT(*) FROM LibraryCopy WHERE ItemID=? AND Status='onShelf'", (item_id,))
    available_copies = cursor.fetchone()[0]
    
    print("\n" + "-"*50)
    print(f"Available copies: {available_copies}")
    print("-"*50)

    print("\nOptions:")
    print("[B]orrow this item")
    print("[R]eturn to list")
    print("[M]ain menu")
    
    while True:
        choice = input("Choose an option: ").strip().lower()
        if choice == 'b':
            cursor.execute("SELECT CopyID FROM LibraryCopy WHERE ItemID=? AND Status='onShelf' LIMIT 1", (item_id,))
            copy = cursor.fetchone()
            if copy:
                borrow_item(item_id=item_id, copy_id=copy[0])
            else:
                print("\nNo available copies to borrow.\n")
            return  
        elif choice == 'r':
            return
        elif choice == 'm':
            main_menu()
            return
        else:
            print("Invalid choice. Try again.")

def borrow_item(item_id=None, copy_id=None):
    """Handles the process of borrowing a library item"""
    borrower_id = input("\nEnter your Borrower ID: ")
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
    """Handles donations of new items to the library"""
    title = input("\nEnter title of the item: ")
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

    cursor.execute("INSERT INTO LibraryCopy (ItemID, Status) VALUES (?, 'onShelf')", (item_id,))
    conn.commit()

    print("A new copy has been added and is now available in the library!")

def return_item():
    """Handles returning borrowed items to the library"""
    borrower_id = input("Enter your Borrower ID: ")
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?", (borrower_id,))
    borrower = cursor.fetchone()
    
    if not borrower:
        print("Invalid Borrower ID.")
        return

    cursor.execute("""
        SELECT bt.TransactionID, li.ItemID, li.Title, li.AuthorCreator, bt.BorrowDate, bt.DueDate
        FROM BorrowingTransactions bt
        JOIN LibraryCopy lc ON bt.CopyID = lc.CopyID
        JOIN LibraryItem li ON lc.ItemID = li.ItemID
        WHERE bt.BorrowerID = ? AND bt.ReturnDate IS NULL
    """, (borrower_id,))
    
    borrowed_books = cursor.fetchall()
    
    if not borrowed_books:
        print("You have no books currently borrowed.")
        return
    
    columns = ["No.", "Transaction ID", "Item ID", "Title", "Author", "Borrow Date", "Due Date"]
    page = 0
    
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_page = borrowed_books[start:end]

        print("\n---------    Your Borrowed Items    ---------------")
        print(" | ".join([f"{col:<15}" for col in columns]))
        print("-" * (15 * len(columns) + 3 * (len(columns)-1)))

        for i, book in enumerate(current_page, start=1 + start):
            transaction_id, item_id, title, author, borrow_date, due_date = book
            print(f"{i:<15} | {transaction_id:<15} | {item_id:<15} | {title[:15]:<15} | "
                  f"{author[:15]:<15} | {borrow_date:<15} | {due_date:<15}")

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu | [Select Number]")
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "n" and end < len(borrowed_books):
            page += 1
        elif choice == "p" and page > 0:
            page -= 1
        elif choice == "m":
            return
        elif choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(borrowed_books):
                transaction_id = borrowed_books[index][0]
                cursor.execute("UPDATE BorrowingTransactions SET ReturnDate=DATE('now') WHERE TransactionID=?", (transaction_id,))
                calculate_fines()
                cursor.execute("UPDATE LibraryCopy SET Status='onShelf' WHERE CopyID=(SELECT CopyID FROM BorrowingTransactions WHERE TransactionID=?)", (transaction_id,))
                conn.commit()
                print("\nItem returned successfully!")
                return
            else:
                print("Invalid selection.")
        else:
            print("Invalid choice. Try again.")

def register_account():
    """Creates a new borrower account in the library system"""
    print("\n--- Register a New Library Account ---")

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
   
    try:
        cursor.execute("INSERT INTO Borrowers (Name, Email, PhoneNumber, Address) VALUES (?, ?, ?, ?)",
                       (name, email, phone, address))
        conn.commit()
        borrower_id = cursor.lastrowid
        print(f"\nAccount created successfully! Your Borrower ID is: {borrower_id}")
    except sql.Error as e:
        print("Error registering account:", e)

def find_event():
    """Searches for library events with pagination"""
    event_name = input("Enter the name of the event you're looking for: ")
    cursor.execute("SELECT * FROM Events WHERE EventName LIKE ?", (f"%{event_name}%",))
    events = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]

    if not events:
        print("\nNo events found with that name.")
        return

    page = 0
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_events = events[start:end]

        print("\n---------    Search Results    ---------------")
        print(f"{'No.':<4} " + " | ".join([f"{col:<15}" for col in columns]))
        print("-" * 50)

        for i, event in enumerate(current_events, start=start + 1):
            print(f"{i:<4} " + " | ".join([str(val)[:15].ljust(15) for val in event]))

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu | [Select Number]")
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "n":
            if end < len(events):
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
            if 0 <= index < len(events):
                selected_event = events[index]
                view_event_details(selected_event)
            else:
                print("Invalid selection.")
        else:
            print("Invalid choice. Try again.")

def view_event_details(event):
    """Displays detailed information about a specific event."""
    columns = [desc[0] for desc in cursor.description]
    print("\n" + "="*50)
    print("EVENT DETAILS".center(50))
    print("="*50)
    
    for col, val in zip(columns, event):
        print(f"{col:<20}: {val}")
    
    print("\nOptions:")
    print("[R]egister for this event")
    print("[B]ack to list")
    print("[M]ain menu")
    
    while True:
        choice = input("Choose an option: ").strip().lower()
        if choice == 'r':
            register_event(event[0]) 
            return
        elif choice == 'b':
            return
        elif choice == 'm':
            main_menu()
            return
        else:
            print("Invalid choice. Try again.")

def register_event(event_id=None):
    """Registers a borrower for a library event"""
    print("\n--- Register for an Event ---")
    borrower_id = input("Enter your Borrower ID: ")
    
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?", (borrower_id,))
    borrower = cursor.fetchone()
    if not borrower:
        print("Invalid Borrower ID. Please create an account first or recheck your ID.")
        return

    if not event_id:
        event_id = input("Enter the Event ID you want to register for: ")

    cursor.execute("SELECT * FROM Events WHERE EventID=?", (event_id,))
    event_row = cursor.fetchone()
    if not event_row:
        print("No event found with that ID.")
        return

    cursor.execute("SELECT * FROM EventRegistration WHERE EventID=? AND BorrowerID=?", (event_id, borrower_id))
    existing_registration = cursor.fetchone()
    if existing_registration:
        print("You are already registered for this event.")
        return

    try:
        cursor.execute("INSERT INTO EventRegistration (EventID, BorrowerID, RegistrationDate) VALUES (?, ?, DATE('now'))",
                       (event_id, borrower_id))
        conn.commit()
        registration_id = cursor.lastrowid
        print(f"Successfully registered for the event!")
        print(f"Your Event Registration ID is: {registration_id}")
    except sql.IntegrityError as e:
        print("Error registering for the event (duplicate or constraint issue).")

def volunteer():
    """Registers a new volunteer for the library"""
    print("\n--- Volunteer for the Library ---")
    name = input("Enter your Name: ")
    email = input("Enter your Email: ")
    phone = input("Enter your Phone Number: ")

    cursor.execute("SELECT * FROM Personnel WHERE Name=? AND Email=? AND Role='Volunteer'", (name, email))
    existing = cursor.fetchone()
    if existing:
        print("You are already a registered volunteer.")
        return

    try:
        cursor.execute("INSERT INTO Personnel (Name, Role, Email, PhoneNumber) VALUES (?,'Volunteer',?,?)",
                       (name, email, phone))
        conn.commit()
        staff_id = cursor.lastrowid
        print("Successfully registered as a volunteer!")
        print(f"Your Volunteer ID is: {staff_id}")
    except sql.IntegrityError as e:
        print("Error registering as a volunteer (duplicate or constraint issue).")

def ask_help():
    """Displays available librarians and their contact information"""
    print("\n--- Ask a Librarian for Help ---")
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

def calculate_fines():
    """Calculates and updates fines for overdue items."""
    cursor.execute("""
    UPDATE BorrowingTransactions 
    SET FineAmount = JULIANDAY('now') - JULIANDAY(DueDate) * 0.50
    WHERE ReturnDate IS NULL 
    AND DueDate < DATE('now')
    AND PaidStatus = 'Unpaid'
    """)
conn.commit()

if __name__ == "__main__":
    main_menu()

conn.close()