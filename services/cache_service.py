"""
LRU Cache Service
Simple LRU (Least Recently Used) cache implementation for caching API responses
"""

import asyncio
from collections import OrderedDict
from typing import Any, Optional
import json
import hashlib
from datetime import datetime, timedelta

class CacheService:
    """Simple LRU Cache implementation with TTL support"""
    
    def __init__(self, max_size: int = 100, default_ttl: int = 300):
        """
        Initialize LRU Cache
        
        Args:
            max_size: Maximum number of items to cache
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache = OrderedDict()
        self.ttl_data = {}  # Store TTL information
        self._lock = asyncio.Lock()
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from prefix and parameters"""
        # Create a consistent key from parameters
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        async with self._lock:
            # Check if key exists and is not expired
            if key in self.cache:
                # Check TTL
                if key in self.ttl_data:
                    if datetime.now() > self.ttl_data[key]:
                        # Expired, remove from cache
                        del self.cache[key]
                        del self.ttl_data[key]
                        return None
                
                # Move to end (most recently used)
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set item in cache"""
        async with self._lock:
            # Use default TTL if not specified
            ttl = ttl or self.default_ttl
            
            # If key already exists, remove it first
            if key in self.cache:
                del self.cache[key]
            
            # If cache is full, remove least recently used item
            elif len(self.cache) >= self.max_size:
                # Remove oldest item
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                if oldest_key in self.ttl_data:
                    del self.ttl_data[oldest_key]
            
            # Add new item
            self.cache[key] = value
            self.ttl_data[key] = datetime.now() + timedelta(seconds=ttl)
    
    async def delete(self, key: str) -> bool:
        """Delete item from cache"""
        async with self._lock:
            if key in self.cache:
                del self.cache[key]
                if key in self.ttl_data:
                    del self.ttl_data[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache"""
        async with self._lock:
            self.cache.clear()
            self.ttl_data.clear()
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        async with self._lock:
            return {
                "size": len(self.cache),
                "max_size": self.max_size,
                "usage_percent": (len(self.cache) / self.max_size) * 100,
                "keys": list(self.cache.keys())
            }
    
    # Convenience methods for common cache patterns
    
    async def get_or_set(self, key: str, fetch_func, ttl: Optional[int] = None) -> Any:
        """Get from cache or fetch and set if not exists"""
        value = await self.get(key)
        if value is not None:
            return value
        
        # Fetch new value
        value = await fetch_func() if asyncio.iscoroutinefunction(fetch_func) else fetch_func()
        await self.set(key, value, ttl)
        return value
    
    async def cache_book_search(self, query: str, category: str, author: str, 
                               status: str, fetch_func) -> Any:
        """Cache book search results"""
        cache_key = self._generate_key(
            "book_search",
            query=query,
            category=category,
            author=author,
            status=status
        )
        return await self.get_or_set(cache_key, fetch_func, ttl=180)  # 3 minutes
    
    async def cache_student_data(self, student_id: int, fetch_func) -> Any:
        """Cache student data"""
        cache_key = self._generate_key("student", id=student_id)
        return await self.get_or_set(cache_key, fetch_func, ttl=600)  # 10 minutes
    
    async def cache_book_data(self, book_id: int, fetch_func) -> Any:
        """Cache book data"""
        cache_key = self._generate_key("book", id=book_id)
        return await self.get_or_set(cache_key, fetch_func, ttl=300)  # 5 minutes
    
    async def cache_fine_calculation(self, calculation_date: str, fetch_func) -> Any:
        """Cache fine calculation results"""
        cache_key = self._generate_key("fine_calculation", date=calculation_date)
        return await self.get_or_set(cache_key, fetch_func, ttl=3600)  # 1 hour
    
    async def invalidate_book_cache(self, book_id: int) -> None:
        """Invalidate book-related cache entries"""
        book_key = self._generate_key("book", id=book_id)
        await self.delete(book_key)
        
        # Also clear book search cache (simple approach - clear all search results)
        async with self._lock:
            keys_to_delete = [key for key in self.cache.keys() if key.startswith("book_search")]
            for key in keys_to_delete:
                del self.cache[key]
                if key in self.ttl_data:
                    del self.ttl_data[key]
    
    async def invalidate_student_cache(self, student_id: int) -> None:
        """Invalidate student-related cache entries"""
        student_key = self._generate_key("student", id=student_id)
        await self.delete(student_key)
    
    async def cleanup_expired(self) -> int:
        """Clean up expired cache entries"""
        async with self._lock:
            now = datetime.now()
            expired_keys = []
            
            for key, expiry_time in self.ttl_data.items():
                if now > expiry_time:
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self.cache:
                    del self.cache[key]
                del self.ttl_data[key]
            
            return len(expired_keys)