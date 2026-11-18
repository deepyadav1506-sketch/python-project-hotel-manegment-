"""
StayHome Hotel Management System - Reservation Management Module
File: modules/reservations.py

Purpose:
    Handles end-to-end hotel room booking logic:
    - Date validation (arrival before departure, positive night count).
    - Room availability verification (prevents overlapping/double bookings).
    - Unique booking reference code generation.
    - Automatic bill and invoice creation upon booking confirmation.
    - Reservation status filtering and cancellation workflows.

Syllabus Concepts Covered:
    - Unit 1: Functions, parameters, return statements, mathematical operations,
      if-elif-else statements, boolean logic (AND/OR).
    - Unit 2: Tuples, Lists, String formatting, Date arithmetic (timedelta).
"""

from typing import List, Optional
from datetime import date, datetime
import random
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status

from database.models import Booking, Room, Customer, Payment
from schemas.schemas import (
    ReservationCreate,
    ReservationUpdate,
    ReservationResponse,
    BookingCustomerSummary,
    BookingRoomSummary,
    BookingPaymentSummary
)


def calculate_nights(check_in: date, check_out: date) -> int:
    """
    Unit 1 Function: Calculate the total number of nights between two dates.

    Parameters:
        check_in (date): Guest arrival date.
        check_out (date): Guest departure date.

    Returns:
        int: Total nights of stay.

    Raises:
        HTTPException: If dates are logically invalid (check-in on or after check-out).
    """
    if check_in >= check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dates: Check-in date must be strictly before check-out date."
        )

    # Date subtraction returns a timedelta object; .days extracts the integer count
    delta = (check_out - check_in).days
    return int(delta)


def check_room_availability(
    db: Session,
    room_id: int,
    check_in: date,
    check_out: date,
    exclude_booking_id: Optional[int] = None
) -> bool:
    """
    Verifies whether a room is free from overlapping active bookings.

    Mathematical Condition for Overlap:
        An existing reservation overlaps with the requested interval if:
        (Existing Check-In < Requested Check-Out) AND (Existing Check-Out > Requested Check-In)

    Parameters:
        db (Session): Database session.
        room_id (int): ID of the room to inspect.
        check_in (date): Requested check-in date.
        check_out (date): Requested check-out date.
        exclude_booking_id (int, optional): Booking ID to exclude (used when editing a booking).

    Returns:
        bool: True if room is free and available, False if conflict exists.
    """
    query = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.booking_status.in_(["Confirmed", "Checked-In"]),
        Booking.check_in_date < check_out,
        Booking.check_out_date > check_in
    )

    if exclude_booking_id:
        query = query.filter(Booking.id != exclude_booking_id)

    conflict_count = query.count()
    return conflict_count == 0


def generate_booking_code() -> str:
    """
    Generate a professional unique reference code for a booking.
    Format: SH-YYYYMM-XXXX (e.g. SH-202611-4821)
    """
    today_str = datetime.now().strftime("%Y%m")
    random_digits = random.randint(1000, 9999)
    return f"SH-{today_str}-{random_digits}"


def generate_invoice_number() -> str:
    """
    Generate a professional unique invoice number.
    Format: INV-SH-XXXXX
    """
    random_digits = random.randint(10000, 99999)
    return f"INV-SH-{random_digits}"


def create_reservation(db: Session, data: ReservationCreate) -> Booking:
    """
    Creates a new reservation with automatic room conflict check and billing setup.

    Steps:
        1. Verify Customer exists.
        2. Verify Room exists and is not under Maintenance.
        3. Validate dates and compute nights.
        4. Check for double booking / date overlap.
        5. Insert Booking record.
        6. Calculate charges, discount, taxes and insert linked Payment record.
    """
    # 1. Customer verification
    customer = db.query(Customer).filter(Customer.id == data.customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {data.customer_id} does not exist."
        )

    # 2. Room verification
    room = db.query(Room).filter(Room.id == data.room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with ID {data.room_id} does not exist."
        )

    if room.status == "Maintenance":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room {room.room_number} is currently marked under Maintenance and cannot be booked."
        )

    # 3. Date validation & night calculation
    nights = calculate_nights(data.check_in_date, data.check_out_date)

    # 4. Check for double booking conflict
    is_available = check_room_availability(
        db=db,
        room_id=data.room_id,
        check_in=data.check_in_date,
        check_out=data.check_out_date
    )

    if not is_available:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room {room.room_number} is already booked for the selected dates ({data.check_in_date} to {data.check_out_date}). Please choose different dates or another room."
        )

    # 5. Create Booking instance
    booking_code = generate_booking_code()

    # Ensure booking code is unique
    while db.query(Booking).filter(Booking.booking_code == booking_code).first():
        booking_code = generate_booking_code()

    new_booking = Booking(
        booking_code=booking_code,
        customer_id=data.customer_id,
        room_id=data.room_id,
        check_in_date=data.check_in_date,
        check_out_date=data.check_out_date,
        total_nights=nights,
        guests_count=data.guests_count,
        special_requests=data.special_requests.strip() if data.special_requests else None,
        booking_status="Confirmed"
    )
    db.add(new_booking)
    db.flush()  # Populates new_booking.id for foreign key reference

    # 6. Billing Calculations (Unit 1: Arithmetic & conditionals)
    room_charges = float(nights * room.price_per_night)
    discount = float(data.discount_amount)

    # Ensure discount does not exceed room charges
    if discount > room_charges:
        discount = room_charges

    taxable_amount = room_charges - discount
    tax_rate = 0.10  # 10% standard hotel tax
    tax_amount = round(taxable_amount * tax_rate, 2)
    total_amount = round(taxable_amount + tax_amount, 2)

    initial_paid = float(data.initial_payment)
    if initial_paid > total_amount:
        initial_paid = total_amount

    # Determine payment status based on amount paid
    if initial_paid >= total_amount:
        payment_status = "Paid"
    elif initial_paid > 0:
        payment_status = "Partially Paid"
    else:
        payment_status = "Pending"

    invoice_number = generate_invoice_number()
    while db.query(Payment).filter(Payment.invoice_number == invoice_number).first():
        invoice_number = generate_invoice_number()

    payment_record = Payment(
        invoice_number=invoice_number,
        booking_id=new_booking.id,
        room_charges=room_charges,
        discount_amount=discount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        amount_paid=initial_paid,
        payment_method=data.payment_method.strip(),
        payment_status=payment_status,
        payment_date=datetime.now() if initial_paid > 0 else None,
        notes=f"Auto-generated invoice on booking creation. Initial payment: {initial_paid}"
    )
    db.add(payment_record)

    db.commit()
    db.refresh(new_booking)
    return new_booking


def get_all_reservations(
    db: Session,
    booking_status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Booking]:
    """
    Retrieve reservations with optional status filter and keyword search.

    Parameters:
        db (Session): Database session.
        booking_status (str, optional): Filter by 'Confirmed', 'Checked-In', 'Checked-Out', 'Cancelled'.
        search (str, optional): Keyword matching booking code, customer name, or room number.

    Returns:
        List[Booking]: Matching reservations list.
    """
    query = db.query(Booking).join(Customer).join(Room)

    if booking_status and booking_status.lower() != "all":
        query = query.filter(Booking.booking_status == booking_status.strip())

    if search:
        kw = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Booking.booking_code.ilike(kw),
                Customer.full_name.ilike(kw),
                Customer.phone.ilike(kw),
                Room.room_number.ilike(kw)
            )
        )

    return query.order_by(Booking.check_in_date.desc(), Booking.id.desc()).all()


def get_reservation_by_id(db: Session, booking_id: int) -> Booking:
    """
    Look up a single reservation by ID.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reservation with ID {booking_id} was not found."
        )
    return booking


def cancel_reservation(db: Session, booking_id: int, reason: Optional[str] = None) -> dict:
    """
    Cancel an existing reservation and release room availability.

    Parameters:
        db (Session): Database session.
        booking_id (int): ID of booking to cancel.
        reason (str, optional): Cancellation reason note.

    Returns:
        dict: Confirmation outcome.
    """
    booking = get_reservation_by_id(db, booking_id)

    if booking.booking_status == "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reservation is already cancelled."
        )

    if booking.booking_status == "Checked-Out":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a reservation that has already checked out."
        )

    # If the booking was currently checked in, set the room back to Available
    if booking.booking_status == "Checked-In":
        room = db.query(Room).filter(Room.id == booking.room_id).first()
        if room and room.status == "Occupied":
            room.status = "Available"

    booking.booking_status = "Cancelled"

    if booking.payment:
        cancellation_note = f"Cancelled on {datetime.now().strftime('%Y-%m-%d %H:%M')}."
        if reason:
            cancellation_note += f" Reason: {reason}"
        booking.payment.notes = (booking.payment.notes or "") + f" | {cancellation_note}"

    db.commit()
    db.refresh(booking)

    return {
        "success": True,
        "message": f"Reservation {booking.booking_code} was successfully cancelled.",
        "booking_code": booking.booking_code
    }
