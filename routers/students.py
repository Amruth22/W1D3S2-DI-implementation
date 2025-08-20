"""
Students Router
Handles all student-related operations with dependency injection
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from models import Student, StudentCreate, StudentUpdate
from services.database_service import DatabaseService
from services.cache_service import CacheService
from services.email_service import EmailService
from dependencies import get_database_service, get_cache_service, get_email_service

router = APIRouter()

@router.get("/", response_model=List[Student])
async def get_all_students(
    active_only: bool = Query(True, description="Get only active students"),
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Get all students with caching"""
    
    async def fetch_students():
        return await db.get_all_students()
    
    cache_key = f"all_students_active_{active_only}"
    students = await cache.get_or_set(cache_key, fetch_students, ttl=300)
    
    if not active_only:
        # If we need inactive students too, we'd need a different query
        # For now, we only support active students
        pass
    
    return students

@router.get("/{student_id}", response_model=Student)
async def get_student(
    student_id: int,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Get student by ID with caching"""
    
    async def fetch_student():
        student = await db.get_student_by_id(student_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        return student
    
    student = await cache.cache_student_data(student_id, fetch_student)
    return student

@router.post("/", response_model=Student)
async def create_student(
    student: StudentCreate,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Create a new student"""
    try:
        student_data = student.dict()
        new_student = await db.create_student(student_data)
        
        # Send welcome email (mock)
        await email_service.send_email(
            to_email=new_student["email"],
            subject="Welcome to School Library System",
            body=f"""
Dear {new_student["name"]},

Welcome to the School Library Management System!

Your student details:
- Student ID: {new_student["student_id"]}
- Grade: {new_student["grade"]}
- Email: {new_student["email"]}

You can now borrow books from the library. Please visit the library desk for your first book!

Best regards,
School Library Team
            """,
            email_type="welcome"
        )
        
        # Invalidate cache
        await cache.delete("all_students_active_True")
        
        return new_student
    except Exception as e:
        if "UNIQUE constraint failed" in str(e):
            if "email" in str(e):
                raise HTTPException(status_code=400, detail="Student with this email already exists")
            elif "student_id" in str(e):
                raise HTTPException(status_code=400, detail="Student with this student ID already exists")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{student_id}", response_model=Student)
async def update_student(
    student_id: int,
    student_update: StudentUpdate,
    db: DatabaseService = Depends(get_database_service),
    cache: CacheService = Depends(get_cache_service)
):
    """Update a student"""
    # Check if student exists
    existing_student = await db.get_student_by_id(student_id)
    if not existing_student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Update student (we need to implement this in database service)
    update_data = student_update.dict(exclude_unset=True)
    
    # For now, we'll create a simple update method
    # In a real implementation, you'd add this to DatabaseService
    if update_data:
        # This is a simplified update - in real implementation, add to DatabaseService
        raise HTTPException(status_code=501, detail="Student update not implemented yet")
    
    # Invalidate cache
    await cache.invalidate_student_cache(student_id)
    await cache.delete("all_students_active_True")
    
    return existing_student

@router.get("/{student_id}/borrowed-books")
async def get_student_borrowed_books(
    student_id: int,
    db: DatabaseService = Depends(get_database_service)
):
    """Get all books currently borrowed by a student"""
    # Check if student exists
    student = await db.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get borrowed books (we need to implement this query)
    # For now, return a placeholder
    return {
        "student_id": student_id,
        "student_name": student["name"],
        "borrowed_books": [],
        "total_borrowed": 0,
        "message": "Feature coming soon - need to implement borrowed books query"
    }

@router.get("/{student_id}/borrow-history")
async def get_student_borrow_history(
    student_id: int,
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    db: DatabaseService = Depends(get_database_service)
):
    """Get student's borrowing history"""
    # Check if student exists
    student = await db.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get borrow history (we need to implement this query)
    return {
        "student_id": student_id,
        "student_name": student["name"],
        "borrow_history": [],
        "total_records": 0,
        "message": "Feature coming soon - need to implement borrow history query"
    }

@router.get("/{student_id}/fines")
async def get_student_fines(
    student_id: int,
    db: DatabaseService = Depends(get_database_service)
):
    """Get student's outstanding fines"""
    # Check if student exists
    student = await db.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get outstanding fines (we need to implement this query)
    return {
        "student_id": student_id,
        "student_name": student["name"],
        "outstanding_fines": 0.0,
        "fine_details": [],
        "message": "Feature coming soon - need to implement fines query"
    }

@router.post("/{student_id}/send-notification")
async def send_student_notification(
    student_id: int,
    subject: str = Query(..., description="Email subject"),
    message: str = Query(..., description="Email message"),
    db: DatabaseService = Depends(get_database_service),
    email_service: EmailService = Depends(get_email_service)
):
    """Send notification email to student"""
    # Check if student exists
    student = await db.get_student_by_id(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Send email
    result = await email_service.send_email(
        to_email=student["email"],
        subject=subject,
        body=f"""
Dear {student["name"]},

{message}

Best regards,
School Library Team
        """,
        email_type="notification"
    )
    
    return {
        "student_id": student_id,
        "student_name": student["name"],
        "email_sent": result["success"],
        "email_id": result.get("email_id"),
        "message": "Notification sent successfully"
    }

@router.get("/stats/summary")
async def get_student_stats(
    db: DatabaseService = Depends(get_database_service)
):
    """Get student statistics"""
    students = await db.get_all_students()
    
    # Count by grade
    grades = {}
    for student in students:
        grade = student["grade"]
        grades[grade] = grades.get(grade, 0) + 1
    
    return {
        "total_students": len(students),
        "active_students": len([s for s in students if s["active"]]),
        "by_grade": grades
    }

@router.get("/search/by-name")
async def search_students_by_name(
    name: str = Query(..., min_length=2, description="Student name to search"),
    db: DatabaseService = Depends(get_database_service)
):
    """Search students by name"""
    students = await db.get_all_students()
    
    # Simple name search
    matching_students = [
        student for student in students 
        if name.lower() in student["name"].lower()
    ]
    
    return {
        "search_query": name,
        "students": matching_students,
        "count": len(matching_students)
    }