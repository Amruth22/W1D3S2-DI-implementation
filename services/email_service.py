"""
Mock Email Service
Simple mock email service that simulates sending emails by logging to console
Perfect for educational purposes without requiring external email providers
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional
import json

class EmailService:
    """Mock email service for educational purposes"""
    
    def __init__(self):
        self.sent_emails = []  # Store sent emails for testing/debugging
        self.email_templates = {
            "overdue_notice": {
                "subject": "📚 Library Book Overdue Notice",
                "template": """
Dear {student_name},

This is a friendly reminder that you have an overdue book from the school library.

Book Details:
- Title: {book_title}
- Due Date: {due_date}
- Days Overdue: {days_overdue}
- Fine Amount: ${fine_amount:.2f}

Please return the book as soon as possible to avoid additional fines.

Thank you,
School Library Management System
                """
            },
            "borrow_confirmation": {
                "subject": "📖 Book Borrowed Successfully",
                "template": """
Dear {student_name},

You have successfully borrowed a book from the school library.

Book Details:
- Title: {book_title}
- Author: {author}
- Borrow Date: {borrow_date}
- Due Date: {due_date}

Please return the book by the due date to avoid fines.

Happy Reading!
School Library Management System
                """
            },
            "return_confirmation": {
                "subject": "✅ Book Returned Successfully",
                "template": """
Dear {student_name},

Thank you for returning your book to the school library.

Book Details:
- Title: {book_title}
- Return Date: {return_date}
- Fine Amount: ${fine_amount:.2f}

{fine_message}

Thank you for using the library!
School Library Management System
                """
            }
        }
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        email_type: str = "general") -> Dict:
        """
        Mock send email function
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body
            email_type: Type of email for categorization
        
        Returns:
            Dict with email sending result
        """
        # Simulate email sending delay
        await asyncio.sleep(0.1)
        
        email_data = {
            "id": len(self.sent_emails) + 1,
            "to": to_email,
            "subject": subject,
            "body": body,
            "type": email_type,
            "sent_at": datetime.now().isoformat(),
            "status": "sent"
        }
        
        # Store email for debugging
        self.sent_emails.append(email_data)
        
        # Print to console (simulating email sending)
        print(f"\n{'='*60}")
        print(f"📧 MOCK EMAIL SENT")
        print(f"{'='*60}")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Type: {email_type}")
        print(f"Sent At: {email_data['sent_at']}")
        print(f"{'='*60}")
        print(body)
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "email_id": email_data["id"],
            "message": "Email sent successfully (mock)",
            "sent_at": email_data["sent_at"]
        }
    
    async def send_overdue_notice(self, student_email: str, student_name: str,
                                 book_title: str, due_date: str, days_overdue: int,
                                 fine_amount: float) -> Dict:
        """Send overdue book notice"""
        template = self.email_templates["overdue_notice"]
        
        body = template["template"].format(
            student_name=student_name,
            book_title=book_title,
            due_date=due_date,
            days_overdue=days_overdue,
            fine_amount=fine_amount
        )
        
        return await self.send_email(
            to_email=student_email,
            subject=template["subject"],
            body=body,
            email_type="overdue_notice"
        )
    
    async def send_borrow_confirmation(self, student_email: str, student_name: str,
                                     book_title: str, author: str, borrow_date: str,
                                     due_date: str) -> Dict:
        """Send book borrow confirmation"""
        template = self.email_templates["borrow_confirmation"]
        
        body = template["template"].format(
            student_name=student_name,
            book_title=book_title,
            author=author,
            borrow_date=borrow_date,
            due_date=due_date
        )
        
        return await self.send_email(
            to_email=student_email,
            subject=template["subject"],
            body=body,
            email_type="borrow_confirmation"
        )
    
    async def send_return_confirmation(self, student_email: str, student_name: str,
                                     book_title: str, return_date: str,
                                     fine_amount: float = 0.0) -> Dict:
        """Send book return confirmation"""
        template = self.email_templates["return_confirmation"]
        
        fine_message = ""
        if fine_amount > 0:
            fine_message = f"Please pay the fine of ${fine_amount:.2f} at the library desk."
        else:
            fine_message = "No fines applicable. Thank you for returning on time!"
        
        body = template["template"].format(
            student_name=student_name,
            book_title=book_title,
            return_date=return_date,
            fine_amount=fine_amount,
            fine_message=fine_message
        )
        
        return await self.send_email(
            to_email=student_email,
            subject=template["subject"],
            body=body,
            email_type="return_confirmation"
        )
    
    async def send_bulk_overdue_notices(self, overdue_data: List[Dict]) -> Dict:
        """Send overdue notices to multiple students"""
        results = []
        
        for data in overdue_data:
            try:
                result = await self.send_overdue_notice(
                    student_email=data["student_email"],
                    student_name=data["student_name"],
                    book_title=data["book_title"],
                    due_date=data["due_date"],
                    days_overdue=data["days_overdue"],
                    fine_amount=data["fine_amount"]
                )
                results.append({"student": data["student_name"], "status": "sent", "result": result})
            except Exception as e:
                results.append({"student": data["student_name"], "status": "failed", "error": str(e)})
        
        return {
            "total_emails": len(overdue_data),
            "sent_successfully": len([r for r in results if r["status"] == "sent"]),
            "failed": len([r for r in results if r["status"] == "failed"]),
            "results": results
        }
    
    async def get_sent_emails(self, email_type: Optional[str] = None, 
                            limit: int = 50) -> List[Dict]:
        """Get list of sent emails"""
        emails = self.sent_emails
        
        if email_type:
            emails = [email for email in emails if email["type"] == email_type]
        
        return emails[-limit:]  # Return last N emails
    
    async def get_email_stats(self) -> Dict:
        """Get email statistics"""
        total_emails = len(self.sent_emails)
        
        # Count by type
        type_counts = {}
        for email in self.sent_emails:
            email_type = email["type"]
            type_counts[email_type] = type_counts.get(email_type, 0) + 1
        
        return {
            "total_emails_sent": total_emails,
            "emails_by_type": type_counts,
            "last_email_sent": self.sent_emails[-1]["sent_at"] if self.sent_emails else None
        }
    
    async def clear_email_history(self) -> Dict:
        """Clear email history (for testing)"""
        count = len(self.sent_emails)
        self.sent_emails.clear()
        return {"message": f"Cleared {count} emails from history"}