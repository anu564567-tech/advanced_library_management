"""
Add admin_notes column to book_requests table
"""

import sqlite3
import os

def add_admin_notes_column():
    """Add admin_notes column to existing book_requests table"""
    db_path = 'library.db'
    
    if not os.path.exists(db_path):
        print("Database not found. Please run the application first to create the database.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if admin_notes column already exists
        cursor.execute("PRAGMA table_info(book_requests)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'admin_notes' in columns:
            print("admin_notes column already exists in book_requests table")
            return True
        
        # Add admin_notes column
        cursor.execute('''
            ALTER TABLE book_requests 
            ADD COLUMN admin_notes TEXT
        ''')
        
        conn.commit()
        print("Successfully added admin_notes column to book_requests table")
        return True
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    add_admin_notes_column()
