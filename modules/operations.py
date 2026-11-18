"""
StayHome Hotel Management System - Operations & Analytics Module
File: modules/operations.py

Purpose:
    Handles core operational hotel workflows:
    - Guest Check-in (verifies reservation, marks room Occupied, updates status).
    - Guest Check-out (settles final balance, marks room Available, updates status).
    - Real-time Dashboard KPI aggregation from actual database records.
    - CSV Export utilities for rooms, customers, and bookings (fulfills Unit 2 File Handling syllabus).

Syllabus Concepts Covered:
    - Unit 1: Functions, conditionals, arithmetic calculations.
    - Unit 2: File Handling (csv module, StringIO), Lists of Dictionaries,
      Set operations, List Comprehensions, String formatting.
"""

from typing import Dict, Any, List
from datetime import date, datetime
import csv
import io
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from database.models import Room, Customer, Booking, Payment
from schemas.schemas import (
    CheckInRequest,
    CheckOutRequest,
    DashboardStatsResponse,
    ReservationResponse
)


# ==============================================================================
# 1. CHECK-IN OPERATION
# ==============================================================================

def process_check_in(db: Session, request: CheckInRequest) -> Dict[str, Any]:
    """
    Process guest check-in:
    - Ensures reservation exists and is currently in 'Confirmed' state.
    - Updates reservation status to 'Checked-In'.
    - Updates corresponding room status to 'Occupied'.

    Parameters:
        db (Session): Database session.
        request (CheckInRequest): Target booking ID.

    Returns:
        dict: Success message with stay details.
    """
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {request.booking_id} was not found."
        )

    # Unit 1: Conditional validation of booking state
    if booking.booking_status == "Checked-In":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Guest is already checked in for this reservation."
        )

    if booking.booking_status == "Checked-Out":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check in a reservation that is already checked out."
        )

    if booking.booking_status == "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot check in a cancelled reservation."
        )

    room = booking.room
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Room assigned to this booking does not exist."
        )

    # Update states
    booking.booking_status = "Checked-In"
    room.status = "Occupied"

    db.commit()
    db.refresh(booking)

    return {
        "success": True,
        "message": f"Successfully checked in {booking.customer.full_name} into Room {room.room_number}.",
        "booking_code": booking.booking_code,
        "room_number": room.room_number,
        "guest_name": booking.customer.full_name,
        "status": booking.booking_status
    }


# ==============================================================================
# 2. CHECK-OUT OPERATION
# ==============================================================================

def process_check_out(db: Session, request: CheckOutRequest) -> Dict[str, Any]:
    """
    Process guest check-out:
    - Ensures reservation exists and is currently in 'Checked-In' state.
    - Processes any final balance settlement paid at front desk.
    - Updates reservation status to 'Checked-Out'.
    - Updates room status back to 'Available' (or ready for housekeeping).

    Parameters:
        db (Session): Database session.
        request (CheckOutRequest): Target booking ID and optional payment details.

    Returns:
        dict: Success message with departure summary.
    """
    booking = db.query(Booking).filter(Booking.id == request.booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {request.booking_id} was not found."
        )

    if booking.booking_status != "Checked-In":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot check out reservation with status '{booking.booking_status}'. Guest must be Checked-In first."
        )

    payment = booking.payment
    if payment and request.amount_paid_now > 0:
        # Settle outstanding balance if payment made at checkout
        payment.amount_paid = round(payment.amount_paid + request.amount_paid_now, 2)
        if request.payment_method:
            payment.payment_method = request.payment_method.strip()
        payment.payment_date = datetime.now()

        if payment.amount_paid >= payment.total_amount:
            payment.payment_status = "Paid"
        else:
            payment.payment_status = "Partially Paid"

        settle_note = f"Settled ₹{request.amount_paid_now:.2f} at checkout."
        if request.notes:
            settle_note += f" ({request.notes})"
        payment.notes = (payment.notes or "") + f" | {settle_note}"

    # Mark booking completed and free the room
    booking.booking_status = "Checked-Out"
    if booking.room:
        booking.room.status = "Available"

    db.commit()
    db.refresh(booking)

    remaining_due = max(0.0, payment.total_amount - payment.amount_paid) if payment else 0.0

    return {
        "success": True,
        "message": f"Successfully checked out {booking.customer.full_name} from Room {booking.room.room_number}.",
        "booking_code": booking.booking_code,
        "room_number": booking.room.room_number,
        "guest_name": booking.customer.full_name,
        "status": booking.booking_status,
        "balance_remaining": remaining_due
    }


# ==============================================================================
# 3. DASHBOARD STATS AGGREGATOR
# ==============================================================================

def get_dashboard_statistics(db: Session) -> DashboardStatsResponse:
    """
    Computes all live operational statistics for the StayHome dashboard
    from actual database records.

    Returns:
        DashboardStatsResponse: Comprehensive statistics payload.
    """
    today = date.today()

    # Room statistics
    total_rooms = db.query(Room).count()
    available_rooms = db.query(Room).filter(Room.status == "Available").count()
    occupied_rooms = db.query(Room).filter(Room.status == "Occupied").count()
    maintenance_rooms = db.query(Room).filter(Room.status == "Maintenance").count()

    # Customer statistics
    total_customers = db.query(Customer).count()

    # Active reservations (Confirmed or Checked-In)
    active_reservations = db.query(Booking).filter(
        Booking.booking_status.in_(["Confirmed", "Checked-In"])
    ).count()

    # Today's check-ins: Bookings scheduled for check-in today
    today_checkins = db.query(Booking).filter(
        Booking.check_in_date == today,
        Booking.booking_status.in_(["Confirmed", "Checked-In"])
    ).count()

    # Today's check-outs: Bookings scheduled for departure today
    today_checkouts = db.query(Booking).filter(
        Booking.check_out_date == today,
        Booking.booking_status.in_(["Checked-In", "Checked-Out"])
    ).count()

    # Financial totals
    revenue_sum = db.query(func.sum(Payment.amount_paid)).scalar() or 0.0
    pending_payments_count = db.query(Payment).filter(
        Payment.payment_status.in_(["Pending", "Partially Paid"])
    ).count()

    # Recent 5 bookings
    recent_bookings_db = db.query(Booking).order_by(Booking.id.desc()).limit(5).all()
    recent_list = [ReservationResponse.model_validate(b) for b in recent_bookings_db]

    return DashboardStatsResponse(
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms,
        maintenance_rooms=maintenance_rooms,
        total_customers=total_customers,
        active_reservations=active_reservations,
        today_checkins=today_checkins,
        today_checkouts=today_checkouts,
        total_revenue=float(revenue_sum),
        pending_payments_count=pending_payments_count,
        recent_bookings=recent_list
    )


# ==============================================================================
# 4. CSV EXPORT UTILITIES (Unit 2: File Handling)
# ==============================================================================

def export_records_to_csv(db: Session, export_type: str) -> str:
    """
    Generates a CSV formatted string from database records.
    Demonstrates Unit 2 Python File Handling using io.StringIO and csv.writer.

    Parameters:
        db (Session): Database session.
        export_type (str): 'rooms', 'customers', or 'bookings'.

    Returns:
        str: CSV text content ready for download.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    if export_type.lower() == "rooms":
        # Write CSV Header
        writer.writerow(["Room ID", "Room Number", "Category", "Price Per Night (INR)", "Capacity", "Status", "Amenities"])
        rooms = db.query(Room).order_by(Room.room_number.asc()).all()
        for r in rooms:
            writer.writerow([r.id, r.room_number, r.room_type, r.price_per_night, r.capacity, r.status, r.amenities])

    elif export_type.lower() == "customers":
        writer.writerow(["Customer ID", "Full Name", "Email", "Phone", "Address", "ID Proof", "Registration Date"])
        customers = db.query(Customer).order_by(Customer.id.asc()).all()
        for c in customers:
            writer.writerow([c.id, c.full_name, c.email, c.phone, c.address or "", c.id_proof or "", c.created_at.strftime("%Y-%m-%d %H:%M")])

    elif export_type.lower() == "bookings":
        writer.writerow([
            "Booking ID", "Booking Code", "Customer Name", "Customer Phone",
            "Room Number", "Room Type", "Check-In Date", "Check-Out Date",
            "Nights", "Booking Status", "Total Amount", "Amount Paid", "Payment Status"
        ])
        bookings = db.query(Booking).order_by(Booking.id.desc()).all()
        for b in bookings:
            pay = b.payment
            writer.writerow([
                b.id,
                b.booking_code,
                b.customer.full_name if b.customer else "N/A",
                b.customer.phone if b.customer else "N/A",
                b.room.room_number if b.room else "N/A",
                b.room.room_type if b.room else "N/A",
                b.check_in_date.strftime("%Y-%m-%d"),
                b.check_out_date.strftime("%Y-%m-%d"),
                b.total_nights,
                b.booking_status,
                pay.total_amount if pay else 0.0,
                pay.amount_paid if pay else 0.0,
                pay.payment_status if pay else "N/A"
            ])
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown export type '{export_type}'. Supported: 'rooms', 'customers', 'bookings'."
        )

    return output.getvalue()
