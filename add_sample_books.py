"""
Script to add sample books data to the database
Run this script to populate the database with sample books
"""

from app import create_app
from database import db, Book, User, UserRole
from datetime import datetime

def add_sample_books():
    """Add sample books to the database"""
    app = create_app()
    with app.app_context():
        # Check if books already exist
        existing_books = Book.query.count()
        if existing_books > 0:
            print(f"Database already has {existing_books} books. Skipping sample data insertion.")
            return
        
        sample_books = [
            {
                'isbn': '978-0135957059',
                'title': 'Python Crash Course',
                'author': 'Eric Matthes',
                'publication': 'No Starch Press',
                'category': 'Programming',
                'language': 'English',
                'edition': '2nd',
                'pages': 544,
                'price': 39.95,
                'description': 'A hands-on, project-based introduction to programming in Python.',
                'quantity': 5,
                'available': 5
            },
            {
                'isbn': '978-0134685991',
                'title': 'Effective Java',
                'author': 'Joshua Bloch',
                'publication': 'Addison-Wesley',
                'category': 'Programming',
                'language': 'English',
                'edition': '3rd',
                'pages': 416,
                'price': 54.99,
                'description': 'The best-selling programming book for Java developers.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0596007126',
                'title': 'Head First Design Patterns',
                'author': 'Eric Freeman',
                'publication': "O'Reilly Media",
                'category': 'Programming',
                'language': 'English',
                'edition': '1st',
                'pages': 694,
                'price': 49.99,
                'description': 'A brain-friendly guide to design patterns.',
                'quantity': 4,
                'available': 4
            },
            {
                'isbn': '978-0201633610',
                'title': 'Design Patterns',
                'author': 'Erich Gamma',
                'publication': 'Addison-Wesley',
                'category': 'Programming',
                'language': 'English',
                'edition': '1st',
                'pages': 416,
                'price': 59.99,
                'description': 'Elements of Reusable Object-Oriented Software.',
                'quantity': 2,
                'available': 2
            },
            {
                'isbn': '978-0321125217',
                'title': 'Refactoring',
                'author': 'Martin Fowler',
                'publication': 'Addison-Wesley',
                'category': 'Programming',
                'language': 'English',
                'edition': '2nd',
                'pages': 448,
                'price': 64.99,
                'description': 'Improving the Design of Existing Code.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0132350884',
                'title': 'Clean Code',
                'author': 'Robert C. Martin',
                'publication': 'Prentice Hall',
                'category': 'Programming',
                'language': 'English',
                'edition': '1st',
                'pages': 464,
                'price': 49.99,
                'description': 'A Handbook of Agile Software Craftsmanship.',
                'quantity': 4,
                'available': 4
            },
            {
                'isbn': '978-0134685992',
                'title': 'The Pragmatic Programmer',
                'author': 'Andrew Hunt',
                'publication': 'Addison-Wesley',
                'category': 'Programming',
                'language': 'English',
                'edition': '1st',
                'pages': 352,
                'price': 44.99,
                'description': 'Your Journey to Mastery.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0596517748',
                'title': 'JavaScript: The Good Parts',
                'author': 'Douglas Crockford',
                'publication': "O'Reilly Media",
                'category': 'Programming',
                'language': 'English',
                'edition': '1st',
                'pages': 176,
                'price': 29.99,
                'description': 'Uncovering the excellent parts of JavaScript.',
                'quantity': 5,
                'available': 5
            },
            {
                'isbn': '978-1491950296',
                'title': 'Data Science from Scratch',
                'author': 'Joel Grus',
                'publication': "O'Reilly Media",
                'category': 'Data Science',
                'language': 'English',
                'edition': '2nd',
                'pages': 406,
                'price': 49.99,
                'description': 'First Principles with Python.',
                'quantity': 4,
                'available': 4
            },
            {
                'isbn': '978-1491912058',
                'title': 'Python for Data Analysis',
                'author': 'Wes McKinney',
                'publication': "O'Reilly Media",
                'category': 'Data Science',
                'language': 'English',
                'edition': '2nd',
                'pages': 544,
                'price': 54.99,
                'description': 'Data Wrangling with Pandas, NumPy, and IPython.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0321884058',
                'title': 'Introduction to Algorithms',
                'author': 'Thomas H. Cormen',
                'publication': 'MIT Press',
                'category': 'Computer Science',
                'language': 'English',
                'edition': '3rd',
                'pages': 1312,
                'price': 74.99,
                'description': 'A comprehensive introduction to algorithms.',
                'quantity': 2,
                'available': 2
            },
            {
                'isbn': '978-0262033848',
                'title': 'Structure and Interpretation of Computer Programs',
                'author': 'Harold Abelson',
                'publication': 'MIT Press',
                'category': 'Computer Science',
                'language': 'English',
                'edition': '2nd',
                'pages': 657,
                'price': 69.99,
                'description': 'A classic textbook on computer programming.',
                'quantity': 2,
                'available': 2
            },
            {
                'isbn': '978-0134444281',
                'title': 'Artificial Intelligence: A Modern Approach',
                'author': 'Stuart Russell',
                'publication': 'Pearson',
                'category': 'Artificial Intelligence',
                'language': 'English',
                'edition': '4th',
                'pages': 1152,
                'price': 84.99,
                'description': 'The definitive text on AI.',
                'quantity': 2,
                'available': 2
            },
            {
                'isbn': '978-0387310732',
                'title': 'Pattern Recognition and Machine Learning',
                'author': 'Christopher Bishop',
                'publication': 'Springer',
                'category': 'Machine Learning',
                'language': 'English',
                'edition': '1st',
                'pages': 738,
                'price': 94.99,
                'description': 'Information Science and Statistics.',
                'quantity': 2,
                'available': 2
            },
            {
                'isbn': '978-1491952437',
                'title': 'Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow',
                'author': 'Aurélien Géron',
                'publication': "O'Reilly Media",
                'category': 'Machine Learning',
                'language': 'English',
                'edition': '2nd',
                'pages': 856,
                'price': 59.99,
                'description': 'Concepts, Tools, and Techniques to Build Intelligent Systems.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0262046257',
                'title': 'Deep Learning',
                'author': 'Ian Goodfellow',
                'publication': 'MIT Press',
                'category': 'Deep Learning',
                'language': 'English',
                'edition': '1st',
                'pages': 800,
                'price': 89.99,
                'description': 'An MIT Press book on deep learning.',
                'quantity': 2,
                'available': 2
            },
            {
                'isbn': '978-1449372620',
                'title': 'Fluent Python',
                'author': 'Luciano Ramalho',
                'publication': "O'Reilly Media",
                'category': 'Programming',
                'language': 'English',
                'edition': '2nd',
                'pages': 1012,
                'price': 64.99,
                'description': 'Clear, Concise, and Effective Programming.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0596007973',
                'title': 'Learning Python',
                'author': 'Mark Lutz',
                'publication': "O'Reilly Media",
                'category': 'Programming',
                'language': 'English',
                'edition': '5th',
                'pages': 1648,
                'price': 64.99,
                'description': 'Powerful Object-Oriented Programming.',
                'quantity': 4,
                'available': 4
            },
            {
                'isbn': '978-0201616224',
                'title': 'The C Programming Language',
                'author': 'Brian Kernighan',
                'publication': 'Prentice Hall',
                'category': 'Programming',
                'language': 'English',
                'edition': '2nd',
                'pages': 272,
                'price': 54.99,
                'description': 'The classic C programming book.',
                'quantity': 3,
                'available': 3
            },
            {
                'isbn': '978-0131103627',
                'title': 'The C++ Programming Language',
                'author': 'Bjarne Stroustrup',
                'publication': 'Addison-Wesley',
                'category': 'Programming',
                'language': 'English',
                'edition': '4th',
                'pages': 1368,
                'price': 74.99,
                'description': 'The definitive C++ reference.',
                'quantity': 2,
                'available': 2
            }
        ]
        
        # Add books to database
        for book_data in sample_books:
            book = Book(**book_data)
            db.session.add(book)
        
        db.session.commit()
        print(f"Successfully added {len(sample_books)} sample books to the database!")

if __name__ == '__main__':
    add_sample_books()
