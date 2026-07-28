"""
Background Scheduler - client brief ka "system must run 24/7" requirement.

APScheduler use kiya hai (Celery+Redis ke bajaye) kyunke:
- $50/month budget mein extra Redis service ki zaroorat nahi padti
- Chhoti/medium scale ke liye kaafi hai
- FastAPI process ke andar hi chalta hai, alag worker deploy nahi karna

What it does:
- Har SCHEDULE_INTERVAL_HOURS ghante baad (default 24), saari saved
  searches (Search table) ko dobara run karta hai
- Naye businesses jo pehle se DB mein nahi hain unhe insert karta hai
  (duplicate businesses skip - same name + website check)
- Naye businesses ko automatically scrape + qualify bhi kar deta hai,
  taake dashboard kholte hi naye qualified leads mil jayein
"""

import os
import logging
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO)

SCHEDULE_INTERVAL_HOURS = int(os.getenv("SCHEDULE_INTERVAL_HOURS", "24"))

scheduler = BackgroundScheduler()


def run_all_saved_searches():
    """Har saved search ko dobara chalata hai, naye leads discover + auto-qualify karta hai."""
    from app.core.database import SessionLocal
    from app.models.models import Search, Business, Lead
    from app.lead_sources.openstreetmap import OpenStreetMapSource
    from app.scrapers.email_extractor import EmailScraper
    from app.qualification.rules import run_qualification

    db = SessionLocal()
    lead_source = OpenStreetMapSource()
    email_scraper = EmailScraper()

    try:
        searches = db.query(Search).all()
        logger.info(f"[Scheduler] Running {len(searches)} saved searches at {datetime.utcnow()}")

        for search in searches:
            try:
                results = lead_source.search(query=search.query, location=search.location, limit=20)
            except Exception as e:
                logger.warning(f"[Scheduler] Search failed for '{search.query}' in '{search.location}': {e}")
                continue

            new_count = 0
            for r in results:
                # Duplicate check - same name + website already tracked anywhere in DB
                existing = db.query(Business).filter(
                    Business.name == r.name, Business.website_url == r.website_url
                ).first()
                if existing:
                    continue

                biz = Business(
                    search_id=search.id, name=r.name, category=r.category, address=r.address,
                    phone=r.phone, rating=r.rating, website_url=r.website_url,
                    latitude=r.latitude, longitude=r.longitude, source=r.source,
                )
                db.add(biz)
                db.commit()
                db.refresh(biz)
                new_count += 1

                # Naye business ko scrape + qualify bhi kar dete hain
                scrape_result = email_scraper.scrape(biz.website_url or "")
                lead = Lead(
                    business_id=biz.id, email=scrape_result.email,
                    email_found=scrape_result.email_found, website_live=scrape_result.website_live,
                )
                db.add(lead)
                db.commit()
                db.refresh(lead)

                business_dict = {"website_url": biz.website_url, "rating": biz.rating}
                lead_dict = {"email_found": lead.email_found, "website_live": lead.website_live}
                status, reason = run_qualification(business_dict, lead_dict)
                lead.status = status
                lead.rejection_reason = reason
                db.commit()

            search.last_run_at = datetime.utcnow()
            db.commit()
            logger.info(f"[Scheduler] '{search.query}' in '{search.location}': {new_count} new leads found")

    finally:
        db.close()


def start_scheduler():
    if not scheduler.running:
        scheduler.add_job(
            run_all_saved_searches,
            "interval",
            hours=SCHEDULE_INTERVAL_HOURS,
            id="recurring_search_job",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(f"[Scheduler] Started - saved searches will re-run every {SCHEDULE_INTERVAL_HOURS}h")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
