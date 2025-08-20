"""
School Library Management API
Main application entry point with dependency injection setup
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from services.database_service import DatabaseService
from services.cache_service import CacheService
from services.email_service import EmailService
from routers import books, students, borrow
import dependencies

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    global database_service, cache_service, email_service
    
    # Startup
    print("🚀 Starting School Library Management API...")
    
    # Initialize services
    dependencies.database_service = DatabaseService()
    dependencies.cache_service = CacheService(max_size=100)
    dependencies.email_service = EmailService()
    
    # Initialize database
    await dependencies.database_service.initialize()
    
    print("✅ All services initialized successfully!")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down services...")
    if dependencies.database_service:
        await dependencies.database_service.close()
    print("👋 School Library Management API stopped!")

# Create FastAPI app with lifespan
app = FastAPI(
    title="School Library Management API",
    description="A simple library management system with DI, async endpoints, and modular architecture",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(books.router, prefix="/api/books", tags=["Books"])
app.include_router(students.router, prefix="/api/students", tags=["Students"])
app.include_router(borrow.router, prefix="/api/borrow", tags=["Borrowing"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to School Library Management API",
        "version": "1.0.0",
        "endpoints": {
            "books": "/api/books/",
            "students": "/api/students/",
            "borrow": "/api/borrow/"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "services": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)