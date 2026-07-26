"""
Email Outreach Channel - SMTP se templated email bhejta hai.

Setup (.env mein):
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_USER=you@gmail.com
    SMTP_PASSWORD=your-gmail-app-password   (normal password nahi - App Password banayein)
    FROM_EMAIL=you@gmail.com
    OUTREACH_DRY_RUN=true                   (true rakhein jab tak sending test na ho jaye)

SAFETY: OUTREACH_DRY_RUN=true (default) hone par actual email NAHI
jata - sirf console mein print hota hai aur "dry_run" status log
hoti hai. Client brief ka "review before sending" requirement isi
se implement hota hai. Jab confident ho jayein, .env mein
OUTREACH_DRY_RUN=false karein.

Sending limit: har run mein max DAILY_SEND_LIMIT emails - spam
flag se bachne ke liye (client brief ka requirement).
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

from .base import BaseChannel, SendResult

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
DRY_RUN = os.getenv("OUTREACH_DRY_RUN", "true").lower() == "true"


class EmailChannel(BaseChannel):

    def send(self, to_email: str, subject: str, body: str) -> SendResult:
        if DRY_RUN:
            print(f"[DRY RUN] Would send to {to_email} | Subject: {subject}")
            return SendResult(success=True, status="dry_run")

        if not SMTP_USER or not SMTP_PASSWORD:
            return SendResult(success=False, status="failed", error_message="SMTP credentials not configured in .env")

        try:
            msg = MIMEText(body, "plain")
            msg["Subject"] = subject
            msg["From"] = FROM_EMAIL
            msg["To"] = to_email

            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(FROM_EMAIL, [to_email], msg.as_string())

            return SendResult(success=True, status="sent")

        except Exception as e:
            return SendResult(success=False, status="failed", error_message=str(e))


def build_email(business_name: str, category: str) -> tuple[str, str]:
    """Simple personalized template - business name aur category insert karta hai."""
    subject = f"Quick question for {business_name}"
    body = f"""Hi {business_name} team,

Hope you're doing well. I came across your {category} business while researching
local services in your area, and wanted to reach out.

We help businesses like yours get more visibility online. Would you be open to
a quick chat this week?

If you'd rather not hear from us again, just reply "unsubscribe" and we won't
contact you further.

Best regards
"""
    return subject, body
