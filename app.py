"""
Library Management System
Flask Application - Main Entry Point
Production-level code with comprehensive features
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import json
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from functools import wraps
from datetime import datetime, timedelta
from sqlalchemy import desc, func, and_
from config import config
from database import db, User, Book, IssuedBook, Fine, Notification, UserRole, BookReservation, BookRequest, BookRenewal
import os
import io
from werkzeug.utils import secure_filename

# Global SocketIO instance
socketio = None


def create_app(config_name='development'):
    """
    Application Factory Function
    Creates and configures Flask application
    """
    app = Flask(__name__, template_folder='templates', static_folder='static')
    
    # Load configuration
    config_name = os.environ.get('FLASK_CONFIG', 'development')
    app.config.from_object(config[config_name])
    
    # Set upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'reports')
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize SocketIO for real-time features
    global socketio
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Create database tables (moved to after app is fully configured)
    with app.app_context():
        try:
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
        except Exception as e:
            print(f"Database initialization error: {e}")
            # Continue without database for now
    
    # ==================== DECORATORS ====================
    
    def admin_required(f):
        """Decorator to require admin role"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    
    def student_required(f):
        """Decorator to require student role"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != UserRole.STUDENT:
                flash('This feature is only available for students.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    
    # ==================== AUTHENTICATION ROUTES ====================
    
    @app.route('/')
    def index():
        """Home page - redirect to dashboard if logged in"""
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration"""
        # Temporarily disabled auth check for testing
        # if current_user.is_authenticated:
        #     return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            contact = request.form.get('contact', '').strip()
            address = request.form.get('address', '').strip()
            
            # Get form data
            role = request.form.get('role', '').strip()
            
            # Validation
            if not all([name, email, password, role, contact]):
                flash('Please fill all required fields.', 'danger')
                return redirect(url_for('register'))
            
            # Roll number is required for students but optional for admins
            if role == 'student' and not roll_number:
                flash('Roll number is required for student registration.', 'danger')
                return redirect(url_for('register'))
            
            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return redirect(url_for('register'))
            
            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return redirect(url_for('register'))
            
            # Check if user exists
            if User.query.filter_by(email=email).first():
                flash('Email already registered. Please log in.', 'warning')
                return redirect(url_for('login'))
            
            # Check roll number uniqueness only if provided
            if roll_number and User.query.filter_by(roll_number=roll_number).first():
                flash('Roll number already exists.', 'warning')
                return redirect(url_for('register'))
            
                        
            try:
                # Create new user
                user_role = UserRole.ADMIN if role == 'admin' else UserRole.STUDENT
                new_user = User(
                    name=name,
                    email=email,
                    roll_number=roll_number,
                    contact=contact,
                    address=address,
                    role=user_role
                )
                new_user.set_password(password)
                
                db.session.add(new_user)
                db.session.commit()
                
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Registration failed: {str(e)}', 'danger')
                return redirect(url_for('register'))
        
        return render_template('register.html')
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login"""
        # Temporarily disabled auth check for debugging
        # if current_user.is_authenticated:
        #     return redirect(url_for('dashboard'))
        
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                if not user.is_active:
                    flash('Your account has been deactivated.', 'danger')
                    return redirect(url_for('login'))
                
                login_user(user, remember=remember)
                session.permanent = True
                
                next_page = request.args.get('next')
                if not next_page or url_has_no_scheme(next_page):
                    next_page = url_for('dashboard')
                
                flash(f'Welcome back, {user.name}!', 'success')
                return redirect(next_page)
            
            flash('Invalid email or password.', 'danger')
        
        return render_template('login.html')
    
    @app.route('/debug-login')
    def debug_login():
        """Debug login template"""
        return render_template('debug-login.html')
    
    @app.route('/profile')
    @login_required
    def profile():
        """User profile page"""
        return render_template('profile.html', user=current_user)
    
    @app.route('/update_profile', methods=['POST'])
    @login_required
    def update_profile():
        """Update user profile"""
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            contact = request.form.get('contact', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not name or not email:
                flash('Name and email are required fields.', 'error')
                return redirect(url_for('profile'))
            
            # Roll number is required for students but optional for admins
            if current_user.role == UserRole.STUDENT and not roll_number:
                flash('Roll number is required for student accounts.', 'error')
                return redirect(url_for('profile'))
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                and_(User.email == email, User.id != current_user.id)
            ).first()
            if existing_user:
                flash('Email is already taken by another user.', 'error')
                return redirect(url_for('profile'))
            
            # Update user profile
            current_user.name = name
            current_user.email = email
            current_user.roll_number = roll_number if roll_number else None
            current_user.contact = contact if contact else None
            current_user.address = address if address else None
            
            db.session.commit()
            
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your profile. Please try again.', 'error')
            return redirect(url_for('profile'))
    
    @app.route('/settings')
    @login_required
    def settings():
        """User settings page"""
        return render_template('settings.html', user=current_user)
    
    @app.route('/update_settings', methods=['POST'])
    @login_required
    def update_settings():
        """Update user account settings"""
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            roll_number = request.form.get('roll_number', '').strip()
            contact = request.form.get('contact', '').strip()
            address = request.form.get('address', '').strip()
            
            # Validate required fields
            if not name or not email:
                flash('Name and email are required fields.', 'error')
                return redirect(url_for('settings'))
            
            # Roll number is required for students but optional for admins
            if current_user.role == UserRole.STUDENT and not roll_number:
                flash('Roll number is required for student accounts.', 'error')
                return redirect(url_for('settings'))
            
            # Check if email is already taken by another user
            existing_user = User.query.filter(
                and_(User.email == email, User.id != current_user.id)
            ).first()
            if existing_user:
                flash('Email is already taken by another user.', 'error')
                return redirect(url_for('settings'))
            
            # Check if roll number is already taken by another user
            if roll_number:
                existing_roll = User.query.filter(
                    and_(User.roll_number == roll_number, User.id != current_user.id)
                ).first()
                if existing_roll:
                    flash('Roll number is already taken by another user.', 'error')
                    return redirect(url_for('settings'))
            
            # Update user settings
            current_user.name = name
            current_user.email = email
            current_user.roll_number = roll_number if roll_number else None
            current_user.contact = contact if contact else None
            current_user.address = address if address else None
            
            db.session.commit()
            
            flash('Account settings updated successfully!', 'success')
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while updating your settings. Please try again.', 'error')
            return redirect(url_for('settings'))
    
        
        
    @app.route('/logout')
    @login_required
    def logout():
        """Logout user"""
        logout_user()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('login'))
    
    # ==================== DASHBOARD ROUTES ====================
    
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Dashboard with analytics"""
        
        # Get statistics
        total_books = Book.query.count()
        total_users = User.query.count()
        issued_books = IssuedBook.query.filter_by(is_returned=False).count()
        overdue_books = IssuedBook.query.filter(
            and_(
                IssuedBook.is_returned == False,
                IssuedBook.due_date < datetime.utcnow()
            )
        ).count()
        
        # Get recently issued books for activity feed
        # Filter by user role: students see only their activities, admins see all
        if current_user.role == UserRole.STUDENT:
            recent_issues = IssuedBook.query.filter_by(user_id=current_user.id).order_by(desc(IssuedBook.issue_date)).limit(8).all()
        else:
            recent_issues = IssuedBook.query.order_by(desc(IssuedBook.issue_date)).limit(8).all()
        
        # Calculate total issues (all issued books)
        total_issues = IssuedBook.query.count()
        
        # Format activities for template
        recent_activities = []
        for issue in recent_issues:
            try:
                activity_type = 'return' if issue.is_returned else 'issue'
                student_name = issue.user.name if issue.user else 'Unknown User'
                book_title = issue.book.title if issue.book else 'Unknown Book'
                description = f'Book "{book_title}" {"returned by" if issue.is_returned else "issued to"} {student_name}'
                if issue.is_returned and issue.fine and issue.fine.amount > 0:
                    description += f' (Fine: Rs. {issue.fine.amount})'
                
                # Include recent activities
                recent_activities.append({
                    'type': activity_type,
                    'description': description,
                    'date': issue.return_date if issue.is_returned else issue.issue_date
                })
            except Exception as e:
                print(f"Error processing activity: {e}")
                continue
        
        # If no activities, add some sample activities for demonstration
        if not recent_activities:
            sample_activities = [
                {
                    'type': 'issue',
                    'description': 'Book "Python Programming" issued to John Doe',
                    'date': datetime.utcnow() - timedelta(hours=2)
                },
                {
                    'type': 'return',
                    'description': 'Book "Data Structures" returned by Jane Smith',
                    'date': datetime.utcnow() - timedelta(hours=4)
                },
                {
                    'type': 'issue',
                    'description': 'Book "Web Development" issued to Mike Johnson',
                    'date': datetime.utcnow() - timedelta(hours=6)
                }
            ]
            recent_activities = sample_activities
        
        # Get current user's statistics
        user_issued = 0
        user_overdue = 0
        user_fines = 0
        my_issued_books = 0
        my_fines = 0
        my_reservations = 0
        
        if current_user.role == UserRole.STUDENT:
            user_issued = IssuedBook.query.filter_by(
                user_id=current_user.id,
                is_returned=False
            ).count()
            
            user_overdue = IssuedBook.query.filter(
                and_(
                    IssuedBook.user_id == current_user.id,
                    IssuedBook.is_returned == False,
                    IssuedBook.due_date < datetime.utcnow()
                )
            ).count()
            
            user_fines = current_user.get_total_fines()
            
            # Additional variables for template
            my_issued_books = user_issued
            my_fines = user_fines
            overdue_books = user_overdue
            
            # Get user's active reservations
            my_reservations = BookReservation.query.filter_by(
                user_id=current_user.id,
                status='active'
            ).count()
            
            # Get or create reading streak for user
            from database import ReadingStreak
            reading_streak = ReadingStreak.query.filter_by(user_id=current_user.id).first()
            if not reading_streak:
                reading_streak = ReadingStreak(user_id=current_user.id)
                db.session.add(reading_streak)
                db.session.commit()
            
            # Check if user has issued books today to update streak
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            today_issues = IssuedBook.query.filter(
                and_(
                    IssuedBook.user_id == current_user.id,
                    IssuedBook.issue_date >= today_start
                )
            ).count()
            
            # Update streak if user has reading activity today
            if today_issues > 0:
                reading_streak.update_streak()
                db.session.commit()
            
            reading_streak_count = reading_streak.check_streak_status()
        else:
            # For admin, set default values
            my_issued_books = 0
            my_fines = 0
            overdue_books = 0
            my_reservations = 0
            reading_streak_count = 0
        
        return render_template('dashboard.html',
                             total_books=total_books,
                             total_users=total_users,
                             issued_books=issued_books,
                             overdue_books=overdue_books,
                             total_issues=total_issues,
                             my_issued_books=my_issued_books,
                             my_fines=my_fines,
                             my_reservations=my_reservations,
                             reading_streak_count=reading_streak_count,
                             recent_activities=recent_activities,
                             user_role=current_user.role.value)
    
    @app.route('/api/dashboard-stats')
    @login_required
    def get_dashboard_stats():
        """API endpoint for real-time dashboard statistics"""
        
        total_books = Book.query.count()
        total_users = User.query.count()
        issued_books = IssuedBook.query.filter_by(is_returned=False).count()
        overdue_books = IssuedBook.query.filter(
            and_(
                IssuedBook.is_returned == False,
                IssuedBook.due_date < datetime.utcnow()
            )
        ).count()
        
        # Category distribution
        category_data = db.session.query(
            Book.category,
            func.count(Book.id).label('count')
        ).group_by(Book.category).all()
        
        # Monthly issue statistics
        monthly_data = db.session.query(
            func.strftime('%m', IssuedBook.issue_date).label('month'),
            func.count(IssuedBook.id).label('count')
        ).group_by(
            func.strftime('%m', IssuedBook.issue_date)
        ).all()
        
        return jsonify({
            'total_books': total_books,
            'total_users': total_users,
            'issued_books': issued_books,
            'overdue_books': overdue_books,
            'categories': {cat[0] or 'Other': cat[1] for cat in category_data if cat[0]},
            'monthly': {data[0] or '0': data[1] for data in monthly_data}
        })
    
    # ==================== BOOK MANAGEMENT ROUTES ====================
    
    @app.route('/books')
    @login_required
    def books_list():
        """List all books with search and filter"""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str).strip()
        category = request.args.get('category', '', type=str).strip()
        
        query = Book.query
        
        # Search filter
        if search:
            query = query.filter(
                db.or_(
                    Book.title.ilike(f'%{search}%'),
                    Book.author.ilike(f'%{search}%'),
                    Book.isbn.ilike(f'%{search}%')
                )
            )
        
        # Category filter
        if category:
            query = query.filter_by(category=category)
        
        # Get all categories for filter dropdown
        all_categories = db.session.query(Book.category).distinct().filter(
            Book.category != None
        ).all()
        categories = [c[0] for c in all_categories]
        
        # Pagination
        pagination = query.paginate(page=page, per_page=10)
        books = pagination.items
        
        return render_template(
            'books.html',
            books=books,
            pagination=pagination,
            search=search,
            category=category,
            categories=categories
        )
    
    @app.route('/books/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def add_book():
        """Add new book (Admin only)"""
        if request.method == 'POST':
            isbn = request.form.get('isbn', '').strip()
            title = request.form.get('title', '').strip()
            author = request.form.get('author', '').strip()
            publication = request.form.get('publication', '').strip()
            category = request.form.get('category', '').strip()
            quantity = request.form.get('quantity', 1, type=int)
            description = request.form.get('description', '').strip()
            edition = request.form.get('edition', '').strip()
            language = request.form.get('language', 'English').strip()
            pages = request.form.get('pages', 1, type=int)
            price = request.form.get('price', 1, type=float)
            rack_number = request.form.get('rack_number', '').strip()
            
            # Validation
            if not all([isbn, title, author]):
                flash('Please fill all required fields.', 'danger')
                return redirect(url_for('add_book'))
            
            if Book.query.filter_by(isbn=isbn).first():
                flash('Book with this ISBN already exists.', 'warning')
                return redirect(url_for('add_book'))
            
            try:
                new_book = Book(
                    isbn=isbn,
                    title=title,
                    author=author,
                    publication=publication,
                    category=category,
                    quantity=quantity,
                    available=quantity,
                    description=description,
                    edition=edition,
                    language=language,
                    pages=pages,
                    price=price,
                    rack_number=rack_number
                )
                
                db.session.add(new_book)
                db.session.commit()
                
                # Emit real-time update for new book
                socketio.emit('book_added', {
                    'book_id': new_book.id,
                    'title': new_book.title,
                    'author': new_book.author,
                    'category': new_book.category,
                    'available': new_book.available
                }, room='books')
                
                # Update dashboard stats
                socketio.emit('stats_changed', room='dashboard')
                
                flash(f'Book "{title}" added successfully!', 'success')
                return redirect(url_for('books_list'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error adding book: {str(e)}', 'danger')
                return redirect(url_for('add_book'))
        
        return render_template('books_add.html')
    
    @app.route('/book/<int:book_id>')
    @login_required
    def book_details(book_id):
        """View book details"""
        book = Book.query.get_or_404(book_id)
        return render_template('book_details.html', book=book)
    
    @app.route('/books/<int:book_id>/edit', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def edit_book(book_id):
        """Edit book details (Admin only)"""
        book = Book.query.get_or_404(book_id)
        
        if request.method == 'POST':
            book.title = request.form.get('title', '').strip()
            book.author = request.form.get('author', '').strip()
            book.publication = request.form.get('publication', '').strip()
            book.category = request.form.get('category', '').strip()
            book.total_quantity = request.form.get('quantity', 1, type=int)
            book.description = request.form.get('description', '').strip()
            book.edition = request.form.get('edition', '').strip()
            book.language = request.form.get('language', 'English').strip()
            book.pages = request.form.get('pages', 0, type=int)
            book.price = request.form.get('price', 0, type=float)
            book.rack_number = request.form.get('rack_number', '').strip()
            
            # Update available count
            issued_count = IssuedBook.query.filter(
                and_(
                    IssuedBook.book_id == book_id,
                    IssuedBook.is_returned == False
                )
            ).count()
            book.available = book.quantity - issued_count
            
            try:
                db.session.commit()
                flash(f'Book "{book.title}" updated successfully!', 'success')
                return redirect(url_for('books_list'))
            
            except Exception as e:
                db.session.rollback()
                flash(f'Error updating book: {str(e)}', 'danger')
        
        return render_template('books_edit.html', book=book)
    
    @app.route('/books/<int:book_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def delete_book(book_id):
        """Delete book (Admin only)"""
        book = Book.query.get_or_404(book_id)
        
        # Check if book is issued
        if IssuedBook.query.filter_by(book_id=book_id, is_returned=False).first():
            flash('Cannot delete book. Copy is currently issued.', 'warning')
            return redirect(url_for('books_list'))
        
        try:
            title = book.title
            db.session.delete(book)
            db.session.commit()
            
            # Emit real-time update for deleted book
            socketio.emit('book_deleted', {
                'book_id': book_id,
                'title': book.title
            }, room='books')
            
            # Update dashboard stats
            socketio.emit('stats_changed', room='dashboard')
            
            flash(f'Book "{title}" deleted successfully!', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting book: {str(e)}', 'danger')
        
        return redirect(url_for('books_list'))
    
    # ==================== BOOK ISSUE/RETURN ROUTES ====================
    
    @app.route('/issue-return')
    @login_required
    @admin_required
    def issue_return():
        """Issue and return books management"""
        page = request.args.get('page', 1, type=int)
        
        # Get all issued books (both current and recently returned)
        # Show books from last 30 days to give complete picture
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        issued_query = IssuedBook.query.filter(
            IssuedBook.issue_date >= thirty_days_ago
        ).order_by(
            desc(IssuedBook.issue_date)
        )
        
        pagination = issued_query.paginate(page=page, per_page=10)
        issued_books = pagination.items
        
        # Get all users and books for autocomplete
        users = User.query.filter_by(role=UserRole.STUDENT).all()
        books = Book.query.filter(Book.available > 0).all()
        
        # Prepare JSON data for autocomplete
        students_data = json.dumps([
            {'id': user.id, 'name': user.name, 'roll_number': user.roll_number}
            for user in users
        ])
        
        books_data = json.dumps([
            {'id': book.id, 'title': book.title, 'author': book.author, 'available': book.available}
            for book in books
        ])
        
        # Calculate statistics
        total_issued = IssuedBook.query.filter_by(is_returned=False).count()
        overdue_count = IssuedBook.query.filter(
            and_(
                IssuedBook.is_returned == False,
                IssuedBook.due_date < datetime.utcnow()
            )
        ).count()
        
        # Calculate returned today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        returned_today = IssuedBook.query.filter(
            and_(
                IssuedBook.is_returned == True,
                IssuedBook.return_date >= today_start
            )
        ).count()
        
        return render_template(
            'issue_return.html',
            issued_books=issued_books,
            pagination=pagination,
            users=users,
            books=books,
            students_data=students_data,
            books_data=books_data,
            datetime=datetime,
            total_issued=total_issued,
            overdue_count=overdue_count,
            returned_today=returned_today
        )
    
    @app.route('/issue-book', methods=['POST'])
    @login_required
    @admin_required
    def issue_book():
        """Issue book to student"""
        user_id = request.form.get('user_id', type=int)
        book_id = request.form.get('book_id', type=int)
        due_days = request.form.get('due_days', 14, type=int)
        
        user = User.query.get(user_id)
        book = Book.query.get(book_id)
        
        if not user or not book:
            flash('Invalid user or book selected.', 'danger')
            return redirect(url_for('issue_return'))
        
        if book.available <= 0:
            flash(f'"{book.title}" is not available.', 'warning')
            return redirect(url_for('issue_return'))
        
        # Check if user already has this book issued
        existing = IssuedBook.query.filter(
            and_(
                IssuedBook.user_id == user_id,
                IssuedBook.book_id == book_id,
                IssuedBook.is_returned == False
            )
        ).first()
        
        if existing:
            flash(f'User already has "{book.title}" issued.', 'warning')
            return redirect(url_for('issue_return'))
        
        try:
            due_date = datetime.utcnow() + timedelta(days=due_days)
            
            new_issue = IssuedBook(
                user_id=user_id,
                book_id=book_id,
                due_date=due_date
            )
            
            book.available -= 1
            
            db.session.add(new_issue)
            db.session.commit()
            
            print(f"DEBUG: Book issued - ID: {new_issue.id}, User: {user.name}, Book: {book.title}")
            
            # Emit real-time updates
            socketio.emit('book_issued', {
                'book_id': book_id,
                'book_title': book.title,
                'user_name': user.name,
                'due_date': due_date.isoformat()
            }, room='books')
            
            # Update dashboard stats for all users
            socketio.emit('stats_changed', room='dashboard')
            
            flash(f'Book "{book.title}" issued to {user.name}.', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error issuing book: {str(e)}', 'danger')
        
        return redirect(url_for('issue_return'))
    
    @app.route('/return-book/<int:issued_id>', methods=['POST'])
    @login_required
    @admin_required
    def return_book(issued_id):
        """Return issued book"""
        print(f"DEBUG: Return book route called with issued_id: {issued_id}")
        issued_book = IssuedBook.query.get_or_404(issued_id)
        print(f"DEBUG: Found issued book: {issued_book.book.title} for {issued_book.user.name}")
        
        if issued_book.is_returned:
            flash('This book has already been returned.', 'warning')
            return redirect(url_for('issue_return'))
        
        try:
            issued_book.return_date = datetime.utcnow()
            issued_book.is_returned = True
            
            # Update book availability
            issued_book.book.available += 1
            
            # Calculate fine if overdue
            if issued_book.is_overdue:
                days_overdue = issued_book.days_overdue
                fine_amount = days_overdue * 2.0  # Rs. 2 per day
                
                fine = Fine(
                    user_id=issued_book.user_id,
                    issued_book_id=issued_id,
                    amount=fine_amount
                )
                db.session.add(fine)
                issued_book.fine = fine
            
            db.session.commit()
            
            print(f"DEBUG: Book returned - ID: {issued_book.id}, User: {issued_book.student.name}, Book: {issued_book.book.title}")
            
            # Emit real-time updates
            socketio.emit('book_returned', {
                'book_id': issued_book.book_id,
                'book_title': issued_book.book.title,
                'user_name': issued_book.student.name,
                'fine_amount': issued_book.fine.amount if issued_book.fine else 0
            }, room='books')
            
            # Update dashboard stats for all users
            socketio.emit('stats_changed', room='dashboard')
            
            flash(f'Book "{issued_book.book.title}" returned successfully.', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error returning book: {str(e)}', 'danger')
        
        return redirect(url_for('issue_return'))
    
    @app.route('/test-return/<int:issued_id>', methods=['GET'])
    @login_required
    @admin_required
    def test_return_book(issued_id):
        """Test return book route with GET method"""
        print(f"DEBUG: TEST return book route called with issued_id: {issued_id}")
        flash(f'Test: Return book {issued_id} would be processed', 'info')
        return redirect(url_for('issue_return'))
    
    @app.route('/return-book-get/<int:issued_id>', methods=['GET'])
    @login_required
    @admin_required
    def return_book_get(issued_id):
        """Return issued book using GET method for testing"""
        print(f"DEBUG: GET return book route called with issued_id: {issued_id}")
        
        # Call the actual return logic
        return return_book(issued_id)
        
        return redirect(url_for('issue_return'))
    
    @app.route('/renew-book/<int:issued_id>', methods=['POST'])
    @login_required
    @student_required
    def renew_book(issued_id):
        """Request renewal of issued book"""
        issued_book = IssuedBook.query.get_or_404(issued_id)
        
        # Check if the book belongs to current user
        if issued_book.user_id != current_user.id:
            flash('You can only renew your own books.', 'danger')
            return redirect(url_for('my_books'))
        
        # Check if book is already returned
        if issued_book.is_returned:
            flash('Cannot renew returned book.', 'danger')
            return redirect(url_for('my_books'))
        
        # Check if there's already a pending renewal request for this book
        existing_request = BookRenewal.query.filter_by(
            issued_book_id=issued_id,
            user_id=current_user.id,
            status='pending'
        ).first()
        
        if existing_request:
            flash('You already have a pending renewal request for this book.', 'warning')
            return redirect(url_for('my_books'))
        
        # Create renewal request
        renewal_request = BookRenewal(
            issued_book_id=issued_id,
            user_id=current_user.id,
            requested_days=14,
            reason=f"Renewal request for '{issued_book.book.title}'"
        )
        
        db.session.add(renewal_request)
        
        # Create notification for all admins
        admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title='New Renewal Request',
                message=f'{current_user.name} has requested renewal for "{issued_book.book.title}". Please review and approve/reject.'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash(f'Renewal request for "{issued_book.book.title}" submitted successfully! Waiting for admin approval.', 'info')
        return redirect(url_for('my_books'))
    
    @app.route('/notifications')
    @login_required
    def notifications():
        """View user notifications"""
        user_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
        
        # Mark notifications as read
        for notification in user_notifications:
            if not notification.is_read:
                notification.is_read = True
        db.session.commit()
        
        # Calculate unread count
        unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
        return render_template('notifications.html', notifications=user_notifications, unread_count=unread_count)
    
    @app.route('/my-books')
    @login_required
    @student_required
    def my_books():
        """View student's issued books"""
        issued_books = IssuedBook.query.filter_by(
            user_id=current_user.id,
            is_returned=False
        ).order_by(desc(IssuedBook.issue_date)).all()
        
        return render_template('my_books.html', issued_books=issued_books, datetime=datetime)
    
    @app.route('/fines')
    @login_required
    @student_required
    def my_fines():
        """View student's fines"""
        fines = Fine.query.filter_by(user_id=current_user.id).order_by(desc(Fine.created_at)).all()
        
        # Separate paid and unpaid fines
        unpaid_fines = [f for f in fines if not f.is_paid]
        paid_fines = [f for f in fines if f.is_paid]
        total_unpaid = sum(f.amount for f in unpaid_fines)
        
        return render_template('fines.html', 
                             fines=fines, 
                             unpaid_fines=unpaid_fines, 
                             paid_fines=paid_fines, 
                             total_unpaid=total_unpaid)
    
    @app.route('/pay-fine/<int:fine_id>', methods=['POST'])
    @login_required
    @student_required
    def pay_fine(fine_id):
        """Pay fine"""
        fine = Fine.query.get_or_404(fine_id)
        
        # Check if the fine belongs to current user
        if fine.user_id != current_user.id:
            flash('You can only pay your own fines.', 'danger')
            return redirect(url_for('my_fines'))
        
        # Check if fine is already paid
        if fine.is_paid:
            flash('This fine has already been paid.', 'warning')
            return redirect(url_for('my_fines'))
        
        # Mark fine as paid
        fine.is_paid = True
        fine.paid_at = datetime.utcnow()
        db.session.commit()
        
        flash(f'Fine of ₹{fine.amount} paid successfully!', 'success')
        return redirect(url_for('my_fines'))
    
    @app.route('/renewal-requests')
    @login_required
    @admin_required
    def renewal_requests():
        """View all book renewal requests"""
        renewals = BookRenewal.query.order_by(BookRenewal.created_at.desc()).all()
        return render_template('renewal_requests.html', renewals=renewals)
    
    @app.route('/approve-renewal/<int:renewal_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def approve_renewal(renewal_id):
        """Approve a book renewal request"""
        renewal = BookRenewal.query.get_or_404(renewal_id)
        
        if renewal.status != 'pending':
            flash('This renewal request has already been processed.', 'warning')
            return redirect(url_for('renewal_requests'))
        
        if renewal.approve_renewal():
            # Create notification for student
            notification = Notification(
                user_id=renewal.user_id,
                title='Renewal Request Approved',
                message=f'Your renewal request for "{renewal.issued_book.book.title}" has been approved. New due date: {renewal.issued_book.due_date.strftime("%Y-%m-%d")}.'
            )
            db.session.add(notification)
            db.session.commit()
            flash(f'Renewal request for "{renewal.issued_book.book.title}" approved successfully!', 'success')
        else:
            flash('Failed to approve renewal request. Book may have been returned.', 'danger')
        
        return redirect(url_for('renewal_requests'))
    
    @app.route('/reject-renewal/<int:renewal_id>', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def reject_renewal(renewal_id):
        """Reject a book renewal request"""
        renewal = BookRenewal.query.get_or_404(renewal_id)
        
        if renewal.status != 'pending':
            flash('This renewal request has already been processed.', 'warning')
            return redirect(url_for('renewal_requests'))
        
        notes = request.form.get('admin_notes', '')
        renewal.reject_renewal(notes)
        
        # Create notification for student
        message = f'Your renewal request for "{renewal.issued_book.book.title}" has been rejected.'
        if notes:
            message += f' Reason: {notes}'
        
        notification = Notification(
            user_id=renewal.user_id,
            title='Renewal Request Rejected',
            message=message
        )
        db.session.add(notification)
        db.session.commit()
        
        flash(f'Renewal request for "{renewal.issued_book.book.title}" rejected.', 'info')
        return redirect(url_for('renewal_requests'))
    
    @app.route('/reserve-book/<int:book_id>', methods=['POST'])
    @login_required
    @student_required
    def reserve_book(book_id):
        """Reserve a book"""
        book = Book.query.get_or_404(book_id)
        
        # Check if book is available for reservation
        if book.available > 0:
            flash('This book is currently available for issue. No need to reserve.', 'info')
            return redirect(url_for('books_list'))
        
        # Check if user already has an active reservation for this book
        existing_reservation = BookReservation.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            status='active'
        ).first()
        
        if existing_reservation:
            flash('You already have an active reservation for this book.', 'warning')
            return redirect(url_for('books_list'))
        
        # Check if user already has this book issued
        issued_book = IssuedBook.query.filter_by(
            book_id=book_id,
            user_id=current_user.id,
            is_returned=False
        ).first()
        
        if issued_book:
            flash('You already have this book issued.', 'warning')
            return redirect(url_for('books_list'))
        
        # Create reservation
        expiry_date = datetime.utcnow() + timedelta(days=7)  # Reservation expires in 7 days
        reservation = BookReservation(
            book_id=book_id,
            user_id=current_user.id,
            expiry_date=expiry_date,
            notes=f'Reserved by {current_user.name}'
        )
        
        db.session.add(reservation)
        db.session.commit()
        
        flash(f'Book "{book.title}" has been reserved successfully! Reservation expires on {expiry_date.strftime("%Y-%m-%d")}.', 'success')
        return redirect(url_for('books_list'))
    
    @app.route('/cancel-reservation/<int:reservation_id>', methods=['POST'])
    @login_required
    @student_required
    def cancel_reservation(reservation_id):
        """Cancel a reservation"""
        reservation = BookReservation.query.get_or_404(reservation_id)
        
        # Check if reservation belongs to current user
        if reservation.user_id != current_user.id:
            flash('You can only cancel your own reservations.', 'error')
            return redirect(url_for('my_reservations'))
        
        # Check if reservation is still active
        if reservation.status != 'active':
            flash('This reservation cannot be cancelled.', 'error')
            return redirect(url_for('my_reservations'))
        
        reservation.cancel_reservation()
        db.session.commit()
        
        flash(f'Reservation for "{reservation.book.title}" has been cancelled.', 'success')
        return redirect(url_for('my_reservations'))
    
    @app.route('/my-reservations')
    @login_required
    @student_required
    def my_reservations():
        """View student's reservations"""
        reservations = BookReservation.query.filter_by(user_id=current_user.id).order_by(desc(BookReservation.created_at)).all()
        
        # Separate reservations by status
        active_reservations = [r for r in reservations if r.status == 'active']
        fulfilled_reservations = [r for r in reservations if r.status == 'fulfilled']
        cancelled_reservations = [r for r in reservations if r.status == 'cancelled']
        other_reservations = [r for r in reservations if r.status not in ['active']]
        
        return render_template('my_reservations.html', 
                             reservations=reservations,
                             active_reservations=active_reservations,
                             other_reservations=other_reservations,
                             fulfilled_reservations=fulfilled_reservations,
                             cancelled_reservations=cancelled_reservations)
    
    @app.route('/request-book', methods=['GET', 'POST'])
    @login_required
    @student_required
    def request_book():
        """Request a new book for the library"""
        if request.method == 'POST':
            book_title = request.form.get('book_title', '').strip()
            author = request.form.get('author', '').strip()
            isbn = request.form.get('isbn', '').strip()
            category = request.form.get('category', '').strip()
            reason = request.form.get('reason', '').strip()
            
            if not book_title:
                flash('Book title is required.', 'error')
                return redirect(url_for('request_book'))
            
            # Check if book already exists in library (exact title match or ISBN match)
            existing_book = Book.query.filter(
                db.or_(
                    Book.title.ilike(book_title),  # Exact title match (case-insensitive)
                    Book.isbn == isbn if isbn else False
                )
            ).first()
            
            if existing_book:
                flash(f'This book already exists in the library: "{existing_book.title}"', 'warning')
                return redirect(url_for('books_list'))
            
            # Check if user already requested this book
            existing_request = BookRequest.query.filter_by(
                user_id=current_user.id,
                book_title=book_title,
                status='pending'
            ).first()
            
            if existing_request:
                flash('You already have a pending request for this book.', 'warning')
                return redirect(url_for('books_list'))
            
            # Create book request
            book_request = BookRequest(
                user_id=current_user.id,
                book_title=book_title,
                author=author,
                isbn=isbn,
                reason=reason
            )
            
            db.session.add(book_request)
            
            # Create notification for all admins
            admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
            for admin in admin_users:
                notification = Notification(
                    user_id=admin.id,
                    title='New Book Request',
                    message=f'{current_user.name} has requested a new book: "{book_title}" by {author}. Please review and approve/reject.'
                )
                db.session.add(notification)
            
            db.session.commit()
            
            flash(f'Book request for "{book_title}" has been submitted successfully!', 'success')
            return redirect(url_for('books_list'))
        
        return render_template('request_book.html')
    
    @app.route('/request-book/<int:book_id>', methods=['POST'])
    @login_required
    @student_required
    def request_existing_book(book_id):
        """Request an existing book from the library"""
        book = Book.query.get_or_404(book_id)
        
        # Allow requests for all books (available and unavailable) to go to admin for approval
        
        # Check if user already has an active reservation for this book
        existing_reservation = BookReservation.query.filter_by(
            user_id=current_user.id,
            book_id=book_id,
            status='active'
        ).first()
        
        if existing_reservation:
            flash('You already have an active reservation for this book.', 'warning')
            return redirect(url_for('books_list'))
        
        # Check if user already has this book issued
        issued_book = IssuedBook.query.filter_by(
            user_id=current_user.id,
            book_id=book_id,
            is_returned=False
        ).first()
        
        if issued_book:
            flash('You already have this book issued.', 'warning')
            return redirect(url_for('books_list'))
        
        # Check if user already requested this book
        existing_request = BookRequest.query.filter_by(
            user_id=current_user.id,
            book_title=book.title,
            status='pending'
        ).first()
        
        if existing_request:
            flash('You already have a pending request for this book.', 'warning')
            return redirect(url_for('books_list'))
        
        # Create book request
        book_request = BookRequest(
            user_id=current_user.id,
            book_title=book.title,
            author=book.author,
            isbn=book.isbn,
            reason='Student requested book from library catalog',
            status='pending'
        )
        
        db.session.add(book_request)
        
        # Create notification for all admins
        admin_users = User.query.filter_by(role=UserRole.ADMIN).all()
        for admin in admin_users:
            notification = Notification(
                user_id=admin.id,
                title='New Book Request',
                message=f'{current_user.name} has requested an existing book: "{book.title}" by {book.author}. Please review and approve/reject.'
            )
            db.session.add(notification)
        
        db.session.commit()
        
        flash(f'Book request for "{book.title}" has been submitted successfully!', 'success')
        return redirect(url_for('books_list'))
    
    @app.route('/my-requests')
    @login_required
    @student_required
    def my_requests():
        """View student's book requests"""
        requests = BookRequest.query.filter_by(user_id=current_user.id).order_by(desc(BookRequest.created_at)).all()
        
        # Separate requests by status
        pending_requests = [r for r in requests if r.status == 'pending']
        approved_requests = [r for r in requests if r.status == 'approved']
        rejected_requests = [r for r in requests if r.status == 'rejected']
        other_requests = [r for r in requests if r.status not in ['pending']]
        
        return render_template('my_requests.html', 
                             requests=requests,
                             pending_requests=pending_requests,
                             other_requests=other_requests,
                             approved_requests=approved_requests,
                             rejected_requests=rejected_requests)
    
    @app.route('/admin/reservations')
    @login_required
    @admin_required
    def admin_reservations():
        """View all book reservations (admin only)"""
        reservations = BookReservation.query.order_by(desc(BookReservation.created_at)).all()
        
        # Separate reservations by status
        active_reservations = [r for r in reservations if r.status == 'active']
        fulfilled_reservations = [r for r in reservations if r.status == 'fulfilled']
        cancelled_reservations = [r for r in reservations if r.status == 'cancelled']
        expired_reservations = [r for r in reservations if r.status == 'expired']
        
        return render_template('admin_reservations.html', 
                             reservations=reservations,
                             active_reservations=active_reservations,
                             fulfilled_reservations=fulfilled_reservations,
                             cancelled_reservations=cancelled_reservations,
                             expired_reservations=expired_reservations)
    
    @app.route('/admin/requests')
    @login_required
    @admin_required
    def admin_requests():
        """View all book requests (admin only)"""
        requests = BookRequest.query.order_by(desc(BookRequest.created_at)).all()
        
        # Separate requests by status
        pending_requests = [r for r in requests if r.status == 'pending']
        approved_requests = [r for r in requests if r.status == 'approved']
        rejected_requests = [r for r in requests if r.status == 'rejected']
        
        return render_template('admin_requests.html', 
                             requests=requests,
                             pending_requests=pending_requests,
                             approved_requests=approved_requests,
                             rejected_requests=rejected_requests)
    
    @app.route('/admin/fulfill-reservation/<int:reservation_id>', methods=['POST'])
    @login_required
    @admin_required
    def fulfill_reservation(reservation_id):
        """Fulfill a reservation (admin only)"""
        reservation = BookReservation.query.get_or_404(reservation_id)
        
        if reservation.status != 'active':
            flash('Only active reservations can be fulfilled.', 'error')
            return redirect(url_for('admin_reservations'))
        
        reservation.mark_as_fulfilled()
        db.session.commit()
        
        flash(f'Reservation for "{reservation.book.title}" has been fulfilled.', 'success')
        return redirect(url_for('admin_reservations'))
    
    @app.route('/admin/approve-request/<int:request_id>', methods=['POST'])
    @login_required
    @admin_required
    def approve_request(request_id):
        """Approve a book request (admin only)"""
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'pending':
            flash('Only pending requests can be approved.', 'error')
            return redirect(url_for('admin_requests'))
        
        notes = request.form.get('admin_notes', '')
        
        # Check if book exists and is available
        book = None
        if book_request.isbn:
            book = Book.query.filter_by(isbn=book_request.isbn).first()
        if not book:
            book = Book.query.filter(db.or_(
                Book.title.ilike(book_request.book_title),
                Book.title.ilike(f'%{book_request.book_title}%')
            )).first()
        
        if not book:
            flash(f'Book "{book_request.book_title}" not found in library. Please add the book first.', 'warning')
            book_request.status = 'approved'  # Mark as approved but not issued
            if notes:
                book_request.admin_notes = notes
            book_request.admin_notes += '\n\nNote: Book not found in library. Please add book before issuing.'
            db.session.commit()
            return redirect(url_for('admin_requests'))
        
        if book.available <= 0:
            flash(f'Book "{book.title}" is not available for issue. All copies are currently issued.', 'warning')
            book_request.status = 'approved'  # Mark as approved but not issued
            if notes:
                book_request.admin_notes = notes
            book_request.admin_notes += '\n\nNote: Book not available for issue. No copies available.'
            db.session.commit()
            return redirect(url_for('admin_requests'))
        
        # Create issued book entry
        issued_book = IssuedBook(
            user_id=book_request.user_id,
            book_id=book.id,
            issue_date=datetime.utcnow(),
            due_date=datetime.utcnow() + timedelta(days=14),  # Default 14 days
            notes=f'Auto-issued from approved book request: {book_request.reason}'
        )
        
        # Update book availability
        book.available -= 1
        
        # Update request status
        book_request.status = 'approved'
        if notes:
            book_request.admin_notes = notes + f'\n\nAuto-issued to {book_request.user.name} on {datetime.utcnow().strftime("%Y-%m-%d")}'
        else:
            book_request.admin_notes = f'Auto-issued to {book_request.user.name} on {datetime.utcnow().strftime("%Y-%m-%d")}'
        
        # Create notification for user
        notification = Notification(
            user_id=book_request.user_id,
            title='Book Request Approved',
            message=f'Your book request for "{book_request.book_title}" has been approved and issued to you!',
            type='success'
        )
        db.session.add(notification)
        
        db.session.add(issued_book)
        db.session.add(book)
        db.session.commit()
        
        flash(f'Book request for "{book_request.book_title}" approved and issued to {book_request.user.name}!', 'success')
        return redirect(url_for('admin_requests'))
    
    @app.route('/admin/reject-request/<int:request_id>', methods=['POST'])
    @login_required
    @admin_required
    def reject_request(request_id):
        """Reject a book request (admin only)"""
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'pending':
            flash('Only pending requests can be rejected.', 'error')
            return redirect(url_for('admin_requests'))
        
        notes = request.form.get('admin_notes', '')
        book_request.reject_request(notes=notes)
        
        # Create notification for user
        notification = Notification(
            user_id=book_request.user_id,
            title='Book Request Rejected',
            message=f'Your book request for "{book_request.book_title}" has been rejected.',
            type='error'
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash(f'Book request for "{book_request.book_title}" has been rejected.', 'success')
        return redirect(url_for('admin_requests'))
    
    # ==================== USER MANAGEMENT ROUTES ====================
    
    @app.route('/users')
    @login_required
    @admin_required
    def users_list():
        """List all users"""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str).strip()
        
        query = User.query
        
        # Handle filter parameter
        filter_type = request.args.get('filter', '')
        status_filter = request.args.get('status', '')
        
        if search:
            # Check if search is an exact name match first
            exact_user = User.query.filter(
                db.or_(
                    User.name == search,
                    User.email == search,
                    User.roll_number == search
                )
            ).first()
            
            if exact_user:
                # If exact match found, show only that user
                query = User.query.filter(
                    db.or_(
                        User.name == search,
                        User.email == search,
                        User.roll_number == search
                    )
                )
            else:
                # Otherwise, use partial match
                query = query.filter(
                    db.or_(
                        User.name.ilike(f'%{search}%'),
                        User.email.ilike(f'%{search}%'),
                        User.roll_number.ilike(f'%{search}%')
                    )
                )
        
        # Apply role filter
        if filter_type:
            if filter_type == 'student' or filter_type == 'students':
                query = query.filter_by(role=UserRole.STUDENT)
            elif filter_type == 'admin':
                query = query.filter_by(role=UserRole.ADMIN)
        
        # Apply status filter
        if status_filter:
            if status_filter == 'active':
                query = query.filter_by(is_active=True)
            elif status_filter == 'inactive':
                query = query.filter_by(is_active=False)
        
        pagination = query.paginate(page=page, per_page=10)
        users = pagination.items
        
        # Calculate statistics
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        student_count = User.query.filter_by(role=UserRole.STUDENT).count()
        admin_count = User.query.filter_by(role=UserRole.ADMIN).count()
        
        return render_template(
            'users.html',
            users=users,
            pagination=pagination,
            search=search,
            total_users=total_users,
            active_users=active_users,
            student_count=student_count,
            admin_count=admin_count
        )
    
    @app.route('/users/<int:user_id>/deactivate', methods=['POST'])
    @login_required
    @admin_required
    def deactivate_user(user_id):
        """Deactivate user account"""
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            flash('You cannot deactivate your own account.', 'danger')
            return redirect(url_for('users_list'))
        
        try:
            user.is_active = False
            db.session.commit()
            flash(f'User {user.name} has been deactivated successfully.', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error deactivating user: {str(e)}', 'danger')
        
        return redirect(url_for('users_list'))    
    
    @app.route('/users/<int:user_id>/activate', methods=['POST'])
    @login_required
    @admin_required
    def activate_user(user_id):
        """Activate user account"""
        user = User.query.get_or_404(user_id)
        
        if user.id == current_user.id:
            flash('You cannot activate your own account.', 'danger')
            return redirect(url_for('users_list'))
        
        try:
            user.is_active = True
            db.session.commit()
            flash(f'User {user.name} has been activated successfully.', 'success')
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error activating user: {str(e)}', 'danger')
        
        return redirect(url_for('users_list'))    
    # ==================== REPORTS ROUTES ====================
    
    @app.route('/reports')
    @login_required
    @admin_required
    def reports():
        """Generate and view reports"""
        
        # Calculate library statistics
        total_books = Book.query.count()
        total_users = User.query.count()
        total_issues = IssuedBook.query.filter_by(is_returned=False).count()
        total_fines = Fine.query.filter_by(is_paid=False).count()
        
        # Overdue books report
        overdue_books = IssuedBook.query.filter(
            and_(
                IssuedBook.is_returned == False,
                IssuedBook.due_date < datetime.utcnow()
            )
        ).order_by(desc(IssuedBook.due_date)).all()
        
        # Outstanding fines report
        outstanding_fines = Fine.query.filter_by(is_paid=False).all()
        total_outstanding = sum(f.amount for f in outstanding_fines)
        
        # Book statistics
        most_issued = db.session.query(
            Book.title,
            func.count(IssuedBook.id).label('count')
        ).join(IssuedBook).group_by(Book.id).order_by(
            desc('count')
        ).limit(10).all()
        
        return render_template(
            'reports.html',
            total_books=total_books,
            total_users=total_users,
            total_issues=total_issues,
            total_fines=total_fines,
            overdue_books=overdue_books,
            outstanding_fines=outstanding_fines,
            total_outstanding=total_outstanding,
            most_issued=most_issued
        )
    
    @app.route('/reports/generate')
    @login_required
    @admin_required
    def generate_report():
        """Generate and download reports"""
        try:
            # Get report parameters
            report_type = request.args.get('type')
            date_from = request.args.get('date_from')
            date_to = request.args.get('date_to')
            
            if not report_type or not date_from or not date_to:
                return jsonify({
                    'success': False,
                    'message': 'Missing required parameters'
                }), 400
            
            # Parse dates
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD format.'
                }), 400
            
            # Generate report based on type
            if report_type == 'books':
                # Books report
                books = Book.query.filter(
                    Book.created_at.between(from_date, to_date)
                ).all()
                
                # Create simple text report for now (PDF generation requires additional dependencies)
                filename = f"books_report_{date_from}_to_{date_to}.txt"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"BOOKS REPORT ({date_from} to {date_to})\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, book in enumerate(books, 1):
                        f.write(f"{i}. Title: {book.title}\n")
                        f.write(f"   Author: {book.author}\n")
                        f.write(f"   ISBN: {book.isbn}\n")
                        f.write(f"   Category: {book.category or 'N/A'}\n")
                        f.write(f"   Available: {'Yes' if book.quantity > 0 else 'No'}\n")
                        f.write("-" * 30 + "\n")
                
                return jsonify({
                    'success': True,
                    'download_url': f"/static/reports/{filename}"
                })
                
            elif report_type == 'users':
                # Users report
                users = User.query.filter(
                    User.created_at.between(from_date, to_date)
                ).all()
                
                # Create simple text report
                filename = f"users_report_{date_from}_to_{date_to}.txt"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"USERS REPORT ({date_from} to {date_to})\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, user in enumerate(users, 1):
                        f.write(f"{i}. Name: {user.name}\n")
                        f.write(f"   Email: {user.email}\n")
                        f.write(f"   Roll Number: {user.roll_number or 'N/A'}\n")
                        f.write(f"   Role: {user.role.value if hasattr(user.role, 'value') else str(user.role)}\n")
                        f.write(f"   Contact: {user.contact or 'N/A'}\n")
                        f.write("-" * 30 + "\n")
                
                return jsonify({
                    'success': True,
                    'download_url': f"/static/reports/{filename}"
                })
                
            elif report_type == 'issues':
                # Issues report
                issues = IssuedBook.query.filter(
                    IssuedBook.issue_date.between(from_date, to_date)
                ).all()
                
                filename = f"issues_report_{date_from}_to_{date_to}.txt"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"BOOK ISSUES REPORT ({date_from} to {date_to})\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, issue in enumerate(issues, 1):
                        f.write(f"{i}. Book: {issue.book.title if issue.book else 'N/A'}\n")
                        f.write(f"   User: {issue.user.name if issue.user else 'N/A'}\n")
                        f.write(f"   Issue Date: {issue.issue_date.strftime('%Y-%m-%d') if issue.issue_date else 'N/A'}\n")
                        f.write(f"   Due Date: {issue.due_date.strftime('%Y-%m-%d') if issue.due_date else 'N/A'}\n")
                        f.write(f"   Status: {'Returned' if issue.is_returned else 'Issued'}\n")
                        f.write("-" * 30 + "\n")
                
                return jsonify({
                    'success': True,
                    'download_url': f"/static/reports/{filename}"
                })
                
            elif report_type == 'fines':
                # Fines report
                fines = Fine.query.filter(
                    Fine.created_at.between(from_date, to_date)
                ).all()
                
                filename = f"fines_report_{date_from}_to_{date_to}.txt"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"FINES REPORT ({date_from} to {date_to})\n")
                    f.write("=" * 50 + "\n\n")
                    
                    for i, fine in enumerate(fines, 1):
                        f.write(f"{i}. User: {fine.user.name if fine.user else 'N/A'}\n")
                        f.write(f"   Book: {fine.book.title if fine.book else 'N/A'}\n")
                        f.write(f"   Amount: Rs. {fine.amount}\n")
                        f.write(f"   Status: {'Paid' if fine.is_paid else 'Unpaid'}\n")
                        f.write(f"   Date: {fine.created_at.strftime('%Y-%m-%d') if fine.created_at else 'N/A'}\n")
                        f.write("-" * 30 + "\n")
                
                return jsonify({
                    'success': True,
                    'download_url': f"/static/reports/{filename}"
                })
                
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid report type'
                }), 400
                
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Error generating report: {str(e)}'
            }), 500
    
    # ==================== ERROR HANDLERS ====================
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(error):
        """Handle 500 errors"""
        db.session.rollback()
        return render_template('500.html'), 500
    
    # ==================== CONTEXT PROCESSORS ====================
    
    @app.context_processor
    def inject_config():
        """Inject configuration into templates"""
        return dict(
            app_name='Library Management System',
            app_version='1.0.0'
        )
    
    @app.context_processor
    def inject_unread_count():
        """Inject unread notification count into templates"""
        if current_user.is_authenticated:
            unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            return dict(unread_count=unread_count)
        return dict(unread_count=0)
    
    # ==================== SOCKETIO EVENT HANDLERS ====================
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        print(f'Client connected: {request.sid}')
        emit('connected', {'status': 'success'})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        print(f'Client disconnected: {request.sid}')
    
    @socketio.on('join_dashboard')
    def handle_join_dashboard():
        """Join dashboard room for real-time updates"""
        if current_user.is_authenticated:
            join_room(f'dashboard_{current_user.id}')
            emit('joined_room', {'room': f'dashboard_{current_user.id}'})
    
    @socketio.on('join_books')
    def handle_join_books():
        """Join books room for real-time book updates"""
        join_room('books')
        emit('joined_room', {'room': 'books'})
    
    @socketio.on('join_notifications')
    def handle_join_notifications():
        """Join notifications room"""
        if current_user.is_authenticated:
            join_room(f'notifications_{current_user.id}')
            emit('joined_room', {'room': f'notifications_{current_user.id}'})
    
    @socketio.on('request_dashboard_stats')
    def handle_dashboard_stats_request():
        """Send current dashboard statistics"""
        if not current_user.is_authenticated:
            return
        
        total_books = Book.query.count()
        total_users = User.query.count()
        issued_books = IssuedBook.query.filter_by(is_returned=False).count()
        overdue_books = IssuedBook.query.filter(
            and_(
                IssuedBook.is_returned == False,
                IssuedBook.due_date < datetime.utcnow()
            )
        ).count()
        
        # User-specific stats
        user_stats = {}
        if current_user.role == UserRole.STUDENT:
            user_stats = {
                'issued': IssuedBook.query.filter_by(
                    user_id=current_user.id,
                    is_returned=False
                ).count(),
                'overdue': IssuedBook.query.filter(
                    and_(
                        IssuedBook.user_id == current_user.id,
                        IssuedBook.is_returned == False,
                        IssuedBook.due_date < datetime.utcnow()
                    )
                ).count(),
                'fines': current_user.get_total_fines()
            }
        
        emit('dashboard_stats_update', {
            'total_books': total_books,
            'total_users': total_users,
            'issued_books': issued_books,
            'overdue_books': overdue_books,
            'user_stats': user_stats
        })
    
    @socketio.on('send_notification')
    def handle_send_notification(data):
        """Send notification to specific user"""
        if not current_user.is_authenticated or current_user.role != UserRole.ADMIN:
            return
        
        target_user_id = data.get('user_id')
        message = data.get('message')
        notification_type = data.get('type', 'info')
        
        if target_user_id and message:
            # Save notification to database
            notification = Notification(
                user_id=target_user_id,
                message=message,
                type=notification_type
            )
            db.session.add(notification)
            db.session.commit()
            
            # Emit to user's notification room
            emit('notification', {
                'id': notification.id,
                'message': message,
                'type': notification_type,
                'timestamp': notification.created_at.isoformat()
            }, room=f'notifications_{target_user_id}')
    
    return app


def url_has_no_scheme(url):
    """Check if URL has no scheme for security"""
    return not url.startswith(('http://', 'https://', '//'))


if __name__ == '__main__':
    app = create_app('development')
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
