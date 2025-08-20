"""
SQLite Database Service
Simple database service using built-in SQLite with async operations
"""

import sqlite3
import asyncio
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import json

class DatabaseService:
    """Simple SQLite database service with async support"""
    
    def __init__(self, db_path: str = "library.db"):
        self.db_path = db_path
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def initialize(self):
        """Initialize database and create tables"""
        await self._execute_query("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                publication_year INTEGER NOT NULL,
                status TEXT DEFAULT 'available',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._execute_query("""
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                student_id TEXT UNIQUE NOT NULL,
                grade TEXT NOT NULL,
                active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        await self._execute_query("""
            CREATE TABLE IF NOT EXISTS borrows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                book_id INTEGER NOT NULL,
                borrow_date DATE NOT NULL,
                due_date DATE NOT NULL,
                returned_date DATE,
                status TEXT DEFAULT 'active',
                fine_amount REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students (id),
                FOREIGN KEY (book_id) REFERENCES books (id)
            )
        """)
        
        # Insert sample data if tables are empty
        await self._insert_sample_data()
    
    async def _execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute a query asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.executor, self._sync_execute_query, query, params)
    
    def _sync_execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Synchronous query execution"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            if query.strip().upper().startswith('SELECT'):
                return [dict(row) for row in cursor.fetchall()]
            else:
                conn.commit()
                return [{"lastrowid": cursor.lastrowid, "rowcount": cursor.rowcount}]
    
    async def _insert_sample_data(self):
        """Insert sample data if tables are empty"""
        # Check if books table is empty
        books = await self._execute_query("SELECT COUNT(*) as count FROM books")
        if books[0]["count"] == 0:
            sample_books = [
                ("The Great Gatsby", "F. Scott Fitzgerald", "9780743273565", "fiction", 1925),
                ("To Kill a Mockingbird", "Harper Lee", "9780061120084", "fiction", 1960),
                ("1984", "George Orwell", "9780451524935", "fiction", 1949),
                ("The Catcher in the Rye", "J.D. Salinger", "9780316769174", "fiction", 1951),
                ("A Brief History of Time", "Stephen Hawking", "9780553380163", "science", 1988),
                ("The Art of War", "Sun Tzu", "9781599869773", "history", -500),
                ("Steve Jobs", "Walter Isaacson", "9781451648539", "biography", 2011),
                ("Clean Code", "Robert Martin", "9780132350884", "technology", 2008)
            ]
            
            for book in sample_books:
                await self._execute_query(
                    "INSERT INTO books (title, author, isbn, category, publication_year) VALUES (?, ?, ?, ?, ?)",
                    book
                )
        
        # Check if students table is empty
        students = await self._execute_query("SELECT COUNT(*) as count FROM students")
        if students[0]["count"] == 0:
            sample_students = [
                ("Alice Johnson", "alice@school.edu", "STU001", "Grade 10"),
                ("Bob Smith", "bob@school.edu", "STU002", "Grade 11"),
                ("Carol Davis", "carol@school.edu", "STU003", "Grade 9"),
                ("David Wilson", "david@school.edu", "STU004", "Grade 12")
            ]
            
            for student in sample_students:
                await self._execute_query(
                    "INSERT INTO students (name, email, student_id, grade) VALUES (?, ?, ?, ?)",
                    student
                )
    
    # Book operations
    async def create_book(self, book_data: Dict) -> Dict:
        """Create a new book"""
        result = await self._execute_query(
            """INSERT INTO books (title, author, isbn, category, publication_year) 
               VALUES (?, ?, ?, ?, ?)""",
            (book_data["title"], book_data["author"], book_data["isbn"], 
             book_data["category"], book_data["publication_year"])
        )
        return await self.get_book_by_id(result[0]["lastrowid"])
    
    async def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """Get book by ID"""
        result = await self._execute_query("SELECT * FROM books WHERE id = ?", (book_id,))
        return result[0] if result else None
    
    async def search_books(self, query: str = None, category: str = None, 
                          author: str = None, status: str = None) -> List[Dict]:
        """Search books with filters"""
        sql = "SELECT * FROM books WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (title LIKE ? OR author LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        if author:
            sql += " AND author LIKE ?"
            params.append(f"%{author}%")
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        sql += " ORDER BY title"
        return await self._execute_query(sql, tuple(params))
    
    async def update_book(self, book_id: int, update_data: Dict) -> Optional[Dict]:
        """Update book"""
        set_clauses = []
        params = []
        
        for key, value in update_data.items():
            if value is not None:
                set_clauses.append(f"{key} = ?")
                params.append(value)
        
        if not set_clauses:
            return await self.get_book_by_id(book_id)
        
        params.append(datetime.now().isoformat())
        params.append(book_id)
        
        sql = f"UPDATE books SET {', '.join(set_clauses)}, updated_at = ? WHERE id = ?"
        await self._execute_query(sql, tuple(params))
        return await self.get_book_by_id(book_id)
    
    # Student operations
    async def create_student(self, student_data: Dict) -> Dict:
        """Create a new student"""
        result = await self._execute_query(
            """INSERT INTO students (name, email, student_id, grade) 
               VALUES (?, ?, ?, ?)""",
            (student_data["name"], student_data["email"], 
             student_data["student_id"], student_data["grade"])
        )
        return await self.get_student_by_id(result[0]["lastrowid"])
    
    async def get_student_by_id(self, student_id: int) -> Optional[Dict]:
        """Get student by ID"""
        result = await self._execute_query("SELECT * FROM students WHERE id = ?", (student_id,))
        return result[0] if result else None
    
    async def get_all_students(self) -> List[Dict]:
        """Get all active students"""
        return await self._execute_query("SELECT * FROM students WHERE active = 1 ORDER BY name")
    
    # Borrow operations
    async def create_borrow(self, borrow_data: Dict) -> Dict:
        """Create a new borrow record"""
        result = await self._execute_query(
            """INSERT INTO borrows (student_id, book_id, borrow_date, due_date) 
               VALUES (?, ?, ?, ?)""",
            (borrow_data["student_id"], borrow_data["book_id"], 
             borrow_data["borrow_date"], borrow_data["due_date"])
        )
        
        # Update book status to borrowed
        await self._execute_query(
            "UPDATE books SET status = 'borrowed', updated_at = ? WHERE id = ?",
            (datetime.now().isoformat(), borrow_data["book_id"])
        )
        
        return await self.get_borrow_by_id(result[0]["lastrowid"])
    
    async def get_borrow_by_id(self, borrow_id: int) -> Optional[Dict]:
        """Get borrow record by ID"""
        result = await self._execute_query(
            """SELECT b.*, s.name as student_name, bk.title as book_title 
               FROM borrows b 
               JOIN students s ON b.student_id = s.id 
               JOIN books bk ON b.book_id = bk.id 
               WHERE b.id = ?""", 
            (borrow_id,)
        )
        return result[0] if result else None
    
    async def get_overdue_borrows(self) -> List[Dict]:
        """Get all overdue borrow records"""
        today = date.today().isoformat()
        return await self._execute_query(
            """SELECT b.*, s.name as student_name, s.email as student_email, 
                      bk.title as book_title 
               FROM borrows b 
               JOIN students s ON b.student_id = s.id 
               JOIN books bk ON b.book_id = bk.id 
               WHERE b.status = 'active' AND b.due_date < ?""",
            (today,)
        )
    
    async def return_book(self, borrow_id: int, return_date: str, fine_amount: float = 0.0) -> Optional[Dict]:
        """Return a book"""
        # Update borrow record
        await self._execute_query(
            """UPDATE borrows SET returned_date = ?, status = 'returned', 
               fine_amount = ?, updated_at = ? WHERE id = ?""",
            (return_date, fine_amount, datetime.now().isoformat(), borrow_id)
        )
        
        # Get book_id and update book status
        borrow = await self.get_borrow_by_id(borrow_id)
        if borrow:
            await self._execute_query(
                "UPDATE books SET status = 'available', updated_at = ? WHERE id = ?",
                (datetime.now().isoformat(), borrow["book_id"])
            )
        
        return borrow
    
    async def close(self):
        """Close database connection"""
        self.executor.shutdown(wait=True)