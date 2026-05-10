"""
Database Migration Script
Add profile_photo column to existing database
"""

import sqlite3
import os

def add_profile_photo_column():
    """Add profile_photo column to existing database"""
    db_path = 'library.db'
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'profile_photo' in columns:
            print("profile_photo column already exists")
            conn.close()
            return True
        
        # Add profile_photo column
        cursor.execute("ALTER TABLE users ADD COLUMN profile_photo VARCHAR(255)")
        conn.commit()
        conn.close()
        
        print("profile_photo column added successfully!")
        return True
        
    except Exception as e:
        print(f"Error adding profile_photo column: {e}")
        return False

if __name__ == "__main__":
    add_profile_photo_column()
