import sqlite3 as sql

conn = sql.connect("library.db")
cursor = conn.cursor()

ITEMS_PER_PAGE = 5  

def main_menu():
    """Main menu interface for the library system with paginated options"""
    calculate_fines()
    page = 0  
    menu_pages = [
        [
            ("Find an item in the library", find_item),
            ("Borrow an item", borrow_item),
            ("Return a borrowed item", return_item),
            ("Donate an item to the library", donate_item),
            ("View your borrowed books", view_borrowed_books),
            ("Pay fines", pay_fines),
            ("Register for an account", register_account)
        ],
        [
            ("Find an event in the library", find_event),
            ("Register for an event", register_event),
            ("Volunteer for the library", volunteer),
            ("Ask for help from a librarian", ask_help)
        ]
    ]
    
    while True:
        print("\n===== Library System =====")
        print(f"=== Page {page+1} of {len(menu_pages)} ===")
        
        for i, (option_text, _) in enumerate(menu_pages[page], 1):
            print(f"{i}. {option_text}")
    
        print("\nNavigation:")
        if page < len(menu_pages)-1:
            print("[N]ext Page")
        if page > 0:
            print("[P]revious Page")
        print("[E]xit System")
        
        choice = input("\nSelect an option: ").strip().lower()
        
        if choice == 'n' and page < len(menu_pages)-1:
            page += 1
            continue
        elif choice == 'p' and page > 0:
            page -= 1
            continue
        elif choice == 'e':
            print("Exiting system. Goodbye!")
            break
        
        if choice.isdigit():
            option_num = int(choice) - 1
            if 0 <= option_num < len(menu_pages[page]):
                _, function = menu_pages[page][option_num]
                result = function()
                if result == 'main_menu':
                    continue
            else:
                print("Invalid option number.")
        else:
            print("Invalid choice. Please try again.")

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

        # Check for unpaid fines
    calculate_fines()
    cursor.execute("SELECT SUM(FineAmount) FROM BorrowingTransactions WHERE BorrowerID=? AND PaidStatus='Unpaid'", (borrower_id,))
    unpaid_fines = cursor.fetchone()[0] or 0
    
    if unpaid_fines > 0:
        print(f"\nCannot borrow items - you have ${unpaid_fines:.2f} in unpaid fines.")
        print("Please pay your fines first.")
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

def pay_fines():
    """Handles payment of fines for a borrower"""
    borrower_id = input("Enter your Borrower ID: ")
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?", (borrower_id,))
    if not cursor.fetchone():
        print("Invalid Borrower ID.")
        return

    # Calculate current fines
    calculate_fines()
    
    cursor.execute("""
        SELECT SUM(FineAmount) 
        FROM BorrowingTransactions 
        WHERE BorrowerID=? AND PaidStatus='Unpaid'
    """, (borrower_id,))
    
    total_fines = cursor.fetchone()[0] or 0
    
    if total_fines <= 0:
        print("\nYou have no outstanding fines.")
        return
    
    print(f"\nYour total outstanding fines: ${total_fines:.2f}")
    confirm = input("Would you like to pay all fines now? (Y/N): ").strip().lower()
    
    if confirm == 'y':
        cursor.execute("""
            UPDATE BorrowingTransactions 
            SET PaidStatus='Paid', FineAmount=0 
            WHERE BorrowerID=? AND PaidStatus='Unpaid'
        """, (borrower_id,))
        conn.commit()
        print("\nPayment successful! All fines have been cleared.")
    else:
        print("\nPayment cancelled.")

def view_borrowed_books():
    """Displays all books currently borrowed by a user"""
    borrower_id = input("Enter your Borrower ID: ")
    cursor.execute("SELECT * FROM Borrowers WHERE BorrowerID=?", (borrower_id,))
    if not cursor.fetchone():
        print("Invalid Borrower ID.")
        return

    cursor.execute("""
        SELECT li.ItemID, li.Title, li.AuthorCreator, bt.BorrowDate, bt.DueDate, bt.FineAmount
        FROM BorrowingTransactions bt
        JOIN LibraryCopy lc ON bt.CopyID = lc.CopyID
        JOIN LibraryItem li ON lc.ItemID = li.ItemID
        WHERE bt.BorrowerID = ? AND bt.ReturnDate IS NULL
    """, (borrower_id,))
    
    borrowed_books = cursor.fetchall()
    
    if not borrowed_books:
        print("\nYou have no books currently borrowed.")
        return
    
    columns = ["Item ID", "Title", "Author", "Borrow Date", "Due Date", "Fine Amount"]
    page = 0
    
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_page = borrowed_books[start:end]

        print("\n---------    Your Borrowed Books    ---------------")
        print(" | ".join([f"{col:<15}" for col in columns]))
        print("-" * (15 * len(columns) + 3 * (len(columns)-1)))

        for i, book in enumerate(current_page, start=1 + start):
            item_id, title, author, borrow_date, due_date, fine = book
            print(f"{i:<4} | {item_id:<15} | {title[:15]:<15} | "
                  f"{author[:15]:<15} | {borrow_date:<15} | ${fine:.2f}")

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu")
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "n" and end < len(borrowed_books):
            page += 1
        elif choice == "p" and page > 0:
            page -= 1
        elif choice == "m":
            return
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
    """Searches for library events with pagination and view all option"""
    while True:
        print("\n--- Find Library Events ---")
        print("1. List all upcoming events")
        print("2. Search events by name")
        print("3. View events by type")
        print("4. Return to main menu")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            cursor.execute("""
                SELECT EventID, EventName, EventType, 
                       strftime('%Y-%m-%d %H:%M', DateTime) as FormattedDate,
                       Location, Capacity - 
                       (SELECT COUNT(*) FROM EventRegistration er WHERE er.EventID = e.EventID) as RemainingSpots
                FROM Events e
                WHERE DateTime >= datetime('now')
                ORDER BY DateTime
            """)
            events = cursor.fetchall()
            
            if not events:
                print("\nNo upcoming events found.")
                continue
                
            columns = ["ID", "Event Name", "Type", "Date/Time", "Location", "Spots Left"]
            result = display_events_with_pagination(events, columns, "Upcoming Events")
            if result == 'main_menu':
                return 'main_menu'
                
        elif choice == '2':
            event_name = input("Enter event name (leave blank to cancel): ").strip()
            if not event_name:
                continue
                
            cursor.execute("""
                SELECT EventID, EventName, EventType, 
                       strftime('%Y-%m-%d %H:%M', DateTime) as FormattedDate,
                       Location, Capacity - 
                       (SELECT COUNT(*) FROM EventRegistration er WHERE er.EventID = e.EventID) as RemainingSpots
                FROM Events e
                WHERE EventName LIKE ? 
                AND DateTime >= datetime('now')
                ORDER BY DateTime
            """, (f"%{event_name}%",))
            
            events = cursor.fetchall()
            
            if not events:
                print("\nNo upcoming events found matching that name.")
                continue
                
            columns = ["ID", "Event Name", "Type", "Date/Time", "Location", "Spots Left"]
            result = display_events_with_pagination(events, columns, f"Events matching '{event_name}'")
            if result == 'main_menu':
                return 'main_menu'
                
        elif choice == '3':
            cursor.execute("SELECT DISTINCT EventType FROM Events WHERE EventType IS NOT NULL")
            event_types = cursor.fetchall()
            
            if not event_types:
                print("\nNo event categories available.")
                continue
                
            print("\nAvailable Event Types:")
            for i, (etype,) in enumerate(event_types, 1):
                print(f"{i}. {etype}")
                
            type_choice = input("Select event type number (or 0 to cancel): ").strip()
            if not type_choice.isdigit() or int(type_choice) < 1 or int(type_choice) > len(event_types):
                continue
                
            selected_type = event_types[int(type_choice)-1][0]
            
            cursor.execute("""
                SELECT EventID, EventName, EventType, 
                       strftime('%Y-%m-%d %H:%M', DateTime) as FormattedDate,
                       Location, Capacity - 
                       (SELECT COUNT(*) FROM EventRegistration er WHERE er.EventID = e.EventID) as RemainingSpots
                FROM Events e
                WHERE EventType = ? 
                AND DateTime >= datetime('now')
                ORDER BY DateTime
            """, (selected_type,))
            
            events = cursor.fetchall()
            
            if not events:
                print(f"\nNo upcoming {selected_type} events found.")
                continue
                
            columns = ["ID", "Event Name", "Type", "Date/Time", "Location", "Spots Left"]
            result = display_events_with_pagination(events, columns, f"{selected_type} Events")
            if result == 'main_menu':
                return 'main_menu'
                
        elif choice == '4':
            return
        else:
            print("Invalid choice. Please try again.")

def display_events_with_pagination(events, columns, title):
    """Displays events with pagination controls and selection options"""
    page = 0
    while True:
        start = page * ITEMS_PER_PAGE
        end = start + ITEMS_PER_PAGE
        current_events = events[start:end]

        print(f"\n---------    {title}    ---------------")
        print(f"{'No.':<4} " + " | ".join([f"{col:<15}" for col in columns]))
        print("-" * 60)

        for i, event in enumerate(current_events, start=1 + start):
            print(f"{i:<4} " + " | ".join([str(val)[:15].ljust(15) for val in event]))

        print("\nOptions: [N]ext Page | [P]revious Page | [M]ain Menu | [Select Number]")
        choice = input("\nChoose an option: ").strip().lower()

        if choice == "n" and end < len(events):
            page += 1
        elif choice == "p" and page > 0:
            page -= 1
        elif choice == "m":
            return 'main_menu'
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
    """Displays detailed information about a specific event"""
    event_id = event[0]
    cursor.execute("""
        SELECT e.*, 
               strftime('%Y-%m-%d %H:%M', e.DateTime) as FormattedDate,
               (SELECT COUNT(*) FROM EventRegistration er WHERE er.EventID = e.EventID) as RegisteredCount
        FROM Events e
        WHERE e.EventID = ?
    """, (event_id,))
    
    full_event = cursor.fetchone()
    columns = [desc[0] for desc in cursor.description]
    
    print("\n" + "="*60)
    print("EVENT DETAILS".center(60))
    print("="*60)

    display_fields = {
        'EventName': 'Event Name',
        'EventType': 'Type',
        'FormattedDate': 'Date/Time',
        'Location': 'Location',
        'RecommendedAudience': 'Recommended For',
        'RegisteredCount': 'Registered',
        'Capacity': 'Capacity'
    }
    
    for col in columns:
        if col in display_fields and full_event[columns.index(col)] is not None:
            print(f"{display_fields[col]:<20}: {full_event[columns.index(col)]}")
    
    remaining = full_event[columns.index('Capacity')] - full_event[columns.index('RegisteredCount')]
    print(f"{'Spots Available':<20}: {remaining}")
    print("="*60)

    print("\nOptions:")
    print("[R]egister for this event")
    print("[B]ack to event list")
    print("[M]ain menu")
    
    while True:
        choice = input("Choose an option: ").strip().lower()
        if choice == 'r':
            register_event(event_id)
            return
        elif choice == 'b':
            return
        elif choice == 'm':
            main_menu()
            return
        else:
            print("Invalid choice. Try again.")

def register_event(event_id=None):
    """Registers a borrower for a library event with capacity checking"""
    if event_id is None:
        event_id = input("Enter the Event ID you want to register for: ")
    cursor.execute("""
        SELECT e.Capacity, 
               (SELECT COUNT(*) FROM EventRegistration er WHERE er.EventID = e.EventID) as RegisteredCount
        FROM Events e
        WHERE e.EventID = ?
    """, (event_id,))
    
    event_data = cursor.fetchone()
    if not event_data:
        print("No event found with that ID.")
        return
    
    capacity, registered = event_data
    if registered >= capacity:
        print("This event is already at full capacity.")
        return
    
    borrower_id = input("Enter your Borrower ID: ")
    cursor.execute("""
        SELECT 1 FROM EventRegistration 
        WHERE EventID = ? AND BorrowerID = ?
    """, (event_id, borrower_id))
    
    if cursor.fetchone():
        print("You are already registered for this event.")
        return
    
    try:
        cursor.execute("""
            INSERT INTO EventRegistration (EventID, BorrowerID, RegistrationDate)
            VALUES (?, ?, datetime('now'))
        """, (event_id, borrower_id))
        conn.commit()
        
        print("\nRegistration successful!")
        print(f"Remaining spots: {capacity - registered - 1}")
    except sql.Error as e:
        print("Error registering for event:", e)

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
    SET FineAmount = (JULIANDAY('now') - JULIANDAY(DueDate)) * 0.50
    WHERE ReturnDate IS NULL 
    AND DueDate < DATE('now')
    AND PaidStatus = 'Unpaid'
    """)
    conn.commit()

if __name__ == "__main__":
    main_menu()

conn.close()