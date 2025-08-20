"""
Borrow Router
Handles all borrowing operations with async fine calculations and dependency injection
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
import asyncio
import time
from datetime import date, datetime, timedelta

from models import Borrow, BorrowCreate, BorrowUpdate, FineCalculation, FineCalculationResult
from services.database_service import DatabaseService
from services.cache_service import CacheService
from services.email_service import EmailService
from dependencies import get_database_service, get_cache_service, get_email_service

router = APIRouter()

@router.post("/", response_model=Borrow)
async def borrow_book(
    borrow_data: BorrowCreate,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Borrow a book"""
    # Check if student exists
    student = await db.get_student_by_id(borrow_data.student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Check if book exists and is available
    book = await db.get_book_by_id(borrow_data.book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    if book["status"] != "available":
        raise HTTPException(status_code=400, detail=f"Book is not available (status: {book['status']})")
    
    # Create borrow record
    borrow_dict = {
        "student_id": borrow_data.student_id,
        "book_id": borrow_data.book_id,
        "borrow_date": date.today().isoformat(),
        "due_date": borrow_data.due_date.isoformat()
    }
    
    new_borrow = await db.create_borrow(borrow_dict)
    
    # Send confirmation email
    await email_service.send_borrow_confirmation(
        student_email=student["email"],
        student_name=student["name"],
        book_title=book["title"],
        author=book["author"],
        borrow_date=borrow_dict["borrow_date"],
        due_date=borrow_dict["due_date"]
    )
    
    # Invalidate relevant caches
    await cache.invalidate_book_cache(borrow_data.book_id)
    await cache.delete("all_books")
    
    return new_borrow

@router.get("/{borrow_id}", response_model=Borrow)
async def get_borrow_record(
    borrow_id: int,
    db: DatabaseService = Depends(get_database_service)
):
    """Get borrow record by ID"""
    borrow = await db.get_borrow_by_id(borrow_id)
    if not borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    
    return borrow

@router.put("/{borrow_id}/return")
async def return_book(
    borrow_id: int,
    return_date: Optional[date] = Query(None, description="Return date (defaults to today)"),
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Return a borrowed book"""
    # Get borrow record
    borrow = await db.get_borrow_by_id(borrow_id)
    if not borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    
    if borrow["status"] != "active":
        raise HTTPException(status_code=400, detail="Book is already returned")
    
    # Use provided return date or today
    actual_return_date = return_date or date.today()
    
    # Calculate fine if overdue
    due_date = datetime.strptime(borrow["due_date"], "%Y-%m-%d").date()
    fine_amount = 0.0
    
    if actual_return_date > due_date:
        days_overdue = (actual_return_date - due_date).days
        fine_per_day = 1.0  # $1 per day
        fine_amount = days_overdue * fine_per_day
    
    # Return the book
    returned_borrow = await db.return_book(
        borrow_id=borrow_id,
        return_date=actual_return_date.isoformat(),
        fine_amount=fine_amount
    )
    
    # Send return confirmation email
    student = await db.get_student_by_id(borrow["student_id"])
    book = await db.get_book_by_id(borrow["book_id"])
    
    await email_service.send_return_confirmation(
        student_email=student["email"],
        student_name=student["name"],
        book_title=book["title"],
        return_date=actual_return_date.isoformat(),
        fine_amount=fine_amount
    )
    
    # Invalidate caches
    await cache.invalidate_book_cache(borrow["book_id"])
    await cache.delete("all_books")
    
    return {
        "borrow_id": borrow_id,
        "returned": True,
        "return_date": actual_return_date.isoformat(),
        "fine_amount": fine_amount,
        "message": "Book returned successfully"
    }

@router.get("/fines/calculate", response_model=FineCalculationResult)
async def calculate_overdue_fines_async(
    fine_per_day: float = Query(1.0, ge=0.1, le=10.0, description="Fine amount per day"),
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """
    Async fine calculation for overdue books
    This endpoint demonstrates async operations for calculating fines
    """
    start_time = time.time()
    
    async def fetch_fine_calculations():
        # Get all overdue borrows
        overdue_borrows = await db.get_overdue_borrows()
        
        if not overdue_borrows:
            return []
        
        # Calculate fines for each overdue book concurrently
        fine_tasks = []
        
        for borrow in overdue_borrows:
            fine_tasks.append(
                calculate_single_fine(borrow, fine_per_day)
            )
        
        # Execute all fine calculations concurrently
        fine_calculations = await asyncio.gather(*fine_tasks)
        
        return fine_calculations
    
    # Use cache for fine calculations (cache for 1 hour)
    today = date.today().isoformat()
    fines = await cache.cache_fine_calculation(
        calculation_date=f"{today}_{fine_per_day}",
        fetch_func=fetch_fine_calculations
    )
    
    calculation_time = (time.time() - start_time) * 1000  # Convert to milliseconds
    total_fines = sum(fine.total_fine for fine in fines)
    
    return FineCalculationResult(
        fines=fines,
        total_fines=total_fines,
        calculation_time_ms=round(calculation_time, 2)
    )

async def calculate_single_fine(borrow: dict, fine_per_day: float) -> FineCalculation:
    """Calculate fine for a single overdue book"""
    # Simulate some processing time
    await asyncio.sleep(0.01)
    
    due_date = datetime.strptime(borrow["due_date"], "%Y-%m-%d").date()
    today = date.today()
    days_overdue = (today - due_date).days
    total_fine = days_overdue * fine_per_day
    
    return FineCalculation(
        borrow_id=borrow["id"],
        days_overdue=days_overdue,
        fine_per_day=fine_per_day,
        total_fine=total_fine,
        student_name=borrow["student_name"],
        book_title=borrow["book_title"]
    )

@router.post("/fines/send-notices")
async def send_overdue_notices(
    fine_per_day: float = Query(1.0, ge=0.1, le=10.0, description="Fine amount per day"),
    db: DatabaseService = Depends(get_database_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Send overdue notices to all students with overdue books"""
    # Get overdue borrows
    overdue_borrows = await db.get_overdue_borrows()
    
    if not overdue_borrows:
        return {
            "message": "No overdue books found",
            "notices_sent": 0
        }
    
    # Prepare email data
    email_data = []
    for borrow in overdue_borrows:
        due_date = datetime.strptime(borrow["due_date"], "%Y-%m-%d").date()
        days_overdue = (date.today() - due_date).days
        fine_amount = days_overdue * fine_per_day
        
        email_data.append({
            "student_email": borrow["student_email"],
            "student_name": borrow["student_name"],
            "book_title": borrow["book_title"],
            "due_date": borrow["due_date"],
            "days_overdue": days_overdue,
            "fine_amount": fine_amount
        })
    
    # Send bulk overdue notices
    result = await email_service.send_bulk_overdue_notices(email_data)
    
    return {
        "message": "Overdue notices processing completed",
        "total_overdue_books": len(overdue_borrows),
        "notices_sent": result["sent_successfully"],
        "notices_failed": result["failed"],
        "details": result
    }

@router.get("/active")
async def get_active_borrows(
    student_id: Optional[int] = Query(None, description="Filter by student ID"),
    book_id: Optional[int] = Query(None, description="Filter by book ID"),
    db: DatabaseService = Depends(get_database_service)
):
    """Get all active borrow records"""
    # This would need a proper query implementation in DatabaseService
    # For now, return a placeholder
    return {
        "active_borrows": [],
        "count": 0,
        "message": "Feature coming soon - need to implement active borrows query"
    }

@router.get("/overdue")
async def get_overdue_borrows(
    db: DatabaseService = Depends(get_database_service)
):
    """Get all overdue borrow records"""
    overdue_borrows = await db.get_overdue_borrows()
    
    return {
        "overdue_borrows": overdue_borrows,
        "count": len(overdue_borrows),
        "total_students_affected": len(set(b["student_id"] for b in overdue_borrows))
    }

@router.get("/stats/summary")
async def get_borrow_stats(
    db: DatabaseService = Depends(get_database_service)
):
    """Get borrowing statistics"""
    overdue_borrows = await db.get_overdue_borrows()
    
    return {
        "overdue_books": len(overdue_borrows),
        "students_with_overdue": len(set(b["student_id"] for b in overdue_borrows)),
        "message": "More stats coming soon - need to implement additional queries"
    }

@router.put("/{borrow_id}/extend")
async def extend_due_date(
    borrow_id: int,
    new_due_date: date = Query(..., description="New due date"),
    db: DatabaseService = Depends(get_database_service)
):
    """Extend the due date of a borrowed book"""
    # Get borrow record
    borrow = await db.get_borrow_by_id(borrow_id)
    if not borrow:
        raise HTTPException(status_code=404, detail="Borrow record not found")
    
    if borrow["status"] != "active":
        raise HTTPException(status_code=400, detail="Cannot extend due date for returned book")
    
    # Check if new due date is in the future
    if new_due_date <= date.today():
        raise HTTPException(status_code=400, detail="New due date must be in the future")
    
    # Update due date (we need to implement this in DatabaseService)
    # For now, return a placeholder
    return {
        "borrow_id": borrow_id,
        "old_due_date": borrow["due_date"],
        "new_due_date": new_due_date.isoformat(),
        "message": "Feature coming soon - need to implement due date extension"
    }