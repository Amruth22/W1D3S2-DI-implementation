"""
Dependency Injection Setup
Simple DI pattern for injecting services into FastAPI endpoints
"""

from fastapi import Depends
from services.database_service import DatabaseService
from services.cache_service import CacheService
from services.email_service import EmailService
import main

def get_database_service() -> DatabaseService:
    """Dependency to inject database service"""
    return main.database_service

def get_cache_service() -> CacheService:
    """Dependency to inject cache service"""
    return main.cache_service

def get_email_service() -> EmailService:
    """Dependency to inject email service"""
    return main.email_service

# Combined dependency for endpoints that need all services
def get_all_services():
    """Dependency to inject all services at once"""
    return {
        "db": get_database_service(),
        "cache": get_cache_service(),
        "email": get_email_service()
    }