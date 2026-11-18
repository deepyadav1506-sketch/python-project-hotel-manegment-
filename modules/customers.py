"""
StayHome Hotel Management System - Customer Management Module
File: modules/customers.py

Purpose:
    Handles customer record operations:
    - Adding new customers with email format and uniqueness validation.
    - Retrieving customer lists with search capabilities (name, email, phone).
    - Updating contact information.
    - Safe deletion checking (prevents deleting customers with active stays).

Syllabus Concepts Covered:
    - Unit 1: Functions, return values, typecasting, conditional statements.
    - Unit 2: Dictionaries, String methods (.lower(), .strip()), List comprehensions.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from database.models import Customer, Booking
from schemas.schemas import CustomerCreate, CustomerUpdate, CustomerResponse


def get_all_customers(db: Session, search: Optional[str] = None) -> List[CustomerResponse]:
    """
    Retrieve all customers from the database with optional search filtering.
    Calculates total bookings count for each customer.

    Parameters:
        db (Session): Database session.
        search (str, optional): Search keyword matching name, email, or phone.

    Returns:
        List[CustomerResponse]: Customer data enriched with total booking count.
    """
    query = db.query(Customer)

    # Unit 2: String manipulation for case-insensitive search
    if search:
        search_pattern = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Customer.full_name.ilike(search_pattern),
                Customer.email.ilike(search_pattern),
                Customer.phone.ilike(search_pattern)
            )
        )

    customers = query.order_by(Customer.created_at.desc()).all()

    # Unit 2: List comprehension to build structured responses with booking counts
    response_list = []
    for c in customers:
        booking_count = db.query(Booking).filter(Booking.customer_id == c.id).count()
        response_list.append(
            CustomerResponse(
                id=c.id,
                full_name=c.full_name,
                email=c.email,
                phone=c.phone,
                address=c.address,
                id_proof=c.id_proof,
                created_at=c.created_at,
                total_bookings=booking_count
            )
        )

    return response_list


def get_customer_by_id(db: Session, customer_id: int) -> Customer:
    """
    Find a customer by primary key ID.
    """
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID {customer_id} was not found."
        )
    return customer


def create_customer(db: Session, customer_data: CustomerCreate) -> CustomerResponse:
    """
    Create a new customer profile after verifying email uniqueness.

    Parameters:
        db (Session): Database session.
        customer_data (CustomerCreate): Validated customer details.

    Returns:
        CustomerResponse: Newly created customer record.
    """
    # Unit 2: String sanitization
    clean_email = customer_data.email.strip().lower()
    clean_name = customer_data.full_name.strip()
    clean_phone = customer_data.phone.strip()

    # Check if email is already registered
    existing_customer = db.query(Customer).filter(Customer.email == clean_email).first()
    if existing_customer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A customer with email '{clean_email}' already exists in the system."
        )

    new_customer = Customer(
        full_name=clean_name,
        email=clean_email,
        phone=clean_phone,
        address=customer_data.address.strip() if customer_data.address else None,
        id_proof=customer_data.id_proof.strip() if customer_data.id_proof else None
    )

    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    return CustomerResponse(
        id=new_customer.id,
        full_name=new_customer.full_name,
        email=new_customer.email,
        phone=new_customer.phone,
        address=new_customer.address,
        id_proof=new_customer.id_proof,
        created_at=new_customer.created_at,
        total_bookings=0
    )


def update_customer(db: Session, customer_id: int, update_data: CustomerUpdate) -> CustomerResponse:
    """
    Update existing customer details.
    """
    customer = get_customer_by_id(db, customer_id)
    update_dict = update_data.model_dump(exclude_unset=True)

    # Check email uniqueness if email is being changed
    if "email" in update_dict and update_dict["email"]:
        new_email = update_dict["email"].strip().lower()
        if new_email != customer.email:
            conflict = db.query(Customer).filter(Customer.email == new_email).first()
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email '{new_email}' is already used by another customer."
                )
            customer.email = new_email

    for field, val in update_dict.items():
        if field != "email" and val is not None:
            setattr(customer, field, val.strip() if isinstance(val, str) else val)

    db.commit()
    db.refresh(customer)

    booking_count = db.query(Booking).filter(Booking.customer_id == customer.id).count()
    return CustomerResponse(
        id=customer.id,
        full_name=customer.full_name,
        email=customer.email,
        phone=customer.phone,
        address=customer.address,
        id_proof=customer.id_proof,
        created_at=customer.created_at,
        total_bookings=booking_count
    )


def delete_customer(db: Session, customer_id: int) -> dict:
    """
    Safely delete a customer profile if they have no active bookings.
    """
    customer = get_customer_by_id(db, customer_id)

    # Check for active bookings
    active_stays = db.query(Booking).filter(
        Booking.customer_id == customer_id,
        Booking.booking_status.in_(["Confirmed", "Checked-In"])
    ).count()

    if active_stays > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete customer '{customer.full_name}' because they have {active_stays} active or confirmed reservation(s)."
        )

    deleted_name = customer.full_name
    db.delete(customer)
    db.commit()

    return {
        "success": True,
        "message": f"Customer '{deleted_name}' was successfully removed from the system."
    }
