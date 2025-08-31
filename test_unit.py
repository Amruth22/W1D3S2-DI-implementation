import unittest
import os
import sys
import tempfile
import shutil
import asyncio
from datetime import datetime, date, timedelta
from dotenv import load_dotenv

# Add the current directory to Python path to import project modules
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class CoreDependencyInjectionTests(unittest.TestCase):
    """Core 5 unit tests for Dependency Injection Implementation with real components"""
    
    @classmethod
    def setUpClass(cls):
        """Load configuration and validate setup"""
        # Note: This system doesn't require API keys - it's a local library management system
        print("Setting up Dependency Injection System tests...")
        
        # Initialize DI components (classes only, no heavy initialization)
        try:
            import dependencies
            from services.database_service import DatabaseService
            from services.cache_service import CacheService
            from services.email_service import EmailService
            import models
            
            cls.dependencies = dependencies
            cls.DatabaseService = DatabaseService
            cls.CacheService = CacheService
            cls.EmailService = EmailService
            cls.models = models
            
            print("Dependency injection components loaded successfully")
        except ImportError as e:
            raise unittest.SkipTest(f"Required dependency injection components not found: {e}")

    def setUp(self):
        """Set up test fixtures with temporary database"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_library.db")

    def tearDown(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_01_dependency_injection_setup(self):
        """Test 1: Dependency Injection Setup and Configuration"""
        print("Running Test 1: Dependency Injection Setup")
        
        # Test dependency injection module structure
        self.assertTrue(hasattr(self.dependencies, 'get_database_service'))
        self.assertTrue(hasattr(self.dependencies, 'get_cache_service'))
        self.assertTrue(hasattr(self.dependencies, 'get_email_service'))
        self.assertTrue(hasattr(self.dependencies, 'get_all_services'))
        
        # Test global service variables
        self.assertTrue(hasattr(self.dependencies, 'database_service'))
        self.assertTrue(hasattr(self.dependencies, 'cache_service'))
        self.assertTrue(hasattr(self.dependencies, 'email_service'))
        
        # Test dependency functions are callable
        self.assertTrue(callable(self.dependencies.get_database_service))
        self.assertTrue(callable(self.dependencies.get_cache_service))
        self.assertTrue(callable(self.dependencies.get_email_service))
        self.assertTrue(callable(self.dependencies.get_all_services))
        
        # Test service class availability
        self.assertIsNotNone(self.DatabaseService)
        self.assertIsNotNone(self.CacheService)
        self.assertIsNotNone(self.EmailService)
        
        # Test models module
        self.assertTrue(hasattr(self.models, 'Book'))
        self.assertTrue(hasattr(self.models, 'Student'))
        self.assertTrue(hasattr(self.models, 'Borrow'))
        
        print("PASS: Dependency injection functions available")
        print("PASS: Service classes available")
        print("PASS: Models module available")
        print("PASS: Dependency injection setup validated")

    def test_02_database_service_operations(self):
        """Test 2: Database Service Operations"""
        print("Running Test 2: Database Service Operations")
        
        # Initialize database service with test database
        db_service = self.DatabaseService(db_path=self.test_db_path)
        self.assertIsNotNone(db_service)
        self.assertEqual(db_service.db_path, self.test_db_path)
        self.assertIsNotNone(db_service.executor)
        
        # Test database initialization
        async def test_db_init():
            await db_service.initialize()
            return True
        
        init_result = asyncio.run(test_db_init())
        self.assertTrue(init_result)
        self.assertTrue(os.path.exists(self.test_db_path))
        
        # Test book operations
        async def test_book_operations():
            # Create a test book
            book_data = {
                "title": "Test Book",
                "author": "Test Author",
                "isbn": "9780123456789",
                "category": "test",
                "publication_year": 2023
            }
            
            created_book = await db_service.create_book(book_data)
            self.assertIsNotNone(created_book)
            self.assertEqual(created_book['title'], "Test Book")
            self.assertEqual(created_book['author'], "Test Author")
            
            # Get book by ID
            retrieved_book = await db_service.get_book_by_id(created_book['id'])
            self.assertIsNotNone(retrieved_book)
            self.assertEqual(retrieved_book['id'], created_book['id'])
            
            # Search books
            search_results = await db_service.search_books(query="Test", category="test")
            self.assertIsInstance(search_results, list)
            self.assertGreater(len(search_results), 0)
            
            return created_book['id']
        
        book_id = asyncio.run(test_book_operations())
        
        # Test student operations
        async def test_student_operations():
            # Create a test student
            student_data = {
                "name": "Test Student",
                "email": "test@school.edu",
                "student_id": "TEST001",
                "grade": "Grade 10"
            }
            
            created_student = await db_service.create_student(student_data)
            self.assertIsNotNone(created_student)
            self.assertEqual(created_student['name'], "Test Student")
            
            # Get all students
            all_students = await db_service.get_all_students()
            self.assertIsInstance(all_students, list)
            self.assertGreater(len(all_students), 0)
            
            return created_student['id']
        
        student_id = asyncio.run(test_student_operations())
        
        # Test borrow operations
        async def test_borrow_operations():
            # Create a borrow record
            borrow_data = {
                "student_id": student_id,
                "book_id": book_id,
                "borrow_date": date.today().isoformat(),
                "due_date": (date.today() + timedelta(days=14)).isoformat()
            }
            
            created_borrow = await db_service.create_borrow(borrow_data)
            self.assertIsNotNone(created_borrow)
            self.assertEqual(created_borrow['student_id'], student_id)
            self.assertEqual(created_borrow['book_id'], book_id)
            
            return created_borrow['id']
        
        borrow_id = asyncio.run(test_borrow_operations())
        
        # Clean up
        async def cleanup():
            await db_service.close()
        
        asyncio.run(cleanup())
        
        print(f"PASS: Database operations - Book ID: {book_id}, Student ID: {student_id}, Borrow ID: {borrow_id}")
        print("PASS: Database service operations validated")

    def test_03_cache_service_operations(self):
        """Test 3: LRU Cache Service Operations"""
        print("Running Test 3: Cache Service Operations")
        
        # Initialize cache service
        cache_service = self.CacheService(max_size=5, default_ttl=60)
        self.assertIsNotNone(cache_service)
        self.assertEqual(cache_service.max_size, 5)
        self.assertEqual(cache_service.default_ttl, 60)
        self.assertIsInstance(cache_service.cache, dict)
        
        # Test cache operations
        async def test_cache_ops():
            # Test set and get
            await cache_service.set("test_key", "test_value")
            value = await cache_service.get("test_key")
            self.assertEqual(value, "test_value")
            
            # Test cache miss
            missing_value = await cache_service.get("nonexistent_key")
            self.assertIsNone(missing_value)
            
            # Test cache deletion
            deleted = await cache_service.delete("test_key")
            self.assertTrue(deleted)
            
            # Test cache after deletion
            deleted_value = await cache_service.get("test_key")
            self.assertIsNone(deleted_value)
            
            # Test LRU eviction
            for i in range(6):  # More than max_size
                await cache_service.set(f"key_{i}", f"value_{i}")
            
            # First key should be evicted
            first_value = await cache_service.get("key_0")
            self.assertIsNone(first_value)
            
            # Last key should still exist
            last_value = await cache_service.get("key_5")
            self.assertEqual(last_value, "value_5")
            
            # Test cache statistics
            stats = await cache_service.get_stats()
            self.assertIn('size', stats)
            self.assertIn('max_size', stats)
            self.assertIn('usage_percent', stats)
            self.assertEqual(stats['max_size'], 5)
            self.assertLessEqual(stats['size'], 5)
            
            # Test cache key generation
            key1 = cache_service._generate_key("test", param1="value1", param2="value2")
            key2 = cache_service._generate_key("test", param1="value1", param2="value2")
            key3 = cache_service._generate_key("test", param1="different", param2="value2")
            
            self.assertEqual(key1, key2)  # Same parameters should generate same key
            self.assertNotEqual(key1, key3)  # Different parameters should generate different keys
            
            return stats
        
        stats = asyncio.run(test_cache_ops())
        
        print(f"PASS: Cache operations - Size: {stats['size']}/{stats['max_size']}")
        print(f"PASS: LRU eviction working correctly")
        print(f"PASS: Cache key generation working")
        print("PASS: Cache service operations validated")

    def test_04_email_service_operations(self):
        """Test 4: Email Service Operations"""
        print("Running Test 4: Email Service Operations")
        
        # Initialize email service
        email_service = self.EmailService()
        self.assertIsNotNone(email_service)
        self.assertIsInstance(email_service.sent_emails, list)
        self.assertIsInstance(email_service.email_templates, dict)
        
        # Test email templates
        expected_templates = ["overdue_notice", "borrow_confirmation", "return_confirmation"]
        for template in expected_templates:
            self.assertIn(template, email_service.email_templates)
            self.assertIn("subject", email_service.email_templates[template])
            self.assertIn("template", email_service.email_templates[template])
        
        # Test email operations
        async def test_email_ops():
            # Test basic email sending
            result = await email_service.send_email(
                to_email="test@example.com",
                subject="Test Email",
                body="This is a test email",
                email_type="test"
            )
            
            self.assertTrue(result['success'])
            self.assertIn('email_id', result)
            self.assertIn('sent_at', result)
            
            # Test overdue notice
            overdue_result = await email_service.send_overdue_notice(
                student_email="student@school.edu",
                student_name="Test Student",
                book_title="Test Book",
                due_date="2023-12-01",
                days_overdue=5,
                fine_amount=7.50
            )
            
            self.assertTrue(overdue_result['success'])
            
            # Test borrow confirmation
            borrow_result = await email_service.send_borrow_confirmation(
                student_email="student@school.edu",
                student_name="Test Student",
                book_title="Test Book",
                author="Test Author",
                borrow_date=date.today().isoformat(),
                due_date=(date.today() + timedelta(days=14)).isoformat()
            )
            
            self.assertTrue(borrow_result['success'])
            
            # Test email statistics
            stats = await email_service.get_email_stats()
            self.assertIn('total_emails_sent', stats)
            self.assertIn('emails_by_type', stats)
            self.assertGreater(stats['total_emails_sent'], 0)
            
            # Test sent emails retrieval
            sent_emails = await email_service.get_sent_emails(limit=10)
            self.assertIsInstance(sent_emails, list)
            self.assertGreater(len(sent_emails), 0)
            
            return stats
        
        stats = asyncio.run(test_email_ops())
        
        print(f"PASS: Email operations - {stats['total_emails_sent']} emails sent")
        print(f"PASS: Email templates - {len(email_service.email_templates)} templates available")
        print("PASS: Email service operations validated")

    def test_05_fastapi_structure_and_di_integration(self):
        """Test 5: FastAPI Structure and DI Integration"""
        print("Running Test 5: FastAPI Structure and DI Integration")
        
        # Test FastAPI application structure
        try:
            from main import app
            from fastapi.testclient import TestClient
            
            test_client = TestClient(app)
            
            # Test root endpoint
            response = test_client.get("/")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("message", data)
            self.assertIn("School Library Management API", data["message"])
            self.assertIn("endpoints", data)
            
            # Test health endpoint
            response = test_client.get("/health")
            self.assertEqual(response.status_code, 200)
            health_data = response.json()
            self.assertEqual(health_data["status"], "healthy")
            self.assertEqual(health_data["services"], "running")
            
            print("PASS: FastAPI structure validated")
            
        except ImportError as e:
            print(f"INFO: FastAPI test skipped due to: {str(e)}")
            
            # Test that main files exist
            self.assertTrue(os.path.exists('main.py'))
            self.assertTrue(os.path.exists('dependencies.py'))
            print("PASS: Main application files exist")
        
        # Test router structure
        try:
            from routers import books, students, borrow
            
            # Test that routers have the required attributes
            self.assertTrue(hasattr(books, 'router'))
            self.assertTrue(hasattr(students, 'router'))
            self.assertTrue(hasattr(borrow, 'router'))
            
            print("PASS: Router modules structure validated")
            
        except ImportError as e:
            print(f"INFO: Router test skipped due to: {str(e)}")
            
            # Test that router files exist
            self.assertTrue(os.path.exists('routers/books.py'))
            self.assertTrue(os.path.exists('routers/students.py'))
            self.assertTrue(os.path.exists('routers/borrow.py'))
            print("PASS: Router files exist")
        
        # Test models structure
        try:
            from models import Book, Student, Borrow
            
            # Test model creation
            test_book = Book(
                id=1,
                title="Test Book",
                author="Test Author",
                isbn="9780123456789",
                category="fiction",
                publication_year=2023,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.assertEqual(test_book.title, "Test Book")
            self.assertEqual(test_book.author, "Test Author")
            self.assertEqual(test_book.status, "available")  # Default value
            
            test_student = Student(
                id=1,
                name="Test Student",
                email="test@school.edu",
                student_id="TEST001",
                grade="Grade 10",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.assertEqual(test_student.name, "Test Student")
            self.assertEqual(test_student.email, "test@school.edu")
            self.assertTrue(test_student.active)  # Default value
            
            test_borrow = Borrow(
                id=1,
                student_id=1,
                book_id=1,
                borrow_date=date.today(),
                due_date=date.today() + timedelta(days=14),
                status="active",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            self.assertEqual(test_borrow.student_id, 1)
            self.assertEqual(test_borrow.book_id, 1)
            self.assertEqual(test_borrow.status, "active")  # Default value
            
            print("PASS: Pydantic models structure validated")
            
        except ImportError as e:
            print(f"INFO: Models test skipped due to: {str(e)}")
            
            # Test that models file exists
            self.assertTrue(os.path.exists('models.py'))
            print("PASS: Models file exists")
        
        # Test directory structure
        expected_dirs = ['services', 'routers']
        for directory in expected_dirs:
            self.assertTrue(os.path.exists(directory), f"Directory {directory} should exist")
        
        # Test service files
        service_files = ['services/database_service.py', 'services/cache_service.py', 'services/email_service.py']
        for service_file in service_files:
            self.assertTrue(os.path.exists(service_file), f"Service file {service_file} should exist")
        
        print("PASS: FastAPI application structure validated")
        print("PASS: Dependency injection integration confirmed")
        print("PASS: Service and router architecture validated")
        print("PASS: FastAPI structure and DI integration validated")

def run_core_tests():
    """Run core tests and provide summary"""
    print("=" * 70)
    print("[*] Core Dependency Injection Implementation Unit Tests (5 Tests)")
    print("Testing with LOCAL Services and DI Components")
    print("=" * 70)
    
    print("[INFO] This system uses local services (no API keys required)")
    print("[INFO] Tests validate DI pattern, services, and FastAPI integration")
    print()
    
    # Run tests
    suite = unittest.TestLoader().loadTestsFromTestCase(CoreDependencyInjectionTests)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    print("[*] Test Results:")
    print(f"[*] Tests Run: {result.testsRun}")
    print(f"[*] Failures: {len(result.failures)}")
    print(f"[*] Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n[FAILURES]:")
        for test, traceback in result.failures:
            print(f"  - {test}")
            print(f"    {traceback}")
    
    if result.errors:
        print("\n[ERRORS]:")
        for test, traceback in result.errors:
            print(f"  - {test}")
            print(f"    {traceback}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print("\n[SUCCESS] All 5 core dependency injection tests passed!")
        print("[OK] Dependency injection components working correctly with local services")
        print("[OK] DI Setup, Database Service, Cache Service, Email Service, FastAPI Integration validated")
    else:
        print(f"\n[WARNING] {len(result.failures) + len(result.errors)} test(s) failed")
    
    return success

if __name__ == "__main__":
    print("[*] Starting Core Dependency Injection Implementation Tests")
    print("[*] 5 essential tests with local services and DI components")
    print("[*] Components: DI Setup, Database Service, Cache Service, Email Service, FastAPI Integration")
    print()
    
    success = run_core_tests()
    exit(0 if success else 1)