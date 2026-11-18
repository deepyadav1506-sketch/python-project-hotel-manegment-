"""
StayHome Hotel Management System - Database Initialization & Seed Data
File: database/init_db.py

Purpose:
    Creates all database tables according to SQLAlchemy models and populates
    realistic initial data (rooms, customers, bookings, payments) if the tables
    are empty. This ensures a clean out-of-the-box demo experience for faculty
    and student presentations.

Syllabus Concepts Covered:
    - Dictionaries, Lists of Dictionaries.
    - Loop constructs (for loops).
    - Function definitions with default arguments.
    - Exception handling (try-except-finally).
    - Date and time arithmetic using datetime.date and timedelta.
"""

from datetime import date, timedelta, datetime
from database.database import engine, SessionLocal, Base
from database.models import Room, Customer, Booking, Payment


def init_db():
    """
    Initializes database tables and seeds demo records if database is empty.
    Returns:
        dict: Summary of seeded record counts.
    """
    # Create all tables defined in models.py if they don't already exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if rooms table already has data
        existing_rooms_count = db.query(Room).count()
        if existing_rooms_count > 0:
            print(f"[StayHome DB] Database already contains {existing_rooms_count} rooms. Skipping initial seed.")
            return {"status": "already_initialized", "rooms": existing_rooms_count}

        print("[StayHome DB] Empty database detected. Seeding sample rooms, customers, bookings, and payments...")

        # -------------------------------------------------------------
        # 1. Seed Rooms (Unit 2: Lists of Dictionaries)
        # -------------------------------------------------------------
        seed_rooms = [
            {"room_number": "101", "room_type": "Standard", "price_per_night": 1500.0, "capacity": 2, "status": "Available", "amenities": "Queen Bed, Wi-Fi, AC, Work Desk, Kettle"},
            {"room_number": "102", "room_type": "Standard", "price_per_night": 1500.0, "capacity": 2, "status": "Occupied", "amenities": "Twin Beds, Wi-Fi, AC, TV"},
            {"room_number": "103", "room_type": "Standard", "price_per_night": 1500.0, "capacity": 1, "status": "Available", "amenities": "Single Bed, Wi-Fi, Fan, Work Desk"},
            {"room_number": "201", "room_type": "Deluxe", "price_per_night": 2800.0, "capacity": 2, "status": "Available", "amenities": "King Bed, Balcony, City View, Wi-Fi, Smart TV, Mini Fridge"},
            {"room_number": "202", "room_type": "Deluxe", "price_per_night": 2800.0, "capacity": 3, "status": "Available", "amenities": "King Bed + Sofa Bed, Balcony, Wi-Fi, Smart TV, Mini Bar"},
            {"room_number": "203", "room_type": "Deluxe", "price_per_night": 2800.0, "capacity": 2, "status": "Maintenance", "amenities": "King Bed, Garden View, Wi-Fi, Air Conditioning"},
            {"room_number": "301", "room_type": "Suite", "price_per_night": 5500.0, "capacity": 4, "status": "Available", "amenities": "Master Bedroom, Living Room, Jacuzzi, Ocean View, Butler Service"},
            {"room_number": "302", "room_type": "Suite", "price_per_night": 5500.0, "capacity": 4, "status": "Available", "amenities": "2 King Bedrooms, Kitchenette, Panoramic View, Smart Automation"},
            {"room_number": "104", "room_type": "Standard", "price_per_night": 1600.0, "capacity": 2, "status": "Available", "amenities": "Queen Bed, Wi-Fi, AC, Coffee Maker"},
            {"room_number": "204", "room_type": "Deluxe", "price_per_night": 3000.0, "capacity": 3, "status": "Available", "amenities": "King Bed, Mountain View, Breakfast Included, Smart TV"}
        ]

        created_rooms = []
        for r_data in seed_rooms:
            room = Room(**r_data)
            db.add(room)
            created_rooms.append(room)
        db.flush()  # Generates room IDs

        # -------------------------------------------------------------
        # 2. Seed Customers
        # -------------------------------------------------------------
        seed_customers = [
            {"full_name": "Aarav Sharma", "email": "aarav.sharma@example.com", "phone": "+91 98765 43210", "address": "Flat 402, Green Glen Heights, Bengaluru, Karnataka", "id_proof": "PASSPORT-A9812401"},
            {"full_name": "Priya Nair", "email": "priya.nair@example.com", "phone": "+91 98230 11223", "address": "12/A Marine Drive, Kochi, Kerala", "id_proof": "AADHAAR-8823-1029-4411"},
            {"full_name": "Rohan Deshmukh", "email": "rohan.d@example.com", "phone": "+91 97654 32109", "address": "55 Shivaji Park, Dadar, Mumbai, Maharashtra", "id_proof": "DL-MH01-2019-00341"},
            {"full_name": "Sneha Mukherjee", "email": "sneha.m@example.com", "phone": "+91 98112 99887", "address": "Plot 8, Salt Lake Sector V, Kolkata, West Bengal", "id_proof": "PASSPORT-Z7721890"},
            {"full_name": "Vikram Patel", "email": "vikram.patel@example.com", "phone": "+91 99001 22334", "address": "Sector 14, Gandhinagar, Gujarat", "id_proof": "AADHAAR-5512-8877-9922"}
        ]

        created_customers = []
        for c_data in seed_customers:
            customer = Customer(**c_data)
            db.add(customer)
            created_customers.append(customer)
        db.flush()  # Generates customer IDs

        # -------------------------------------------------------------
        # 3. Seed Bookings & Invoices
        # -------------------------------------------------------------
        today = date.today()

        # Booking 1: Currently Occupied stay (Checked-In yesterday, checking out in 2 days)
        booking1 = Booking(
            booking_code="SH-BK-1001",
            customer_id=created_customers[0].id,
            room_id=created_rooms[1].id,  # Room 102 (Occupied)
            check_in_date=today - timedelta(days=1),
            check_out_date=today + timedelta(days=2),
            total_nights=3,
            guests_count=2,
            special_requests="Late check-in requested and quiet room preference.",
            booking_status="Checked-In"
        )
        db.add(booking1)
        db.flush()

        payment1 = Payment(
            invoice_number="INV-SH-1001",
            booking_id=booking1.id,
            room_charges=1500.0 * 3,  # 4500.0
            discount_amount=200.0,
            tax_amount=(4500.0 - 200.0) * 0.10,  # 430.0 (10% tax)
            total_amount=4500.0 - 200.0 + 430.0,  # 4730.0
            amount_paid=4730.0,
            payment_method="UPI",
            payment_status="Paid",
            payment_date=datetime.now() - timedelta(days=1),
            notes="Paid in full via GPay QR at front desk."
        )
        db.add(payment1)

        # Booking 2: Upcoming stay starting Today (Confirmed)
        booking2 = Booking(
            booking_code="SH-BK-1002",
            customer_id=created_customers[1].id,
            room_id=created_rooms[3].id,  # Room 201 (Deluxe)
            check_in_date=today,
            check_out_date=today + timedelta(days=3),
            total_nights=3,
            guests_count=2,
            special_requests="Extra bath towels and high floor.",
            booking_status="Confirmed"
        )
        db.add(booking2)
        db.flush()

        payment2 = Payment(
            invoice_number="INV-SH-1002",
            booking_id=booking2.id,
            room_charges=2800.0 * 3,  # 8400.0
            discount_amount=400.0,
            tax_amount=(8400.0 - 400.0) * 0.10,  # 800.0
            total_amount=8400.0 - 400.0 + 800.0,  # 8800.0
            amount_paid=4400.0,
            payment_method="Credit Card",
            payment_status="Partially Paid",
            payment_date=datetime.now() - timedelta(days=2),
            notes="50% advance deposit paid online via Visa."
        )
        db.add(payment2)

        # Booking 3: Past completed stay (Checked-Out)
        booking3 = Booking(
            booking_code="SH-BK-1003",
            customer_id=created_customers[2].id,
            room_id=created_rooms[0].id,  # Room 101
            check_in_date=today - timedelta(days=5),
            check_out_date=today - timedelta(days=2),
            total_nights=3,
            guests_count=1,
            special_requests="Airport pickup assistance.",
            booking_status="Checked-Out"
        )
        db.add(booking3)
        db.flush()

        payment3 = Payment(
            invoice_number="INV-SH-1003",
            booking_id=booking3.id,
            room_charges=1500.0 * 3,  # 4500.0
            discount_amount=0.0,
            tax_amount=4500.0 * 0.10,  # 450.0
            total_amount=4950.0,
            amount_paid=4950.0,
            payment_method="Cash",
            payment_status="Paid",
            payment_date=datetime.now() - timedelta(days=2),
            notes="Settled fully in cash upon checkout."
        )
        db.add(payment3)

        # Booking 4: Future stay (Confirmed)
        booking4 = Booking(
            booking_code="SH-BK-1004",
            customer_id=created_customers[3].id,
            room_id=created_rooms[6].id,  # Room 301 Suite
            check_in_date=today + timedelta(days=2),
            check_out_date=today + timedelta(days=6),
            total_nights=4,
            guests_count=3,
            special_requests="Anniversary floral arrangement in room.",
            booking_status="Confirmed"
        )
        db.add(booking4)
        db.flush()

        payment4 = Payment(
            invoice_number="INV-SH-1004",
            booking_id=booking4.id,
            room_charges=5500.0 * 4,  # 22000.0
            discount_amount=1000.0,
            tax_amount=(22000.0 - 1000.0) * 0.10,  # 2100.0
            total_amount=22000.0 - 1000.0 + 2100.0,  # 23100.0
            amount_paid=0.0,
            payment_method="Credit Card",
            payment_status="Pending",
            payment_date=None,
            notes="Pay on arrival."
        )
        db.add(payment4)

        db.commit()
        print("[StayHome DB] Seed data inserted successfully!")
        return {
            "status": "success",
            "rooms_created": len(created_rooms),
            "customers_created": len(created_customers),
            "bookings_created": 4,
            "payments_created": 4
        }
    except Exception as e:
        db.rollback()
        print(f"[StayHome DB] Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
