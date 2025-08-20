#!/usr/bin/env python3
"""
Simple API testing script to demonstrate the School Library Management API
Run this after starting the server to see the API in action
"""

import asyncio
import aiohttp
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"

async def test_api():
    """Test the API endpoints"""
    async with aiohttp.ClientSession() as session:
        print("🧪 Testing School Library Management API")
        print("=" * 50)
        
        # Test 1: Health Check
        print("\n1. 🏥 Health Check")
        async with session.get(f"{BASE_URL}/health") as response:
            data = await response.json()
            print(f"Status: {response.status}")
            print(f"Response: {data}")
        
        # Test 2: Get all books
        print("\n2. 📚 Get All Books")
        async with session.get(f"{BASE_URL}/api/books/") as response:
            books = await response.json()
            print(f"Status: {response.status}")
            print(f"Found {len(books)} books")
            if books:
                print(f"First book: {books[0]['title']} by {books[0]['author']}")
        
        # Test 3: Search books (async endpoint)
        print("\n3. 🔍 Async Book Search")
        search_params = {"query": "gatsby", "category": "fiction"}
        async with session.get(f"{BASE_URL}/api/books/search", params=search_params) as response:
            search_result = await response.json()
            print(f"Status: {response.status}")
            print(f"Search time: {search_result.get('search_time_ms', 0)}ms")
            print(f"Found {search_result.get('total_count', 0)} books")
        
        # Test 4: Get all students
        print("\n4. 👨‍🎓 Get All Students")
        async with session.get(f"{BASE_URL}/api/students/") as response:
            students = await response.json()
            print(f"Status: {response.status}")
            print(f"Found {len(students)} students")
            if students:
                print(f"First student: {students[0]['name']} ({students[0]['student_id']})")
        
        # Test 5: Create a new student
        print("\n5. ➕ Create New Student")
        new_student = {
            "name": "Test Student",
            "email": "test@school.edu",
            "student_id": "TEST001",
            "grade": "Grade 12"
        }
        async with session.post(f"{BASE_URL}/api/students/", 
                               json=new_student) as response:
            if response.status == 201 or response.status == 200:
                student_data = await response.json()
                print(f"Status: {response.status}")
                print(f"Created student: {student_data['name']} (ID: {student_data['id']})")
                created_student_id = student_data['id']
            else:
                print(f"Status: {response.status}")
                error = await response.json()
                print(f"Error: {error}")
                created_student_id = 1  # Use existing student for further tests
        
        # Test 6: Borrow a book
        print("\n6. 📖 Borrow a Book")
        due_date = (date.today() + timedelta(days=14)).isoformat()
        borrow_data = {
            "student_id": created_student_id,
            "book_id": 1,
            "due_date": due_date
        }
        async with session.post(f"{BASE_URL}/api/borrow/", 
                               json=borrow_data) as response:
            if response.status == 201 or response.status == 200:
                borrow_result = await response.json()
                print(f"Status: {response.status}")
                print(f"Borrowed book successfully (Borrow ID: {borrow_result['id']})")
                borrow_id = borrow_result['id']
            else:
                print(f"Status: {response.status}")
                error = await response.json()
                print(f"Error: {error}")
                borrow_id = None
        
        # Test 7: Calculate fines (async endpoint)
        print("\n7. 💰 Async Fine Calculation")
        fine_params = {"fine_per_day": 1.5}
        async with session.get(f"{BASE_URL}/api/borrow/fines/calculate", 
                              params=fine_params) as response:
            fine_result = await response.json()
            print(f"Status: {response.status}")
            print(f"Calculation time: {fine_result.get('calculation_time_ms', 0)}ms")
            print(f"Total fines: ${fine_result.get('total_fines', 0):.2f}")
            print(f"Overdue books: {len(fine_result.get('fines', []))}")
        
        # Test 8: Get book statistics
        print("\n8. 📊 Book Statistics")
        async with session.get(f"{BASE_URL}/api/books/stats/summary") as response:
            stats = await response.json()
            print(f"Status: {response.status}")
            print(f"Total books: {stats.get('total_books', 0)}")
            print(f"Available: {stats.get('available', 0)}")
            print(f"Borrowed: {stats.get('borrowed', 0)}")
        
        # Test 9: Send notification to student
        if created_student_id:
            print("\n9. 📧 Send Student Notification")
            notification_params = {
                "subject": "Test Notification",
                "message": "This is a test notification from the API testing script!"
            }
            async with session.post(f"{BASE_URL}/api/students/{created_student_id}/send-notification",
                                   params=notification_params) as response:
                notification_result = await response.json()
                print(f"Status: {response.status}")
                print(f"Notification sent: {notification_result.get('email_sent', False)}")
        
        # Test 10: Get overdue books
        print("\n10. ⏰ Get Overdue Books")
        async with session.get(f"{BASE_URL}/api/borrow/overdue") as response:
            overdue_result = await response.json()
            print(f"Status: {response.status}")
            print(f"Overdue books: {overdue_result.get('count', 0)}")
            print(f"Students affected: {overdue_result.get('total_students_affected', 0)}")
        
        print("\n" + "=" * 50)
        print("✅ API Testing Complete!")
        print("🎓 Check the console output for mock email notifications")
        print("📖 Visit http://localhost:8000/docs for interactive API documentation")

def main():
    """Main function to run the tests"""
    print("Starting API tests...")
    print("Make sure the server is running on http://localhost:8000")
    print("You can start it with: python main.py or python run.py")
    print()
    
    try:
        asyncio.run(test_api())
    except aiohttp.ClientConnectorError:
        print("❌ Error: Could not connect to the API server.")
        print("Please make sure the server is running on http://localhost:8000")
        print("Start the server with: python main.py")
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == "__main__":
    main()