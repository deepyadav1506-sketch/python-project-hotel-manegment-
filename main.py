"""
StayHome Hotel Management System - Main FastAPI Application
File: main.py

Purpose:
    The central entry point of the application. Initializes FastAPI, configures
    CORS, registers all REST API endpoints, initializes database tables,
    and mounts the frontend single-page interface for browser access.

Syllabus Concepts Covered:
    - FastAPI framework fundamentals (Path parameters, Query parameters, Request bodies).
    - Dependency Injection (Depends(get_db)).
    - Status codes (HTTP 200, 201, 400, 404).
    - Exception handling and JSON response serialization.
"""

import os
from contextlib import asynccontextmanager
from typing import List, Optional
from datetime import date

from fastapi import FastAPI, Depends, Query, Path, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from database.database import get_db, engine, Base
from database.init_db import init_db
from schemas.schemas import (
    RoomCreate, RoomUpdate, RoomResponse,
    CustomerCreate, CustomerUpdate, CustomerResponse,
    ReservationCreate, ReservationUpdate, ReservationResponse,
    PaymentRecordRequest, PaymentResponse, InvoiceResponse,
    CheckInRequest, CheckOutRequest, DashboardStatsResponse
)
from modules import rooms, customers, reservations, billing, operations


# ==============================================================================
# LIFESPAN / APPLICATION STARTUP
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles application startup and shutdown events cleanly.
    Automatically creates database tables and seeds demo data on launch.
    """
    print("[StayHome] Application starting up...")
    try:
        init_db()
        print("[StayHome] Database initialized successfully.")
    except Exception as e:
        print(f"[StayHome Warning] Database initialization check: {e}")
    yield
    print("[StayHome] Application shutting down...")


# Create FastAPI application instance
app = FastAPI(
    title="StayHome Hotel Management System",
    description="Full-stack hotel management platform built with Python, FastAPI, and SQLAlchemy.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================================================================
# 1. DASHBOARD & ANALYTICS ENDPOINTS
# ==============================================================================

@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse, tags=["Dashboard"])
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns real-time dashboard KPIs computed directly from database records:
    Total rooms, available rooms, occupied rooms, active stays, revenue, today's checkins/outs.
    """
    return operations.get_dashboard_statistics(db)


# ==============================================================================
# 2. ROOM MANAGEMENT ENDPOINTS
# ==============================================================================

@app.get("/api/rooms", response_model=List[RoomResponse], tags=["Rooms"])
def list_rooms(
    category: Optional[str] = Query(None, description="Filter by 'Standard', 'Deluxe', 'Suite'"),
    status: Optional[str] = Query(None, description="Filter by 'Available', 'Occupied', 'Maintenance'"),
    search: Optional[str] = Query(None, description="Search room number or amenities"),
    db: Session = Depends(get_db)
):
    """Fetch all rooms with multi-criteria search and category filters."""
    return rooms.get_all_rooms(db=db, category=category, room_status=status, search=search)


@app.get("/api/rooms/available/lookup", response_model=List[RoomResponse], tags=["Rooms"])
def lookup_available_rooms(
    check_in: date = Query(..., description="Check-in date (YYYY-MM-DD)"),
    check_out: date = Query(..., description="Check-out date (YYYY-MM-DD)"),
    category: Optional[str] = Query(None, description="Optional category filter"),
    db: Session = Depends(get_db)
):
    """Find rooms that have NO conflicting bookings between given check-in and check-out dates."""
    return rooms.get_available_rooms_for_dates(db=db, check_in=check_in, check_out=check_out, room_type=category)


@app.get("/api/rooms/{room_id}", response_model=RoomResponse, tags=["Rooms"])
def get_room_details(room_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Retrieve details of a specific room by its ID."""
    return rooms.get_room_by_id(db=db, room_id=room_id)


@app.post("/api/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, tags=["Rooms"])
def add_new_room(room_data: RoomCreate, db: Session = Depends(get_db)):
    """Create a new hotel room in the system."""
    return rooms.create_room(db=db, room_data=room_data)


@app.put("/api/rooms/{room_id}", response_model=RoomResponse, tags=["Rooms"])
def update_room_details(
    room_id: int = Path(..., gt=0),
    update_data: RoomUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update existing room information (pricing, category, amenities, status)."""
    return rooms.update_room(db=db, room_id=room_id, update_data=update_data)


@app.delete("/api/rooms/{room_id}", tags=["Rooms"])
def remove_room(room_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Safely delete a room (blocked if active reservations exist)."""
    return rooms.delete_room(db=db, room_id=room_id)


# ==============================================================================
# 3. CUSTOMER MANAGEMENT ENDPOINTS
# ==============================================================================

@app.get("/api/customers", response_model=List[CustomerResponse], tags=["Customers"])
def list_customers(
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    db: Session = Depends(get_db)
):
    """Retrieve registered customer profiles with their total booking counts."""
    return customers.get_all_customers(db=db, search=search)


@app.get("/api/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def get_customer_details(customer_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Get profile information of a single customer."""
    c = customers.get_customer_by_id(db=db, customer_id=customer_id)
    return CustomerResponse.model_validate(c)


@app.post("/api/customers", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, tags=["Customers"])
def register_customer(customer_data: CustomerCreate, db: Session = Depends(get_db)):
    """Register a new customer profile."""
    return customers.create_customer(db=db, customer_data=customer_data)


@app.put("/api/customers/{customer_id}", response_model=CustomerResponse, tags=["Customers"])
def update_customer_profile(
    customer_id: int = Path(..., gt=0),
    update_data: CustomerUpdate = ...,
    db: Session = Depends(get_db)
):
    """Update contact details of a customer."""
    return customers.update_customer(db=db, customer_id=customer_id, update_data=update_data)


@app.delete("/api/customers/{customer_id}", tags=["Customers"])
def remove_customer(customer_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Safely delete a customer (blocked if active stays exist)."""
    return customers.delete_customer(db=db, customer_id=customer_id)


# ==============================================================================
# 4. RESERVATION MANAGEMENT ENDPOINTS
# ==============================================================================

@app.get("/api/reservations", response_model=List[ReservationResponse], tags=["Reservations"])
def list_reservations(
    status: Optional[str] = Query(None, description="Filter by Confirmed, Checked-In, Checked-Out, Cancelled"),
    search: Optional[str] = Query(None, description="Search by booking code, customer, room number"),
    db: Session = Depends(get_db)
):
    """List all reservations with comprehensive customer, room, and payment details."""
    bookings = reservations.get_all_reservations(db=db, booking_status=status, search=search)
    return [ReservationResponse.model_validate(b) for b in bookings]


@app.get("/api/reservations/{booking_id}", response_model=ReservationResponse, tags=["Reservations"])
def get_reservation(booking_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Retrieve full details of an individual reservation."""
    b = reservations.get_reservation_by_id(db=db, booking_id=booking_id)
    return ReservationResponse.model_validate(b)


@app.post("/api/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED, tags=["Reservations"])
def book_room(data: ReservationCreate, db: Session = Depends(get_db)):
    """
    Create a new reservation:
    - Validates arrival and departure dates.
    - Prevents double booking and overlapping stays.
    - Computes nights, room charges, discount, and tax.
    - Automatically creates a linked Payment / Invoice record.
    """
    new_booking = reservations.create_reservation(db=db, data=data)
    return ReservationResponse.model_validate(new_booking)


@app.post("/api/reservations/{booking_id}/cancel", tags=["Reservations"])
def cancel_booking(
    booking_id: int = Path(..., gt=0),
    reason: Optional[str] = Query(None, description="Cancellation reason note"),
    db: Session = Depends(get_db)
):
    """Cancel a confirmed reservation and immediately release the room."""
    return reservations.cancel_reservation(db=db, booking_id=booking_id, reason=reason)


# ==============================================================================
# 5. FRONT DESK OPERATIONS (CHECK-IN / CHECK-OUT)
# ==============================================================================

@app.post("/api/operations/check-in", tags=["Operations"])
def check_in_guest(request: CheckInRequest, db: Session = Depends(get_db)):
    """Check in a confirmed guest, mark booking 'Checked-In', and room 'Occupied'."""
    return operations.process_check_in(db=db, request=request)


@app.post("/api/operations/check-out", tags=["Operations"])
def check_out_guest(request: CheckOutRequest, db: Session = Depends(get_db)):
    """Check out a guest, collect any remaining balance, mark booking 'Checked-Out', and room 'Available'."""
    return operations.process_check_out(db=db, request=request)


# ==============================================================================
# 6. BILLING & INVOICE ENDPOINTS
# ==============================================================================

@app.get("/api/billing/payments", tags=["Billing"])
def list_payments(
    status: Optional[str] = Query(None, description="Filter: Paid, Partially Paid, Pending"),
    search: Optional[str] = Query(None, description="Search invoice number or guest name"),
    db: Session = Depends(get_db)
):
    """List all billing and payment transaction records."""
    payments = billing.get_all_payments(db=db, payment_status=status, search=search)
    result = []
    for p in payments:
        b = p.booking
        result.append({
            "id": p.id,
            "invoice_number": p.invoice_number,
            "booking_id": p.booking_id,
            "booking_code": b.booking_code if b else "N/A",
            "customer_name": b.customer.full_name if (b and b.customer) else "N/A",
            "room_number": b.room.room_number if (b and b.room) else "N/A",
            "room_charges": p.room_charges,
            "discount_amount": p.discount_amount,
            "tax_amount": p.tax_amount,
            "total_amount": p.total_amount,
            "amount_paid": p.amount_paid,
            "balance_due": max(0.0, round(p.total_amount - p.amount_paid, 2)),
            "payment_method": p.payment_method,
            "payment_status": p.payment_status,
            "payment_date": p.payment_date.strftime("%Y-%m-%d %H:%M") if p.payment_date else None,
            "notes": p.notes
        })
    return result


@app.post("/api/billing/payments/{booking_id}", tags=["Billing"])
def record_booking_payment(
    booking_id: int = Path(..., gt=0),
    payment_data: PaymentRecordRequest = ...,
    db: Session = Depends(get_db)
):
    """Record a payment transaction against a booking's invoice."""
    return billing.record_payment(db=db, booking_id=booking_id, payment_data=payment_data)


@app.get("/api/billing/invoice/{booking_id}", response_model=InvoiceResponse, tags=["Billing"])
def get_printable_invoice(booking_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    """Fetch complete itemized printable invoice payload for a stay."""
    return billing.generate_invoice_data(db=db, booking_id=booking_id)


# ==============================================================================
# 7. CSV EXPORT UTILITY (Unit 2: File Handling)
# ==============================================================================

@app.get("/api/export/csv/{export_type}", tags=["Data Export"])
def export_csv(export_type: str = Path(..., description="'rooms', 'customers', or 'bookings'"), db: Session = Depends(get_db)):
    """
    Export hotel data directly into a downloadable CSV file.
    Demonstrates Unit 2 Python file handling and formatting.
    """
    csv_content = operations.export_records_to_csv(db=db, export_type=export_type)
    filename = f"stayhome_{export_type}_{date.today().strftime('%Y%m%d')}.csv"
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==============================================================================
# 8. FRONTEND SERVING (STATIC FILES)
# ==============================================================================

# Ensure public/assets directory exists
public_path = os.path.join(os.path.dirname(__file__), "public")
assets_path = os.path.join(public_path, "assets")
os.makedirs(assets_path, exist_ok=True)

# Mount /assets static directory
app.mount("/assets", StaticFiles(directory=assets_path), name="assets")


@app.get("/", include_in_schema=False)
def serve_index():
    """Serve the primary StayHome single page dashboard."""
    index_file = os.path.join(public_path, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return PlainTextResponse("StayHome Hotel Management API is running. Frontend index.html loading...")
