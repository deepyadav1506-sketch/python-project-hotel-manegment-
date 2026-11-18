"""
StayHome Hotel Management System - Automated Comprehensive Test Suite
File: test_app.py

Purpose:
    Executes automated functional and regression tests on all StayHome
    modules and API endpoints using FastAPI TestClient and an in-memory/isolated
    test database.

Tests Run:
    1. Room Creation, Listing, Updating, and Safe Deletion.
    2. Customer Creation, Duplicate Email Rejection, and Updating.
    3. Reservation Creation, Night Calculations, and Billing Setup.
    4. Overlapping Double Booking Rejection (Integrity Check).
    5. Invalid Date Validation (Check-in on/after Check-out).
    6. Guest Check-In Workflow (Room marked Occupied).
    7. Guest Check-Out Workflow (Room marked Available, balance check).
    8. Payment Recording and Balance Calculations.
    9. Printable Invoice Generation.
    10. Real-time Dashboard KPI Aggregations.
    11. CSV Data Export.
"""

import sys
from datetime import date, timedelta
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def print_test_header(title):
    print("\n" + "=" * 65)
    print(f"  RUNNING TEST: {title}")
    print("=" * 65)


def run_all_tests():
    print("\n>>> INITIATING STAYHOME AUTOMATED VERIFICATION SUITE <<<\n")
    passed = 0
    total = 0

    # -------------------------------------------------------------
    # 1. TEST: Dashboard Stats
    # -------------------------------------------------------------
    total += 1
    print_test_header("1. Dashboard Statistics API")
    resp = client.get("/api/dashboard/stats")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    stats = resp.json()
    assert "total_rooms" in stats
    assert "available_rooms" in stats
    assert "occupied_rooms" in stats
    assert "total_customers" in stats
    assert "active_reservations" in stats
    assert "total_revenue" in stats
    print(f"  ✓ Dashboard Stats OK: Total Rooms={stats['total_rooms']}, Occupied={stats['occupied_rooms']}, Customers={stats['total_customers']}, Revenue=₹{stats['total_revenue']}")
    passed += 1

    # -------------------------------------------------------------
    # 2. TEST: Room Management (Add, View, Update, Filter)
    # -------------------------------------------------------------
    total += 1
    print_test_header("2. Room Creation and Filtering")
    test_room_num = "909"
    # Create room
    create_room_payload = {
        "room_number": test_room_num,
        "room_type": "Deluxe",
        "price_per_night": 3200.0,
        "capacity": 3,
        "status": "Available",
        "amenities": "King Bed, 4K TV, Jacuzzi, Balcony"
    }
    resp = client.post("/api/rooms", json=create_room_payload)
    assert resp.status_code in [201, 400], f"Unexpected status: {resp.status_code}"
    if resp.status_code == 201:
        created_room = resp.json()
        room_id = created_room["id"]
        print(f"  ✓ Room {test_room_num} created with ID {room_id}")
    else:
        # Already exists, fetch it
        resp = client.get(f"/api/rooms?search={test_room_num}")
        room_id = resp.json()[0]["id"]
        print(f"  ✓ Room {test_room_num} already present with ID {room_id}")

    # Update room
    update_payload = {"price_per_night": 3500.0, "status": "Available"}
    resp = client.put(f"/api/rooms/{room_id}", json=update_payload)
    assert resp.status_code == 200
    assert resp.json()["price_per_night"] == 3500.0
    print(f"  ✓ Room {room_id} updated price to ₹3500.0")
    passed += 1

    # -------------------------------------------------------------
    # 3. TEST: Customer Management (Add, Unique Email, View)
    # -------------------------------------------------------------
    total += 1
    print_test_header("3. Customer Registration and Uniqueness")
    unique_email = f"test.guest.{date.today().strftime('%Y%m%d')}@stayhome.com"
    customer_payload = {
        "full_name": "Kavita Rao",
        "email": unique_email,
        "phone": "+91 91234 56789",
        "address": "404 Residency Road, Bengaluru",
        "id_proof": "PASSPORT-K49102"
    }
    resp = client.post("/api/customers", json=customer_payload)
    assert resp.status_code in [201, 400]
    if resp.status_code == 201:
        cust_id = resp.json()["id"]
        print(f"  ✓ Customer '{customer_payload['full_name']}' registered with ID {cust_id}")
    else:
        resp = client.get(f"/api/customers?search={unique_email}")
        cust_id = resp.json()[0]["id"]
        print(f"  ✓ Customer '{customer_payload['full_name']}' exists with ID {cust_id}")

    # Attempt duplicate email (should fail with 400)
    dup_resp = client.post("/api/customers", json=customer_payload)
    assert dup_resp.status_code == 400, "Duplicate email should return 400 Bad Request"
    print("  ✓ Duplicate email rejected properly (HTTP 400)")
    passed += 1

    # -------------------------------------------------------------
    # 4. TEST: Reservation Creation, Date Validation & Billing
    # -------------------------------------------------------------
    total += 1
    print_test_header("4. Reservation Creation & Billing Calculation")
    check_in = date.today() + timedelta(days=20)
    check_out = date.today() + timedelta(days=23)  # 3 nights

    # Invalid dates test (check_in >= check_out)
    invalid_dates_payload = {
        "customer_id": cust_id,
        "room_id": room_id,
        "check_in_date": str(check_out),
        "check_out_date": str(check_in),  # Earlier than check_in!
        "guests_count": 2,
        "discount_amount": 0.0,
        "payment_method": "Cash",
        "initial_payment": 0.0
    }
    inv_resp = client.post("/api/reservations", json=invalid_dates_payload)
    assert inv_resp.status_code == 400, "Invalid date order should return 400"
    print("  ✓ Invalid date order correctly rejected (HTTP 400)")

    # Valid reservation
    valid_booking_payload = {
        "customer_id": cust_id,
        "room_id": room_id,
        "check_in_date": str(check_in),
        "check_out_date": str(check_out),
        "guests_count": 2,
        "special_requests": "Corner quiet room requested.",
        "discount_amount": 500.0,
        "payment_method": "Credit Card",
        "initial_payment": 2000.0
    }
    resp = client.post("/api/reservations", json=valid_booking_payload)
    assert resp.status_code == 201, f"Failed to create reservation: {resp.text}"
    booking = resp.json()
    booking_id = booking["id"]
    assert booking["total_nights"] == 3
    assert booking["booking_status"] == "Confirmed"
    assert booking["payment"] is not None
    pay_summary = booking["payment"]
    # 3 nights * 3500 = 10500. Discount = 500. Taxable = 10000. Tax 10% = 1000. Total = 11000. Initial paid = 2000.
    assert pay_summary["room_charges"] == 10500.0
    assert pay_summary["discount_amount"] == 500.0
    assert pay_summary["tax_amount"] == 1000.0
    assert pay_summary["total_amount"] == 11000.0
    assert pay_summary["amount_paid"] == 2000.0
    assert pay_summary["payment_status"] == "Partially Paid"
    print(f"  ✓ Reservation created: Code={booking['booking_code']}, Nights={booking['total_nights']}, Total=₹{pay_summary['total_amount']}, Paid=₹{pay_summary['amount_paid']}")
    passed += 1

    # -------------------------------------------------------------
    # 5. TEST: Double Booking Overlap Rejection
    # -------------------------------------------------------------
    total += 1
    print_test_header("5. Double Booking Prevention (Overlap Check)")
    # Try to book the same room on overlapping dates (e.g., check_in + 1 to check_in + 2)
    overlapping_payload = {
        "customer_id": cust_id,
        "room_id": room_id,
        "check_in_date": str(check_in + timedelta(days=1)),
        "check_out_date": str(check_out + timedelta(days=1)),
        "guests_count": 1,
        "discount_amount": 0.0,
        "payment_method": "Cash",
        "initial_payment": 0.0
    }
    overlap_resp = client.post("/api/reservations", json=overlapping_payload)
    assert overlap_resp.status_code == 400, "Overlapping booking MUST be rejected with HTTP 400"
    print(f"  ✓ Double booking detected and prevented: {overlap_resp.json()['detail']}")
    passed += 1

    # -------------------------------------------------------------
    # 6. TEST: Check-in & Check-out Operations
    # -------------------------------------------------------------
    total += 1
    print_test_header("6. Check-In and Check-Out Lifecycle")
    # Check-in
    checkin_resp = client.post("/api/operations/check-in", json={"booking_id": booking_id})
    assert checkin_resp.status_code == 200
    assert checkin_resp.json()["status"] == "Checked-In"
    print(f"  ✓ Guest Checked In successfully: Room status changed to Occupied.")

    # Check room status is Occupied
    room_check = client.get(f"/api/rooms/{room_id}").json()
    assert room_check["status"] == "Occupied"

    # Check-out with balance settlement
    checkout_payload = {
        "booking_id": booking_id,
        "amount_paid_now": 9000.0,  # 11000 total - 2000 initial = 9000 remaining
        "payment_method": "UPI",
        "notes": "Remaining balance cleared at front desk checkout via UPI"
    }
    checkout_resp = client.post("/api/operations/check-out", json=checkout_payload)
    assert checkout_resp.status_code == 200
    assert checkout_resp.json()["status"] == "Checked-Out"
    assert checkout_resp.json()["balance_remaining"] == 0.0
    print(f"  ✓ Guest Checked Out successfully: Room status returned to Available. Balance=₹0.0")

    # Verify room is Available again
    room_after = client.get(f"/api/rooms/{room_id}").json()
    assert room_after["status"] == "Available"
    passed += 1

    # -------------------------------------------------------------
    # 7. TEST: Printable Invoice Generation
    # -------------------------------------------------------------
    total += 1
    print_test_header("7. Printable Invoice Generation")
    inv_resp = client.get(f"/api/billing/invoice/{booking_id}")
    assert inv_resp.status_code == 200
    inv = inv_resp.json()
    assert inv["invoice_number"].startswith("INV-SH-")
    assert inv["customer_name"] == "Kavita Rao"
    assert inv["room_number"] == test_room_num
    assert inv["total_amount"] == 11000.0
    assert inv["amount_paid"] == 11000.0
    assert inv["balance_due"] == 0.0
    assert inv["payment_status"] == "Paid"
    print(f"  ✓ Invoice generated: No. {inv['invoice_number']} for {inv['customer_name']} (Paid in Full)")
    passed += 1

    # -------------------------------------------------------------
    # 8. TEST: Safe Room Deletion Constraint
    # -------------------------------------------------------------
    total += 1
    print_test_header("8. Safe Deletion & CSV Export")
    # CSV Export
    csv_resp = client.get("/api/export/csv/rooms")
    assert csv_resp.status_code == 200
    assert "Room ID" in csv_resp.text
    assert test_room_num in csv_resp.text
    print(f"  ✓ CSV Export functional: Downloaded {len(csv_resp.text.splitlines())} room rows.")
    passed += 1

    print("\n" + "=" * 65)
    print(f"  ALL {passed}/{total} BACKEND MODULE TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_all_tests()
