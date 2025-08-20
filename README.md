# School Library Management API

A comprehensive School Library Management System built with FastAPI, demonstrating **Dependency Injection**, **Async Endpoints**, **Modular Architecture**, and **Router Setup**.

## 🎯 Learning Objectives

This project demonstrates:
- **Dependency Injection (DI)** - Clean service injection pattern
- **Async Operations** - Non-blocking I/O for better performance
- **Modular Architecture** - Separated concerns with clean code structure
- **Router Setup** - Organized API endpoints
- **Built-in Services** - SQLite, LRU Cache, Mock Email

## 🏗️ Architecture

```
├── main.py                 # FastAPI app entry point
├── dependencies.py         # Dependency injection setup
├── models.py              # Pydantic models
├── services/              # Service layer
│   ├── database_service.py    # SQLite database operations
│   ├── cache_service.py       # LRU cache implementation
│   └── email_service.py       # Mock email service
└── routers/               # API routes
    ├── books.py              # Book operations
    ├── students.py           # Student management
    └── borrow.py             # Borrowing transactions
```

## 🚀 Features

### Core Services (Dependency Injection)
- **Database Service**: SQLite with async operations
- **Cache Service**: LRU cache for performance optimization
- **Email Service**: Mock email notifications

### API Endpoints

#### 📚 Books (`/api/books/`)
- `GET /` - List all books
- `GET /search` - **Async search** across multiple categories
- `GET /{book_id}` - Get book details
- `POST /` - Create new book
- `PUT /{book_id}` - Update book
- `GET /{book_id}/availability` - Check availability
- `GET /category/{category}` - Books by category
- `GET /stats/summary` - Book statistics

#### 👨‍🎓 Students (`/api/students/`)
- `GET /` - List all students
- `GET /{student_id}` - Get student details
- `POST /` - Create new student (with welcome email)
- `PUT /{student_id}` - Update student
- `GET /{student_id}/borrowed-books` - Current borrowed books
- `GET /{student_id}/fines` - Outstanding fines
- `POST /{student_id}/send-notification` - Send email notification

#### 📖 Borrowing (`/api/borrow/`)
- `POST /` - Borrow a book (with confirmation email)
- `GET /{borrow_id}` - Get borrow record
- `PUT /{borrow_id}/return` - Return book (with fine calculation)
- `GET /fines/calculate` - **Async fine calculation** for overdue books
- `POST /fines/send-notices` - Send overdue notices
- `GET /overdue` - List overdue books
- `PUT /{borrow_id}/extend` - Extend due date

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.8+
- pip

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Amruth22/D1W3S2-DI-implementation.git
cd D1W3S2-DI-implementation
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python main.py
```

Or using uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Access the API**
- API Documentation: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

## 📊 Sample Data

The application automatically creates sample data on first run:

### Books
- The Great Gatsby (Fiction)
- To Kill a Mockingbird (Fiction)
- 1984 (Fiction)
- A Brief History of Time (Science)
- Clean Code (Technology)

### Students
- Alice Johnson (Grade 10)
- Bob Smith (Grade 11)
- Carol Davis (Grade 9)
- David Wilson (Grade 12)

## 🔧 Key Implementation Details

### 1. Dependency Injection Pattern

```python
# dependencies.py
def get_database_service() -> DatabaseService:
    return main.database_service

# Usage in routers
@router.get("/")
async def get_books(
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    # Service automatically injected
```

### 2. Async Operations

```python
# Async book search across categories
async def search_books_async():
    search_tasks = []
    for category in categories:
        search_tasks.append(db.search_books(category=category))
    
    # Execute concurrently
    results = await asyncio.gather(*search_tasks)
```

### 3. LRU Cache Implementation

```python
# Built-in LRU cache with TTL
cache_service = CacheService(max_size=100)
await cache_service.set("key", value, ttl=300)
cached_value = await cache_service.get("key")
```

### 4. Mock Email Service

```python
# Console-based email simulation
await email_service.send_overdue_notice(
    student_email="student@school.edu",
    student_name="John Doe",
    book_title="Sample Book",
    fine_amount=5.0
)
```

## 🧪 Testing the API

### 1. Create a Student
```bash
curl -X POST "http://localhost:8000/api/students/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@school.edu",
    "student_id": "STU005",
    "grade": "Grade 10"
  }'
```

### 2. Search Books
```bash
curl "http://localhost:8000/api/books/search?query=gatsby&category=fiction"
```

### 3. Borrow a Book
```bash
curl -X POST "http://localhost:8000/api/borrow/" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": 1,
    "book_id": 1,
    "due_date": "2024-02-15"
  }'
```

### 4. Calculate Fines
```bash
curl "http://localhost:8000/api/borrow/fines/calculate?fine_per_day=1.5"
```

## 📈 Performance Features

- **Async Operations**: Non-blocking I/O for better concurrency
- **LRU Caching**: Reduces database queries
- **Concurrent Processing**: Parallel fine calculations and searches
- **Connection Pooling**: Efficient database connections

## 🎓 Educational Value

This project is designed for students to understand:

1. **Clean Architecture**: Separation of concerns
2. **Dependency Injection**: Loose coupling between components
3. **Async Programming**: Handling concurrent operations
4. **Caching Strategies**: Performance optimization
5. **API Design**: RESTful endpoints with proper HTTP methods
6. **Error Handling**: Proper exception management
7. **Documentation**: Auto-generated API docs with FastAPI

## 🔍 Code Structure Explanation

### Services Layer
- **DatabaseService**: Handles all database operations with async support
- **CacheService**: LRU cache implementation for performance
- **EmailService**: Mock email service for notifications

### Models Layer
- **Pydantic Models**: Data validation and serialization
- **Enums**: Type-safe constants for categories and statuses

### Routers Layer
- **Modular Routes**: Each domain has its own router
- **Dependency Injection**: Services injected into endpoints
- **Async Endpoints**: Non-blocking operations where beneficial

## 🚀 Next Steps

To extend this project:

1. Add authentication and authorization
2. Implement real database with migrations
3. Add comprehensive logging
4. Create unit and integration tests
5. Add rate limiting
6. Implement real email service
7. Add book reservations
8. Create admin dashboard

## 📝 License

This project is created for educational purposes. Feel free to use and modify as needed.

## 🤝 Contributing

This is an educational project. Students are encouraged to:
1. Fork the repository
2. Add new features
3. Improve existing code
4. Submit pull requests

---

**Happy Learning! 🎓**