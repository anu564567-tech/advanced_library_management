"""
Database Initialization Script
Create database with proper schema including notification fields
"""

import sqlite3
import os

def create_database():
    """Create database with proper schema"""
    db_path = 'library.db'
    
    # Remove existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Removed existing database")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                roll_number VARCHAR(20) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                contact VARCHAR(20),
                address TEXT,
                role VARCHAR(20) DEFAULT 'student' NOT NULL,
                is_active BOOLEAN DEFAULT 1 NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create books table
        cursor.execute('''
            CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn VARCHAR(20) UNIQUE NOT NULL,
                title VARCHAR(200) NOT NULL,
                author VARCHAR(100) NOT NULL,
                publication VARCHAR(100),
                category VARCHAR(50),
                language VARCHAR(20) DEFAULT 'English',
                edition VARCHAR(20),
                pages INTEGER,
                price DECIMAL(10, 2),
                available_copies INTEGER DEFAULT 1,
                total_copies INTEGER DEFAULT 1,
                description TEXT,
                cover_image VARCHAR(255),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create other necessary tables
        cursor.execute('''
            CREATE TABLE issued_books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                issue_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                due_date DATETIME,
                return_date DATETIME,
                is_returned BOOLEAN DEFAULT 0 NOT NULL,
                fine_amount DECIMAL(10, 2) DEFAULT 0,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE fines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                issued_book_id INTEGER NOT NULL,
                amount DECIMAL(10, 2) NOT NULL,
                is_paid BOOLEAN DEFAULT 0 NOT NULL,
                paid_date DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (issued_book_id) REFERENCES issued_books (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                message TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'info',
                is_read BOOLEAN DEFAULT 0 NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE book_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                book_title VARCHAR(200) NOT NULL,
                author VARCHAR(200) NOT NULL,
                isbn VARCHAR(20),
                reason TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("Database created successfully!")
        
    except Exception as e:
        print(f"Error creating database: {e}")
        if conn:
            conn.close()

if __name__ == "__main__":
    create_database()
