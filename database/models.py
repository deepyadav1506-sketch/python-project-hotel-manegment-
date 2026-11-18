"""
StayHome Hotel Management System - Database Models
File: database/models.py

Purpose:
    Defines the Object Relational Mapping (ORM) classes for the StayHome system.
    SQLAlchemy maps each Python class defined here to an actual relational database table.

Tables:
    1. rooms       - Stores hotel room details, categories, pricing, and live status.
    2. customers   - Stores customer contact info and identification records.
    3. bookings    - Connects a customer to a room for a specific date range.
    4. payments    - Tracks billing, tax calculations, discounts, and payment status.

Syllabus Concepts Covered:
    - Object-Oriented Programming (Classes, Inheritance, Attributes).
    - Data Types (Integer, String, Float, Date, DateTime, Text, Boolean).
    - Database Relationships (Primary Key, Foreign Key, One-to-Many, One-to-One).
"""

from datetime import datetime, date
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    DateTime,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from database.database import Base


class Room(Base):
    """
    Represents an individual hotel room in StayHome.

    Attributes:
        id: Unique primary key for internal indexing.
        room_number: Unique room identifier (e.g. "101", "205", "Penthouse-A").
        room_type: Category of room ('Standard', 'Deluxe', 'Suite').
        price_per_night: Base cost per night in currency units (e.g. INR or USD).
        capacity: Maximum allowed guests in the room.
        status: Live operational state ('Available', 'Occupied', 'Maintenance').
        amenities: Comma-separated list of room amenities.
        created_at: Timestamp when room was added to system.
    """
    __tablename__ = "rooms"

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(20), unique=True, nullable=False, index=True)
    room_type = Column(String(50), nullable=False, default="Standard")
    price_per_night = Column(Float, nullable=False, default=1000.0)
    capacity = Column(Integer, nullable=False, default=2)
    status = Column(String(30), nullable=False, default="Available")
    amenities = Column(String(255), nullable=True, default="Free High-Speed Wi-Fi, Air Conditioning, Smart TV")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships:
    # A room can have multiple bookings over time (one-to-many relationship)
    bookings = relationship("Booking", back_populates="room", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Room(number='{self.room_number}', type='{self.room_type}', status='{self.status}')>"


class Customer(Base):
    """
    Represents a guest / customer of the hotel.

    Attributes:
        id: Unique primary key.
        full_name: Guest's full legal name.
        email: Contact email address (must be unique).
        phone: Primary phone number for reservations and SMS alerts.
        address: Residential or billing address.
        id_proof: Government ID number or type (e.g., Passport, Aadhaar, Driver License).
        created_at: Record registration timestamp.
    """
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    phone = Column(String(25), nullable=False)
    address = Column(String(255), nullable=True)
    id_proof = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationships:
    # A customer can make multiple bookings over their lifetime (one-to-many relationship)
    bookings = relationship("Booking", back_populates="customer")

    def __repr__(self):
        return f"<Customer(name='{self.full_name}', email='{self.email}', phone='{self.phone}')>"


class Booking(Base):
    """
    Represents a room reservation made by a customer.

    Attributes:
        id: Unique booking ID.
        booking_code: Human-readable reference code (e.g. "SH-202611-101").
        customer_id: Foreign key referencing the customer table.
        room_id: Foreign key referencing the rooms table.
        check_in_date: Scheduled or actual check-in date (YYYY-MM-DD).
        check_out_date: Scheduled or actual check-out date (YYYY-MM-DD).
        total_nights: Calculated count of nights stayed.
        guests_count: Number of guests accommodated for this stay.
        special_requests: Any dietary or accessibility requests.
        booking_status: Lifecycle status ('Confirmed', 'Checked-In', 'Checked-Out', 'Cancelled').
        created_at: Booking creation timestamp.
    """
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    booking_code = Column(String(30), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)
    total_nights = Column(Integer, nullable=False, default=1)
    guests_count = Column(Integer, nullable=False, default=1)
    special_requests = Column(Text, nullable=True)
    booking_status = Column(String(30), nullable=False, default="Confirmed")
    created_at = Column(DateTime, default=datetime.now)

    # Relationships:
    customer = relationship("Customer", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    # One-to-one relationship with the Payment/Billing record
    payment = relationship("Payment", back_populates="booking", uselist=False, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Booking(code='{self.booking_code}', status='{self.booking_status}')>"


class Payment(Base):
    """
    Represents an invoice and payment transaction for a booking.

    Attributes:
        id: Primary key.
        invoice_number: Unique invoice code (e.g. "INV-SH-1001").
        booking_id: Foreign key referencing the booking.
        room_charges: Subtotal = price_per_night * total_nights.
        discount_amount: Deducted promotional or loyalty discount.
        tax_amount: Calculated government / hotel service tax.
        total_amount: Net payable = room_charges - discount_amount + tax_amount.
        amount_paid: Amount actually received so far.
        payment_method: Mode of payment ('Cash', 'Credit Card', 'UPI', 'Debit Card', 'Bank Transfer').
        payment_status: State of settlement ('Pending', 'Partially Paid', 'Paid').
        payment_date: Timestamp of last recorded payment.
        notes: Optional staff remarks or transaction reference numbers.
        created_at: Invoice creation timestamp.
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(40), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=False, unique=True)
    room_charges = Column(Float, nullable=False, default=0.0)
    discount_amount = Column(Float, nullable=False, default=0.0)
    tax_amount = Column(Float, nullable=False, default=0.0)
    total_amount = Column(Float, nullable=False, default=0.0)
    amount_paid = Column(Float, nullable=False, default=0.0)
    payment_method = Column(String(50), nullable=False, default="Cash")
    payment_status = Column(String(30), nullable=False, default="Pending")
    payment_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    # Relationship back to the booking
    booking = relationship("Booking", back_populates="payment")

    def __repr__(self):
        return f"<Payment(invoice='{self.invoice_number}', total={self.total_amount}, status='{self.payment_status}')>"
