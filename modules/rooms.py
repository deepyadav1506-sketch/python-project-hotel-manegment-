"""
StayHome Hotel Management System - Room Management Module
File: modules/rooms.py

Purpose:
    Handles all business logic and database queries related to hotel rooms:
    - Creating new rooms with validation.
    - Retrieving rooms with multi-criteria filtering (category, status, search keyword).
    - Updating room specifications and live operational state.
    - Safe deletion checking (prevents deleting rooms with active bookings).
    - Querying available rooms for a given date range.

Syllabus Concepts Covered:
    - Unit 1: Functions, parameters, return statements, if-else conditions.
    - Unit 2: Lists, Dictionaries, String methods (.strip(), .lower()), Sets.
"""

from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from fastapi import HTTPException, status

from database.models import Room, Booking
from schemas.schemas import RoomCreate, RoomUpdate


def get_all_rooms(
    db: Session,
    category: Optional[str] = None,
    room_status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Room]:
    """
    Fetch all hotel rooms from the database with optional filtering and search.

    Parameters:
        db (Session): Active SQLAlchemy database session.
        category (str, optional): Filter by 'Standard', 'Deluxe', or 'Suite'.
        room_status (str, optional): Filter by 'Available', 'Occupied', or 'Maintenance'.
        search (str, optional): Search query to match against room number or amenities.

    Returns:
        List[Room]: List of matching Room ORM objects.
    """
    # Start with base query for all rooms
    query = db.query(Room)

    # Unit 1: Conditional statement (if-else) to filter by room type
    if category and category.lower() != "all":
        query = query.filter(Room.room_type == category.strip())

    # Unit 1: Filter by operational status
    if room_status and room_status.lower() != "all":
        query = query.filter(Room.status == room_status.strip())

    # Unit 2: String manipulation and search filtering
    if search:
        search_cleaned = f"%{search.strip().lower()}%"
        query = query.filter(
            or_(
                Room.room_number.ilike(search_cleaned),
                Room.amenities.ilike(search_cleaned),
                Room.room_type.ilike(search_cleaned)
            )
        )

    # Order rooms logically by room number
    return query.order_by(Room.room_number.asc()).all()


def get_room_by_id(db: Session, room_id: int) -> Room:
    """
    Look up a single room by its unique primary key ID.

    Parameters:
        db (Session): Database session.
        room_id (int): Primary key ID of the room.

    Returns:
        Room: The matched Room ORM object.

    Raises:
        HTTPException: 404 Not Found if no room exists with the given ID.
    """
    room = db.query(Room).filter(Room.id == room_id).first()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Room with ID {room_id} was not found."
        )
    return room


def get_room_by_number(db: Session, room_number: str) -> Optional[Room]:
    """
    Helper function to check if a room number already exists.
    """
    return db.query(Room).filter(Room.room_number == room_number.strip()).first()


def create_room(db: Session, room_data: RoomCreate) -> Room:
    """
    Create a new room in the database after validating uniqueness.

    Parameters:
        db (Session): Database session.
        room_data (RoomCreate): Validated room attributes from request body.

    Returns:
        Room: Newly inserted Room record.

    Raises:
        HTTPException: 400 Bad Request if room number already exists.
    """
    # Unit 2: String stripping to sanitize input
    clean_number = room_data.room_number.strip()

    # Check for duplicate room number
    existing_room = get_room_by_number(db, clean_number)
    if existing_room:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Room number '{clean_number}' already exists in the system."
        )

    # Unit 1: Instantiate ORM Model and save to DB
    new_room = Room(
        room_number=clean_number,
        room_type=room_data.room_type.strip(),
        price_per_night=float(room_data.price_per_night),
        capacity=int(room_data.capacity),
        status=room_data.status.strip(),
        amenities=room_data.amenities.strip() if room_data.amenities else "Standard Amenities"
    )

    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    return new_room


def update_room(db: Session, room_id: int, update_data: RoomUpdate) -> Room:
    """
    Update existing room attributes.

    Parameters:
        db (Session): Database session.
        room_id (int): Primary key ID of the room to update.
        update_data (RoomUpdate): Fields to update.

    Returns:
        Room: The updated room record.
    """
    room = get_room_by_id(db, room_id)

    # Unit 2: Dictionary iteration over provided non-null fields
    update_dict = update_data.model_dump(exclude_unset=True)

    # If updating room_number, verify it doesn't conflict with another room
    if "room_number" in update_dict and update_dict["room_number"]:
        target_number = update_dict["room_number"].strip()
        if target_number != room.room_number:
            conflict = get_room_by_number(db, target_number)
            if conflict:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Room number '{target_number}' is already assigned to another room."
                )
            room.room_number = target_number

    # Apply other fields dynamically
    for field_name, value in update_dict.items():
        if field_name != "room_number" and value is not None:
            setattr(room, field_name, value)

    db.commit()
    db.refresh(room)
    return room


def delete_room(db: Session, room_id: int) -> dict:
    """
    Safely delete a room if it has no active bookings.

    Parameters:
        db (Session): Database session.
        room_id (int): Primary key ID of room to delete.

    Returns:
        dict: Success confirmation message.

    Raises:
        HTTPException: 400 Bad Request if room is currently occupied or reserved.
    """
    room = get_room_by_id(db, room_id)

    # Safe deletion check: Cannot delete room with active bookings
    active_bookings_count = db.query(Booking).filter(
        Booking.room_id == room_id,
        Booking.booking_status.in_(["Confirmed", "Checked-In"])
    ).count()

    if active_bookings_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete Room {room.room_number} because it has {active_bookings_count} active/upcoming reservation(s). Cancel the reservations first."
        )

    deleted_number = room.room_number
    db.delete(room)
    db.commit()

    return {
        "success": True,
        "message": f"Room {deleted_number} was successfully deleted from the system."
    }


def get_available_rooms_for_dates(
    db: Session,
    check_in: date,
    check_out: date,
    room_type: Optional[str] = None
) -> List[Room]:
    """
    Find all rooms that do NOT have any overlapping active reservations
    between check_in and check_out dates, and are not under maintenance.

    Parameters:
        db (Session): Database session.
        check_in (date): Target arrival date.
        check_out (date): Target departure date.
        room_type (str, optional): Target room category.

    Returns:
        List[Room]: Available room records ready for booking.
    """
    # Unit 1: Input validation
    if check_in >= check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Check-in date must be strictly before check-out date."
        )

    # Find room IDs with overlapping active reservations
    # Mathematical overlap formula:
    # Existing booking overlaps if (existing.check_in < requested.check_out)
    # AND (existing.check_out > requested.check_in)
    occupied_room_ids_subquery = db.query(Booking.room_id).filter(
        Booking.booking_status.in_(["Confirmed", "Checked-In"]),
        Booking.check_in_date < check_out,
        Booking.check_out_date > check_in
    ).subquery()

    # Query rooms that are NOT in the occupied list and NOT in Maintenance
    query = db.query(Room).filter(
        ~Room.id.in_(occupied_room_ids_subquery),
        Room.status != "Maintenance"
    )

    if room_type and room_type.lower() != "all":
        query = query.filter(Room.room_type == room_type.strip())

    return query.order_by(Room.room_number.asc()).all()
