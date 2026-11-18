"""
StayHome Hotel Management System - Database Configuration
File: database/database.py

Purpose:
    This file establishes the connection between our Python application and
    the database using SQLAlchemy. It supports:
    1. Local SQLite file database (default for development/testing).
    2. Cloud PostgreSQL (such as Neon) for production deployment on Vercel.

Syllabus Concepts Covered:
    - Variables, string manipulation, environment variable loading.
    - Conditional statements (if-else for SQLite vs PostgreSQL connection flags).
    - Functions and Generators (yield keyword in get_db for resource cleanup).
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file if present
load_dotenv()

# Read the database URL from environment, or fall back to local SQLite file
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stayhome.db")

# Neon and some cloud hosting platforms provide database URLs starting with
# 'postgres://' which SQLAlchemy 1.4+ expects as 'postgresql://'.
# We perform this string replacement to ensure full compatibility.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite requires a special connection argument 'check_same_thread: False'
# because FastAPI handles requests across multiple threads.
# PostgreSQL does not need or accept this parameter.
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create the SQLAlchemy Engine
# The engine is the central point of contact with the database.
engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False  # Set to True if you want to see all raw SQL queries in console
)

# Create a configured "SessionLocal" class
# Each instance of SessionLocal represents an individual database session.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Declarative Base: All our ORM models will inherit from this class
Base = declarative_base()


def get_db():
    """
    FastAPI Dependency that provides a database session to API route functions.

    How it works:
        1. Opens a new database session when an HTTP request arrives.
        2. 'yields' the session to the requesting route function.
        3. Automatically closes the session when the request finishes,
           preventing database connection leaks (even if an error occurs).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
