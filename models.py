"""
Pydantic Models for API Data Validation
Simple models for books, students, and borrowing operations
"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

class BookCategory(str, Enum):
    """Book categories enum"""
    FICTION = "fiction"
    NON_FICTION = "non_fiction"
    SCIENCE = "science"
    HISTORY = "history"
    BIOGRAPHY = "biography"
    TECHNOLOGY = "technology"

class BookStatus(str, Enum):
    """Book status enum"""
    AVAILABLE = "available"
    BORROWED = "borrowed"
    RESERVED = "reserved"

# Book Models
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: str = Field(..., min_length=1, max_length=100)
    isbn: str = Field(..., min_length=10, max_length=13)
    category: BookCategory
    publication_year: int = Field(..., ge=1000, le=2024)

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    author: Optional[str] = Field(None, min_length=1, max_length=100)
    category: Optional[BookCategory] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=2024)

class Book(BookBase):
    id: int
    status: BookStatus = BookStatus.AVAILABLE
    created_at: datetime
    updated_at: datetime

# Student Models
class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    student_id: str = Field(..., min_length=1, max_length=20)
    grade: str = Field(..., min_length=1, max_length=10)

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    grade: Optional[str] = Field(None, min_length=1, max_length=10)

class Student(StudentBase):
    id: int
    active: bool = True
    created_at: datetime
    updated_at: datetime

# Borrowing Models
class BorrowStatus(str, Enum):
    """Borrow status enum"""
    ACTIVE = "active"
    RETURNED = "returned"
    OVERDUE = "overdue"

class BorrowCreate(BaseModel):
    student_id: int
    book_id: int
    due_date: date

class BorrowUpdate(BaseModel):
    due_date: Optional[date] = None
    returned_date: Optional[date] = None

class Borrow(BaseModel):
    id: int
    student_id: int
    book_id: int
    borrow_date: date
    due_date: date
    returned_date: Optional[date] = None
    status: BorrowStatus
    fine_amount: float = 0.0
    created_at: datetime
    updated_at: datetime

# Search Models
class BookSearchQuery(BaseModel):
    query: Optional[str] = None
    category: Optional[BookCategory] = None
    author: Optional[str] = None
    status: Optional[BookStatus] = None

class BookSearchResult(BaseModel):
    books: List[Book]
    total_count: int
    search_time_ms: float

# Fine Calculation Models
class FineCalculation(BaseModel):
    borrow_id: int
    days_overdue: int
    fine_per_day: float = 1.0
    total_fine: float
    student_name: str
    book_title: str

class FineCalculationResult(BaseModel):
    fines: List[FineCalculation]
    total_fines: float
    calculation_time_ms: float