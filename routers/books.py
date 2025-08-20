"""
Books Router
Handles all book-related operations with dependency injection and async search
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import asyncio
import time

from models import Book, BookCreate, BookUpdate, BookSearchQuery, BookSearchResult
from services.database_service import DatabaseService
from services.cache_service import CacheService
from services.email_service import EmailService
from dependencies import get_database_service, get_cache_service, get_email_service

router = APIRouter()

@router.get("/", response_model=List[Book])
async def get_all_books(
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Get all books with caching"""
    
    async def fetch_books():
        return await db.search_books()
    
    books = await cache.get_or_set("all_books", fetch_books, ttl=300)
    return books

@router.get("/search", response_model=BookSearchResult)
async def search_books_async(
    query: Optional[str] = Query(None, description="Search in title and author"),
    category: Optional[str] = Query(None, description="Filter by category"),
    author: Optional[str] = Query(None, description="Filter by author"),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Async book search across multiple categories
    This endpoint demonstrates async operations for I/O-heavy tasks
    """
    start_time = time.time()
    
    # Use cache for search results
    async def fetch_search_results():
        # Simulate searching across multiple categories concurrently
        search_tasks = []
        
        if category:
            # Search in specific category
            search_tasks.append(
                db.search_books(query=query, category=category, author=author, status=status)
            )
        else:
            # Search across all categories concurrently
            categories = ["fiction", "non_fiction", "science", "history", "biography", "technology"]
            
            for cat in categories:
                search_tasks.append(
                    db.search_books(query=query, category=cat, author=author, status=status)
                )
        
        # Execute all searches concurrently
        results = await asyncio.gather(*search_tasks)
        
        # Combine and deduplicate results
        all_books = []
        seen_ids = set()
        
        for book_list in results:
            for book in book_list:
                if book["id"] not in seen_ids:
                    all_books.append(book)
                    seen_ids.add(book["id"])
        
        return all_books
    
    # Use cache for search results
    books = await cache.cache_book_search(
        query=query or "",
        category=category or "",
        author=author or "",
        status=status or "",
        fetch_func=fetch_search_results
    )
    
    search_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    
    return BookSearchResult(
        books=books,
        total_count=len(books),
        search_time_ms=round(search_time, 2)
    )

@router.get("/{book_id}", response_model=Book)
async def get_book(
    book_id: int,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Get book by ID with caching"""
    
    async def fetch_book():
        book = await db.get_book_by_id(book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
    
    book = await cache.cache_book_data(book_id, fetch_book)
    return book

@router.post("/", response_model=Book)
async def create_book(
    book: BookCreate,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Create a new book"""
    try:
        book_data = book.dict()
        new_book = await db.create_book(book_data)
        
        # Invalidate cache
        await cache.delete("all_books")
        
        return new_book
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{book_id}", response_model=Book)
async def update_book(
    book_id: int,
    book_update: BookUpdate,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Update a book"""
    # Check if book exists
    existing_book = await db.get_book_by_id(book_id)
    if not existing_book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Update book
    update_data = book_update.dict(exclude_unset=True)
    updated_book = await db.update_book(book_id, update_data)
    
    # Invalidate cache
    await cache.invalidate_book_cache(book_id)
    await cache.delete("all_books")
    
    return updated_book

@router.get("/{book_id}/availability")
async def check_book_availability(
    book_id: int,
    db: DatabaseService = Depends(get_database_service)
):
    """Check if a book is available for borrowing"""
    book = await db.get_book_by_id(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    return {
        "book_id": book_id,
        "title": book["title"],
        "available": book["status"] == "available",
        "status": book["status"]
    }

@router.get("/category/{category}")
async def get_books_by_category(
    category: str,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Get all books in a specific category"""
    
    async def fetch_category_books():
        return await db.search_books(category=category)
    
    cache_key = f"category_{category}"
    books = await cache.get_or_set(cache_key, fetch_category_books, ttl=600)
    
    return {
        "category": category,
        "books": books,
        "count": len(books)
    }

@router.get("/author/{author}")
async def get_books_by_author(
    author: str,
    db: DatabaseService = Depends(get_database_service)
):
    """Get all books by a specific author"""
    books = await db.search_books(author=author)
    
    return {
        "author": author,
        "books": books,
        "count": len(books)
    }

@router.get("/stats/summary")
async def get_book_stats(
    db: DatabaseService = Depends(get_database_service)
):
    """Get book statistics"""
    all_books = await db.search_books()
    
    stats = {
        "total_books": len(all_books),
        "available": len([b for b in all_books if b["status"] == "available"]),
        "borrowed": len([b for b in all_books if b["status"] == "borrowed"]),
        "reserved": len([b for b in all_books if b["status"] == "reserved"])
    }
    
    # Count by category
    categories = {}
    for book in all_books:
        cat = book["category"]
        categories[cat] = categories.get(cat, 0) + 1
    
    stats["by_category"] = categories
    
    return stats