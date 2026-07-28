"""
Database connection setup

Neon Postgres use karne ke liye .env mein DATABASE_URL set karein:
    DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@HOST/DBNAME?sslmode=require

(Neon dashboard se "Connection string" copy and paste here -
 bas 'postgresql://' ko 'postgresql+psycopg2://' se replace kar dein)

Agar DATABASE_URL set nahi hai, app automatically local SQLite file
(local_dev.db) use kar leta hai - taake Neon setup se pehle bhi
system test kiya ja sake.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # Neon set hone tak local fallback - development ke liye safe hai
    engine = create_engine("sqlite:///local_dev.db", connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency - har request ke liye ek DB session deta hai."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """App start hote hi tables create kar deta hai agar exist nahi karte."""
    from app.models import models  # noqa: ensures models are registered
    Base.metadata.create_all(bind=engine)
