# Library Management System - Real-time Web Application

A modern, real-time library management system built with Flask and SocketIO.

## Features

### Real-time Functionality
- **Live Dashboard Updates**: Statistics update automatically without page refresh
- **Real-time Book Management**: Instant notifications when books are added, issued, or returned
- **Live Notifications**: Users receive instant notifications for important events
- **Real-time Availability**: Book availability updates immediately across all connected clients

### Core Features
- User authentication and authorization (Admin/Student roles)
- Book inventory management with categories and search
- Book issuing and returning system
- Fine calculation for overdue books
- User management (Admin only)
- Reports and analytics with downloadable text reports
- Book reservation system
- Book renewal requests
- Profile management
- Responsive design with modern UI

### Advanced Features
- **Book Reservations**: Students can reserve books that are currently issued
- **Renewal System**: Students can request book renewals, admins approve/reject
- **Fine Management**: Automatic fine calculation and payment tracking
- **Admin Notes**: Admins can add notes when approving/rejecting requests
- **Activity Tracking**: Recent activity feed showing all library operations
- **Filtering & Search**: Advanced filtering for books, issues, and requests
- **Dashboard Statistics**: Real-time charts and metrics

## Real-time Events

### Server Events
- `book_added`: Emitted when a new book is added to the system
- `book_issued`: Emitted when a book is issued to a student
- `book_returned`: Emitted when a book is returned
- `book_deleted`: Emitted when a book is removed from the system
- `stats_changed`: Emitted when dashboard statistics change
- `notification`: Emitted to send notifications to specific users

### Client Events
- `join_dashboard`: Join dashboard room for stats updates
- `join_books`: Join books room for book-related updates
- `join_notifications`: Join notifications room
- `request_dashboard_stats`: Request current dashboard statistics

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd library-management-system
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Initialize database:
```bash
python init_database.py
```

5. Run the application:
```bash
python app.py
```

6. Access the application at `http://127.0.0.1:5000`

## Default Admin Account
- Email: admin@library.com
- Password: admin123

## Project Structure
```
library-management-system/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── database.py            # Database models
├── init_database.py       # Database initialization script
├── requirements.txt       # Python dependencies
├── static/               # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── templates/            # HTML templates
└── instance/            # Instance-specific files (database)
```

## Real-time Architecture

The application uses Flask-SocketIO for real-time communication:

- **WebSocket Connection**: Clients establish WebSocket connections for real-time updates
- **Room-based Messaging**: Users join specific rooms (dashboard, books, notifications) to receive targeted updates
- **Event-driven Updates**: Database changes trigger SocketIO events that update connected clients instantly
- **Fallback Notifications**: Toast notifications appear for important events

## Technologies Used

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-WTF
- **Real-time**: Flask-SocketIO, Socket.IO client
- **Frontend**: HTML5, CSS3, Bootstrap 5, JavaScript
- **Database**: SQLite (development) / PostgreSQL (production)

## Real-time Features in Action

1. **Dashboard**: Statistics update every 30 seconds automatically, or instantly when data changes
2. **Book Management**: When books are issued/returned, all connected clients see availability updates
3. **Notifications**: Users receive instant notifications for book-related activities
4. **Multi-user Support**: Multiple users can work simultaneously with real-time synchronization

## User Roles & Permissions

### Admin Features
- Add, edit, and delete books
- Issue and return books
- Manage users (view, edit roles)
- Generate reports (books, users, issues, fines)
- Approve/reject book requests and renewals
- View all library statistics and analytics
- Manage book reservations
- Add admin notes to requests

### Student Features
- Browse and search books
- View book details and availability
- Reserve unavailable books
- Request book renewals
- View issued books and due dates
- Pay fines online
- View personal dashboard
- Manage profile settings

## Available Pages & Routes

### Authentication
- `/` - Home/Redirect
- `/login` - User login
- `/register` - User registration
- `/logout` - User logout

### Dashboard & Profile
- `/dashboard` - Main dashboard (role-based)
- `/profile` - User profile management
- `/settings` - User settings

### Book Management
- `/books` - Book list with search and filters
- `/books/add` - Add new book (Admin only)
- `/book/<id>` - Book details
- `/books/<id>/edit` - Edit book (Admin only)
- `/books/<id>/delete` - Delete book (Admin only)

### Issue & Return
- `/issue-return` - Issue/return books (Admin only)
- `/my-books` - View issued books (Student)
- `/reserve-book/<id>` - Reserve book (Student)

### Reports & Analytics
- `/reports` - Generate and download reports
- `/api/dashboard-stats` - Dashboard statistics API

### Other Features
- `/fines` - View and pay fines (Student)
- `/notifications` - View notifications
- `/admin/requests` - Admin requests management
- `/renewal-requests` - Book renewal requests

## Database Models

The system uses the following main models:
- **User**: Authentication and user management
- **Book**: Book inventory and details
- **IssuedBook**: Book issue/return tracking
- **Fine**: Fine calculation and payment
- **BookReservation**: Book reservation system
- **BookRenewal**: Book renewal requests
- **Notification**: User notifications

## Configuration

The application supports different environments:
- **Development**: SQLite database, debug mode
- **Testing**: In-memory database
- **Production**: PostgreSQL database (configurable)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
