# Library Management System

A Python library management system with both web and command-line interfaces. Shows object-oriented programming, database management, and full-stack development skills.

## 🚀 Features

- **User Management**: Support for members and librarians with different access levels
- **Book Inventory**: Add, remove, and update books in the catalog
- **Borrowing System**: Check out and return books with automatic tracking
- **Loan Limits**: 5-book borrowing limit per member
- **Web Interface**: Modern Streamlit-based UI
- **Command-Line Interface**: Terminal application with ASCII art
- **Database**: MySQL integration with data validation

## 🛠️ Tech Stack

- **Backend**: Python 3.x
- **Web Framework**: Streamlit
- **Database**: MySQL
- **Data Processing**: Pandas, NumPy

## 🚀 Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up MySQL database**
   - Create database named `library_system`
   - Set environment variables for DB connection

3. **Run the application**
   ```bash
   # Command-line interface
   python main.py
   ```

## 📊 Database Schema

Three main tables:
- **`users`**: User information (name, user type)
- **`books`**: Book inventory (title, author, quantity)
- **`borrowed_books`**: Active book loans (user, book, date borrowed)


## 📝 Future Enhancements

- Due date tracking and overdue notifications
- Book reservation system
- Better search and filtering
- Data analytics dashboard
