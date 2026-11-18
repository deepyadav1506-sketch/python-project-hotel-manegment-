"""
StayHome Hotel Management System - Billing & Payment Module
File: modules/billing.py

Purpose:
    Handles financial transactions, bill calculations, and invoice generation:
    - Accurate pricing breakdown (room charges = nights * price_per_night).
    - Promotional discount application.
    - Government/Hotel service tax calculation (10%).
    - Payment recording (cash, credit card, UPI, bank transfer).
    - Printable invoice generation with itemized charges and balance due.

Syllabus Concepts Covered:
    - Unit 1: Functions, parameters, return statements, mathematical operations,
      type conversions (float, int), if-elif-else logic.
    - Unit 2: Dictionaries, String formatting, Data aggregation.
"""

from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from database.models import Payment, Booking, Customer, Room
from schemas.schemas import PaymentRecordRequest, InvoiceResponse


def get_all_payments(
    db: Session,
    payment_status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Payment]:
    """
    Retrieve all payments/invoices with optional status filter and search.

    Parameters:
        db (Session): Database session.
        payment_status (str, optional): 'Paid', 'Partially Paid', or 'Pending'.
        search (str, optional): Search keyword matching invoice number or customer name.

    Returns:
        List[Payment]: Matching payments list.
    """
    query = db.query(Payment).join(Booking).join(Customer)

    if payment_status and payment_status.lower() != "all":
        query = query.filter(Payment.payment_status == payment_status.strip())

    if search:
        kw = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Payment.invoice_number.ilike(kw),
                Customer.full_name.ilike(kw),
                Booking.booking_code.ilike(kw)
            )
        )

    return query.order_by(Payment.id.desc()).all()


def get_payment_by_id(db: Session, payment_id: int) -> Payment:
    """
    Look up a single payment by its primary key ID.
    """
    payment = db.query(Payment).filter(Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment record with ID {payment_id} was not found."
        )
    return payment


def record_payment(
    db: Session,
    booking_id: int,
    payment_data: PaymentRecordRequest
) -> Payment:
    """
    Record an additional payment against a booking's invoice.

    Parameters:
        db (Session): Database session.
        booking_id (int): Booking ID associated with the payment.
        payment_data (PaymentRecordRequest): Amount paid and method.

    Returns:
        Payment: Updated payment record.

    Raises:
        HTTPException: 400 Bad Request if payment exceeds balance due or invalid.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} was not found."
        )

    payment = booking.payment
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice record not found for this booking."
        )

    amount_to_add = float(payment_data.amount)
    if amount_to_add <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than zero."
        )

    balance_due = payment.total_amount - payment.amount_paid
    if amount_to_add > balance_due + 0.01:  # 0.01 float tolerance
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment amount of ₹{amount_to_add:.2f} exceeds outstanding balance of ₹{balance_due:.2f}."
        )

    # Unit 1: Arithmetic update and conditional logic
    payment.amount_paid = round(payment.amount_paid + amount_to_add, 2)
    payment.payment_method = payment_data.payment_method.strip()
    payment.payment_date = datetime.now()

    # Update payment status
    if payment.amount_paid >= payment.total_amount:
        payment.payment_status = "Paid"
    elif payment.amount_paid > 0:
        payment.payment_status = "Partially Paid"
    else:
        payment.payment_status = "Pending"

    # Append note
    new_note = f"Received ₹{amount_to_add:.2f} via {payment_data.payment_method} on {datetime.now().strftime('%Y-%m-%d %H:%M')}."
    if payment_data.notes:
        new_note += f" Note: {payment_data.notes}"
    payment.notes = (payment.notes or "") + f" | {new_note}"

    db.commit()
    db.refresh(payment)
    return payment


def generate_invoice_data(db: Session, booking_id: int) -> InvoiceResponse:
    """
    Compiles full invoice details for printing and display.

    Parameters:
        db (Session): Database session.
        booking_id (int): Target booking ID.

    Returns:
        InvoiceResponse: Complete printable invoice data dictionary.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with ID {booking_id} was not found."
        )

    customer = booking.customer
    room = booking.room
    payment = booking.payment

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No payment record found for this booking."
        )

    # Calculate balance due
    balance_due = max(0.0, round(payment.total_amount - payment.amount_paid, 2))

    return InvoiceResponse(
        invoice_number=payment.invoice_number,
        booking_code=booking.booking_code,
        invoice_date=datetime.now().strftime("%B %d, %Y"),
        customer_name=customer.full_name,
        customer_email=customer.email,
        customer_phone=customer.phone,
        customer_address=customer.address or "Address not provided",
        room_number=room.room_number,
        room_type=room.room_type,
        price_per_night=room.price_per_night,
        check_in_date=booking.check_in_date.strftime("%Y-%m-%d"),
        check_out_date=booking.check_out_date.strftime("%Y-%m-%d"),
        total_nights=booking.total_nights,
        guests_count=booking.guests_count,
        room_charges=payment.room_charges,
        discount_amount=payment.discount_amount,
        tax_rate_percent=10.0,
        tax_amount=payment.tax_amount,
        total_amount=payment.total_amount,
        amount_paid=payment.amount_paid,
        balance_due=balance_due,
        payment_status=payment.payment_status,
        payment_method=payment.payment_method,
        notes=payment.notes
    )
