"""
Lead Generation Platform - Backend Entry Point (Full Pipeline)
"""

import os
from datetime import datetime, date
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db, init_db
from app.core.scheduler import start_scheduler, stop_scheduler, run_all_saved_searches
from app.models.models import Search, Business, Lead, OutreachLog
from app.lead_sources.openstreetmap import OpenStreetMapSource
from app.scrapers.email_extractor import EmailScraper
from app.qualification.rules import run_qualification
from app.outreach.email_channel import EmailChannel, build_email

load_dotenv()

DAILY_SEND_LIMIT = int(os.getenv("DAILY_SEND_LIMIT", "50"))

app = FastAPI(title="Local Lead Generation Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

lead_source = OpenStreetMapSource()
email_scraper = EmailScraper()
email_channel = EmailChannel()


@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    stop_scheduler()


class SearchRequest(BaseModel):
    query: str
    location: str
    limit: int = 20


class LeadUpdateRequest(BaseModel):
    email: str | None = None
    status: str | None = None


def business_to_dict(b: Business) -> dict:
    return {
        "id": b.id,
        "name": b.name,
        "category": b.category,
        "address": b.address,
        "phone": b.phone,
        "rating": b.rating,
        "website_url": b.website_url,
        "latitude": b.latitude,
        "longitude": b.longitude,
        "source": b.source,
    }


def lead_to_dict(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "business_id": lead.business_id,
        "business_name": lead.business.name if lead.business else None,
        "category": lead.business.category if lead.business else None,
        "website_url": lead.business.website_url if lead.business else None,
        "phone": lead.business.phone if lead.business else None,
        "address": lead.business.address if lead.business else None,
        "email": lead.email,
        "email_found": lead.email_found,
        "website_live": lead.website_live,
        "status": lead.status,
        "rejection_reason": lead.rejection_reason,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }


@app.get("/")
def root():
    return {"status": "ok", "message": "Lead Generation Platform API. Dashboard runs separately - see README."}


@app.post("/api/search")
def search_leads(req: SearchRequest, db: Session = Depends(get_db)):
    """OpenStreetMap se businesses laata hai aur DB mein save karta hai."""
    try:
        results = lead_source.search(query=req.query, location=req.location, limit=req.limit)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    search_row = Search(query=req.query, location=req.location, last_run_at=datetime.utcnow())
    db.add(search_row)
    db.commit()
    db.refresh(search_row)

    saved_businesses = []
    for r in results:
        biz = Business(
            search_id=search_row.id,
            name=r.name, category=r.category, address=r.address,
            phone=r.phone, rating=r.rating, website_url=r.website_url,
            latitude=r.latitude, longitude=r.longitude, source=r.source,
        )
        db.add(biz)
        saved_businesses.append(biz)
    db.commit()
    for biz in saved_businesses:
        db.refresh(biz)

    return {
        "search_id": search_row.id,
        "query": req.query,
        "location": req.location,
        "count": len(saved_businesses),
        "businesses": [business_to_dict(b) for b in saved_businesses],
    }


@app.post("/api/scrape/{business_id}")
def scrape_and_qualify(business_id: int, db: Session = Depends(get_db)):
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    scrape_result = email_scraper.scrape(business.website_url or "")

    lead = db.query(Lead).filter(Lead.business_id == business_id).first()
    if not lead:
        lead = Lead(business_id=business_id)
        db.add(lead)

    lead.email = scrape_result.email
    lead.email_found = scrape_result.email_found
    lead.website_live = scrape_result.website_live
    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)

    status, reason = run_qualification(business_to_dict(business), lead_to_dict(lead))
    lead.status = status
    lead.rejection_reason = reason
    db.commit()
    db.refresh(lead)

    return {
        "scrape_error_reason": scrape_result.error_reason,
        "lead": lead_to_dict(lead),
    }


@app.get("/api/leads")
def list_leads(status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    leads = query.order_by(Lead.updated_at.desc()).all()
    return {"count": len(leads), "leads": [lead_to_dict(l) for l in leads]}


@app.put("/api/leads/{lead_id}")
def update_lead(lead_id: int, req: LeadUpdateRequest, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if req.email is not None:
        lead.email = req.email
        lead.email_found = bool(req.email)
    if req.status is not None:
        lead.status = req.status

    lead.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(lead)
    return lead_to_dict(lead)


@app.post("/api/leads/{lead_id}/send")
def send_outreach(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    if lead.status != "qualified":
        raise HTTPException(status_code=400, detail=f"Lead status is '{lead.status}', only 'qualified' leads can be sent")

    if not lead.email:
        raise HTTPException(status_code=400, detail="Lead has no email address")

    today_start = datetime.combine(date.today(), datetime.min.time())
    sent_today = db.query(func.count(OutreachLog.id)).filter(
        OutreachLog.status == "sent", OutreachLog.sent_at >= today_start
    ).scalar()

    if sent_today >= DAILY_SEND_LIMIT:
        raise HTTPException(status_code=429, detail=f"Daily send limit ({DAILY_SEND_LIMIT}) reached - protecting sender reputation")

    business = lead.business
    subject, body = build_email(business.name, business.category or "business")
    result = email_channel.send(lead.email, subject, body)

    log = OutreachLog(
        lead_id=lead.id, channel="email", template_used=body,
        status=result.status, error_message=result.error_message,
    )
    db.add(log)

    if result.success:
        lead.status = "contacted"
        lead.updated_at = datetime.utcnow()

    db.commit()

    return {"send_status": result.status, "error": result.error_message, "lead_status": lead.status}


@app.get("/api/outreach-logs")
def list_outreach_logs(db: Session = Depends(get_db)):
    logs = db.query(OutreachLog).order_by(OutreachLog.sent_at.desc()).all()
    return {
        "count": len(logs),
        "logs": [
            {
                "id": l.id,
                "lead_id": l.lead_id,
                "business_name": l.lead.business.name if l.lead and l.lead.business else None,
                "channel": l.channel,
                "status": l.status,
                "error_message": l.error_message,
                "sent_at": l.sent_at.isoformat() if l.sent_at else None,
            } for l in logs
        ],
    }


@app.get("/api/searches")
def list_searches(db: Session = Depends(get_db)):
    searches = db.query(Search).order_by(Search.created_at.desc()).all()
    return {
        "searches": [
            {"id": s.id, "query": s.query, "location": s.location, "created_at": s.created_at.isoformat()}
            for s in searches
        ]
    }


@app.post("/api/run-scheduled-searches")
def trigger_scheduled_run():
    run_all_saved_searches()
    return {"status": "completed", "message": "All saved searches re-run and new leads auto-qualified"}
