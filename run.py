#!/usr/bin/env python3
"""
Simple run script for School Library Management API
"""

import uvicorn
import sys
import os

def main():
    """Run the FastAPI application"""
    print("🚀 Starting School Library Management API...")
    print("📚 Educational FastAPI project with DI, Async, and Modular Architecture")
    print("-" * 60)
    
    try:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Shutting down gracefully...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()