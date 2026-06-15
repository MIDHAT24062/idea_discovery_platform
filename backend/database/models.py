import os
from datetime import datetime

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, DateTime, Text, ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Railway injects DATABASE_URL as postgres:// but SQLAlchemy 1.4+ requires postgresql://
_raw_url = os.getenv("DATABASE_URL", "postgresql://postgres:12345@localhost/idea_discovery")
DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    query = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("sessions.id"))
    title = Column(String)
    summary = Column(Text)
    difficulty = Column(String)
    tags = Column(String)
    score = Column(Float)
    source = Column(String)
    url = Column(String)
    sentiment_score = Column(Float)
    upvotes = Column(Integer)


def init_db():
    Base.metadata.create_all(bind=engine)
