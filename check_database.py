import sqlite3

def check_database():
    conn = sqlite3.connect('library.db')
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print("Tables:", tables)
    
    # Check users table structure
    if ('users',) in tables:
        cursor.execute('PRAGMA table_info(users)')
        columns = cursor.fetchall()
        print("Users table columns:")
        for col in columns:
            print(f"  {col[1]} - {col[2]}")
    
    conn.close()

if __name__ == "__main__":
    check_database()
