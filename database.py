"""
Database Models and Configuration
Library Management System SQLAlchemy Models
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from enum import Enum
import os

# Initialize SQLAlchemy
db = SQLAlchemy()


class UserRole(Enum):
    """User roles enumeration"""
    ADMIN = "admin"
    STUDENT = "student"


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    roll_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    contact = db.Column(db.String(20))
    address = db.Column(db.Text)
    role = db.Column(db.Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issued_books = db.relationship('IssuedBook', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    fines = db.relationship('Fine', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_total_fines(self):
        """Get total unpaid fines for this user"""
        return sum(fine.amount for fine in self.fines if not fine.is_paid)
    
    def __repr__(self):
        return f'<User {self.name} ({self.email})>'


class Book(db.Model):
    """Book model for library inventory"""

    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)

    # NEW FIELD
    rack_number = db.Column(db.String(20))

    publication = db.Column(db.String(100))
    category = db.Column(db.String(50))
    language = db.Column(db.String(20), default='English')
    edition = db.Column(db.String(20))
    pages = db.Column(db.Integer)
    price = db.Column(db.Float)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    available = db.Column(db.Integer, default=1, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    issued_copies = db.relationship(
        'IssuedBook',
        backref='book',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    @property
    def issued_count(self):
        """Get number of currently issued copies"""
        return self.issued_copies.filter_by(is_returned=False).count()

    @property
    def is_available(self):
        """Check if book is available for issue"""
        return self.available > 0

    def __repr__(self):
        return f'<Book {self.title} by {self.author}>'

class IssuedBook(db.Model):
    """Issued book model for tracking book loans"""
    
    __tablename__ = 'issued_books'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime)
    is_returned = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    fine = db.relationship('Fine', backref='issued_book', uselist=False, cascade='all, delete-orphan')
    
    @property
    def is_overdue(self):
        """Check if book is overdue"""
        return not self.is_returned and datetime.utcnow() > self.due_date
    
    @property
    def days_overdue(self):
        """Get number of days overdue"""
        if self.is_overdue:
            return (datetime.utcnow() - self.due_date).days
        return 0
    
    @property
    def student(self):
        """Get student who issued the book"""
        return self.user
    
    def __repr__(self):
        status = "Returned" if self.is_returned else "Issued"
        return f'<IssuedBook {self.book.title} to {self.user.name} ({status})>'


class Fine(db.Model):
    """Fine model for tracking overdue book penalties"""
    
    __tablename__ = 'fines'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    issued_book_id = db.Column(db.Integer, db.ForeignKey('issued_books.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    is_paid = db.Column(db.Boolean, default=False, nullable=False)
    paid_date = db.Column(db.DateTime)
    payment_method = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def mark_as_paid(self, payment_method=None):
        """Mark fine as paid"""
        self.is_paid = True
        self.paid_date = datetime.utcnow()
        self.payment_method = payment_method
    
    def __repr__(self):
        status = "Paid" if self.is_paid else "Unpaid"
        return f'<Fine Rs.{self.amount} for {self.user.name} ({status})>'


class BookReservation(db.Model):
    """Book reservation model for students to reserve books"""
    
    __tablename__ = 'book_reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    reservation_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_date = db.Column(db.DateTime)  # When reservation expires
    status = db.Column(db.String(20), default='active')  # active, fulfilled, cancelled, expired
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    book = db.relationship('Book', backref=db.backref('reservations', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('reservations', lazy='dynamic', cascade='all, delete-orphan'))
    
    def mark_as_fulfilled(self):
        """Mark reservation as fulfilled"""
        self.status = 'fulfilled'
        self.updated_at = datetime.utcnow()
    
    def cancel_reservation(self):
        """Cancel reservation"""
        self.status = 'cancelled'
        self.updated_at = datetime.utcnow()
    
    def is_expired(self):
        """Check if reservation is expired"""
        return datetime.utcnow() > self.expiry_date
    
    def mark_as_expired(self):
        """Mark reservation as expired"""
        self.status = 'expired'
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Reservation {self.book.title} by {self.user.name} ({self.status})>'


class BookRequest(db.Model):
    """Book request model for students to request books not available in library"""
    __tablename__ = 'book_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('book_requests', lazy='dynamic', cascade='all, delete-orphan'))
    
    def approve_request(self, notes=None):
        """Approve book request and issue book to user"""
        from app import db, Book, IssuedBook
        
        self.status = 'approved'
        if notes:
            self.admin_notes = notes
        self.updated_at = datetime.utcnow()
        
        # Try to find the book in library by title or ISBN
        book = None
        if self.isbn:
            book = Book.query.filter_by(isbn=self.isbn).first()
        if not book:
            book = Book.query.filter(db.or_(
                Book.title.ilike(self.book_title),
                Book.title.ilike(f'%{self.book_title}%')
            )).first()
        
        # If book exists, issue it to the user
        if book and book.available > 0:
            # Create issued book entry
            issued_book = IssuedBook(
                user_id=self.user_id,
                book_id=book.id,
                issue_date=datetime.utcnow(),
                due_date=datetime.utcnow() + timedelta(days=14),  # Default 14 days
                notes=f'Auto-issued from approved book request: {self.reason}'
            )
            
            # Update book availability
            book.available -= 1
            book.total_issued += 1
            
            db.session.add(issued_book)
            db.session.add(book)
    
    def reject_request(self, notes=None):
        """Reject book request"""
        self.status = 'rejected'
        if notes:
            self.admin_notes = notes
        self.updated_at = datetime.utcnow()


class BookRenewal(db.Model):
    """Book renewal request model for students to request book renewal"""
    __tablename__ = 'book_renewals'
    
    id = db.Column(db.Integer, primary_key=True)
    issued_book_id = db.Column(db.Integer, db.ForeignKey('issued_books.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_days = db.Column(db.Integer, default=14)  # Default renewal period
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    admin_notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    issued_book = db.relationship('IssuedBook', backref=db.backref('renewal_requests', lazy='dynamic', cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('renewal_requests', lazy='dynamic', cascade='all, delete-orphan'))
    
    def approve_renewal(self):
        """Approve renewal request and extend due date"""
        if self.issued_book and not self.issued_book.is_returned:
            # Extend due date by requested days
            from datetime import timedelta
            self.issued_book.due_date = datetime.utcnow() + timedelta(days=self.requested_days)
            self.status = 'approved'
            self.updated_at = datetime.utcnow()
            return True
        return False


class ReadingStreak(db.Model):
    """Reading streak model for tracking consecutive reading days"""
    __tablename__ = 'reading_streaks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    current_streak = db.Column(db.Integer, default=0)
    longest_streak = db.Column(db.Integer, default=0)
    last_reading_date = db.Column(db.DateTime, nullable=True)
    total_reading_days = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('reading_streak', uselist=False, cascade='all, delete-orphan'))
    
    def update_streak(self):
        """Update reading streak based on last reading date"""
        today = datetime.utcnow().date()
        
        if self.last_reading_date:
            last_date = self.last_reading_date.date()
            days_diff = (today - last_date).days
            
            if days_diff == 1:
                # Consecutive day, increment streak
                self.current_streak += 1
                self.total_reading_days += 1
            elif days_diff == 0:
                # Same day, no change
                pass
            else:
                # Streak broken, reset to 1 for today
                self.current_streak = 1
                self.total_reading_days += 1
        else:
            # First reading activity
            self.current_streak = 1
            self.total_reading_days = 1
        
        # Update longest streak if needed
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak
        
        self.last_reading_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def check_streak_status(self):
        """Check if streak is still active (within 1 day)"""
        if not self.last_reading_date:
            return 0
        
        today = datetime.utcnow().date()
        last_date = self.last_reading_date.date()
        days_diff = (today - last_date).days
        
        if days_diff == 0:
            return self.current_streak  # Active today
        elif days_diff == 1:
            return self.current_streak  # Still active from yesterday
        else:
            return 0  # Streak broken
    
    def __repr__(self):
        return f'<ReadingStreak {self.user.name}: {self.current_streak} days>'


class Notification(db.Model):
    """Notification model for user notifications"""
    
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default='info')  # info, warning, success, error
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic', cascade='all, delete-orphan'))
    
    def mark_as_read(self):
        """Mark notification as read"""
        self.is_read = True
    
    def __repr__(self):
        return f'<Notification {self.title} for {self.user.name}>'


# Database utility functions
def init_db(app):
    """Initialize database with app context"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(email='admin@library.com').first()
        if not admin:
            admin = User(
                name='System Administrator',
                email='admin@library.com',
                roll_number='ADMIN001',
                role=UserRole.ADMIN
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created: admin@library.com / admin123")


def create_sample_data():
    """Create sample data for testing"""
    # Check if data already exists
    if Book.query.first():
        return
    
    # Sample books
    books = [
        Book(
            isbn='978-0-13-468599-1',
            title='Effective Python',
            author='Brett Slatkin',
            publication='Addison-Wesley',
            category='Programming',
            language='English',
            edition='2nd',
            pages=500,
            price=45.99,
            rack_number='A-101',
            quantity=5,
            available=5,
            description='Effective Python: 90 Specific Ways to Write Better Python Code'
        ),
        Book(
            isbn='978-1-4919-5066-5',
            title='Flask Web Development',
            author='Miguel Grinberg',
            publication="O'Reilly",
            category='Programming',
            language='English',
            edition='2nd',
            pages=350,
            price=39.99,
            rack_number='A-102',
            quantity=3,
            available=3,
            description='Flask Web Development: Developing Web Applications with Python'
        ),
        Book(
            isbn='978-0-262-03293-3',
            title='Introduction to Algorithms',
            author='Thomas H. Cormen',
            publication='MIT Press',
            category='Computer Science',
            language='English',
            edition='3rd',
            pages=1200,
            price=85.99,
            rack_number='B-201',
            quantity=2,
            available=2,
            description='Introduction to Algorithms, 3rd Edition'
        )
    ]
    
    for book in books:
        db.session.add(book)
    
    # Sample student
    student = User(
        name='John Doe',
        email='john.doe@university.edu',
        roll_number='CS2024001',
        contact='+1-234-567-8900',
        address='123 Campus Drive, University City',
        role=UserRole.STUDENT
    )
    student.set_password('student123')
    db.session.add(student)
    
    db.session.commit()
    print("Sample data created successfully!")


if __name__ == '__main__':
    # Test database connection
    from flask import Flask
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/library.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    init_db(app)
    create_sample_data()
