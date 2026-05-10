"""
Database Migration Script
Add notification fields to users table
"""

import sqlite3
import os

def update_database():
    """Add notification fields to existing database"""
    db_path = 'library.db'
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add email_notifications column if it doesn't exist
        if 'email_notifications' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN email_notifications BOOLEAN DEFAULT 1")
            print("Added email_notifications column")
        else:
            print("email_notifications column already exists")
        
        # Add sms_notifications column if it doesn't exist
        if 'sms_notifications' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN sms_notifications BOOLEAN DEFAULT 0")
            print("Added sms_notifications column")
        else:
            print("sms_notifications column already exists")
        
        conn.commit()
        conn.close()
        print("Database updated successfully!")
        
    except Exception as e:
        print(f"Error updating database: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database()
