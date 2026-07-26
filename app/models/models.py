"""
Database tables (SQLAlchemy ORM models).

Pipeline flow: Search -> Business -> Lead -> OutreachLog
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Search(Base):
    __tablename__ = "searches"

    id = Column(Integer, primary_key=True, index=True)
    query = Column(String, nullable=False)         # e.g. "dentists"
    location = Column(String, nullable=False)      # e.g. "Lahore, Pakistan"
    created_at = Column(DateTime, default=datetime.utcnow)
    last_run_at = Column(DateTime, default=datetime.utcnow)

    businesses = relationship("Business", back_populates="search")


class Business(Base):
    __tablename__ = "businesses"

    id = Column(Integer, primary_key=True, index=True)
    search_id = Column(Integer, ForeignKey("searches.id"))
    name = Column(String)
    category = Column(String)
    address = Column(String)
    phone = Column(String)
    rating = Column(Float, nullable=True)
    website_url = Column(String, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    source = Column(String, default="openstreetmap")
    created_at = Column(DateTime, default=datetime.utcnow)

    search = relationship("Search", back_populates="businesses")
    lead = relationship("Lead", back_populates="business", uselist=False)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), unique=True)
    email = Column(String, nullable=True)
    email_found = Column(Boolean, default=False)
    website_live = Column(Boolean, nullable=True)
    status = Column(String, default="new")   # new / qualified / rejected / contacted / replied
    rejection_reason = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    business = relationship("Business", back_populates="lead")
    outreach_logs = relationship("OutreachLog", back_populates="lead")


class OutreachLog(Base):
    __tablename__ = "outreach_logs"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    channel = Column(String, default="email")
    template_used = Column(Text, nullable=True)
    sent_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String)   # sent / dry_run / bounced / failed
    error_message = Column(String, nullable=True)

    lead = relationship("Lead", back_populates="outreach_logs")
