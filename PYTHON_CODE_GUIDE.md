# StayHome: Comprehensive Python Code Guide & Viva Preparation

> **Course:** Introduction to Python Programming  
> **Target Audience:** Third-Semester Artificial Intelligence & Data Science Student  
> **Project:** StayHome - Python-Based Hotel Management System  

---

## Table of Contents
1. [Architecture & Project Overview](#1-architecture--project-overview)
2. [How FastAPI Works in StayHome](#2-how-fastapi-works-in-stayhome)
3. [How the Database Connection Works (database.py)](#3-how-the-database-connection-works)
4. [How SQLAlchemy Models Represent Relational Tables (models.py)](#4-how-sqlalchemy-models-represent-relational-tables)
5. [Database Initialization & Demo Seeding (init_db.py)](#5-database-initialization--demo-seeding)
6. [Room Management Logic (rooms.py)](#6-room-management-logic)
7. [Customer Management Logic (customers.py)](#7-customer-management-logic)
8. [Room Availability Calculation & Overlap Formula (reservations.py)](#8-room-availability-calculation--overlap-formula)
9. [Reservation Creation & Validation Pipeline (reservations.py)](#9-reservation-creation--validation-pipeline)
10. [Billing, Tax & Discount Calculations (billing.py)](#10-billing-tax--discount-calculations)
11. [Front Desk Operations: Check-In & Check-Out (operations.py)](#11-front-desk-operations-check-in--check-out)
12. [How Frontend JavaScript Communicates with Python APIs](#12-how-frontend-javascript-communicates-with-python-apis)
13. [Python Syllabus Mapping (Unit 1 & Unit 2)](#13-python-syllabus-mapping-unit-1--unit-2)
14. [Crucial Code Snippets with Line-by-Line Explanations](#14-crucial-code-snippets-with-line-by-line-explanations)
15. [High-Yield Viva Questions and Model Answers](#15-high-yield-viva-questions-and-model-answers)

---

## 1. Architecture & Project Overview

The **StayHome** system is engineered using a clean **Three-Tier Architecture**:

```
+-------------------------------------------------------------+
|                     PRESENTATION TIER                       |
|   HTML5 Semantic Structure + CSS3 Navy Theme + app.js SPA   |
+-------------------------------------------------------------+
                              |
                     HTTP Fetch (JSON REST)
                              |
                              v
+-------------------------------------------------------------+
|                     APPLICATION TIER                        |
|   FastAPI Web Framework (main.py)                           |
|   Business Modules (rooms, customers, reservations, etc.)  |
|   Pydantic Data Validation (schemas/schemas.py)             |
+-------------------------------------------------------------+
                              |
                    SQLAlchemy ORM Queries
                              |
                              v
+-------------------------------------------------------------+
|                       DATABASE TIER                         |
|   Local: SQLite (stayhome.db)                               |
|   Production: Cloud PostgreSQL (Neon Serverless)            |
+-------------------------------------------------------------+
```

### Why this architecture was chosen:
1. **Separation of Concerns:** Business logic (room charges, availability checks) is kept isolated from HTTP routing (`main.py`) and presentation code (`index.html`).
2. **Pedagogical Clarity:** A student can explain how data enters as a JSON payload, is validated by Pydantic, processed by plain Python functions, and persisted through SQLAlchemy.
3. **Dual-Database Capability:** Allows offline development with zero-config SQLite, while remaining 100% production-ready for Neon PostgreSQL on Vercel.

---

## 2. How FastAPI Works in StayHome

FastAPI is an asynchronous web framework built on top of Starlette and Pydantic. In this project, FastAPI performs four critical jobs:

1. **Routing:** Maps incoming HTTP URLs (like `GET /api/rooms` or `POST /api/reservations`) to specific Python functions.
2. **Request Deserialization & Validation:** Reads JSON strings sent by browser fetch requests, converting them into validated Python objects using Pydantic schemas.
3. **Dependency Injection:** Supplies an isolated database session (`SessionLocal`) to each request via `Depends(get_db)` and ensures it is safely closed when the function finishes.
4. **Response Serialization:** Automatically converts Python lists, dictionaries, or ORM models into HTTP JSON responses with appropriate HTTP status codes (200 OK, 201 Created, 400 Bad Request, 404 Not Found).

---

## 3. How the Database Connection Works

### File: `database/database.py`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./stayhome.db")
```

### Explanation:
1. **Environment Awareness:** The code checks for an environment variable named `DATABASE_URL`.
   - On the local computer, `DATABASE_URL` is omitted, so Python defaults to `sqlite:///./stayhome.db`.
   - On Vercel, `DATABASE_URL` is set to the Neon PostgreSQL connection string.
2. **PostgreSQL URI Normalization:** Cloud providers (like Neon or Supabase) often provide strings starting with `postgres://`. SQLAlchemy requires `postgresql://`. The code cleanly replaces this prefix:
   ```python
   if DATABASE_URL.startswith("postgres://"):
       DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
   ```
3. **Thread Safety for SQLite:**
   ```python
   connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
   ```
   FastAPI uses multiple background threads. SQLite by default restricts access to the thread that opened it. Setting `check_same_thread: False` prevents multi-threading errors.
4. **The `get_db()` Generator:**
   ```python
   def get_db():
       db = SessionLocal()
       try:
           yield db
       finally:
           db.close()
   ```
   - `SessionLocal()` creates a new database connection session.
   - `yield db` gives the session to the FastAPI endpoint function.
   - The `finally:` block executes after the endpoint completes, closing the connection and preventing memory or database connection pool leaks.

---

## 4. How SQLAlchemy Models Represent Relational Tables

### File: `database/models.py`

SQLAlchemy uses **Declarative Base Mapping**. A Python class represents a database table, and class attributes represent table columns.

### Relational Schema Diagram:
```
+--------------------+            +------------------------+
|      ROOMS         |            |       CUSTOMERS        |
+--------------------+            +------------------------+
| id (PK)            | 1        1 | id (PK)                |
| room_number        |            | full_name              |
| room_type          |            | email (Unique)         |
| price_per_night    |            | phone                  |
| status             |            | address                |
+---------+----------+            +-----------+------------+
          | 1                                 | 1
          |                                   |
          | M                                 | M
+---------v-----------------------------------v------------+
|                        BOOKINGS                          |
+----------------------------------------------------------+
| id (PK)                                                  |
| booking_code (Unique, e.g. SH-202611-1001)               |
| customer_id (FK -> customers.id)                         |
| room_id (FK -> rooms.id)                                 |
| check_in_date                                            |
| check_out_date                                           |
| total_nights                                             |
| booking_status ('Confirmed', 'Checked-In', etc.)         |
+---------------------------+------------------------------+
                            | 1
                            | 1
+---------------------------v------------------------------+
|                        PAYMENTS                          |
+----------------------------------------------------------+
| id (PK)                                                  |
| invoice_number (Unique, e.g. INV-SH-1001)                |
| booking_id (FK -> bookings.id, Unique)                   |
| room_charges                                             |
| discount_amount                                          |
| tax_amount                                               |
| total_amount                                             |
| amount_paid                                              |
| payment_status ('Pending', 'Partially Paid', 'Paid')     |
+----------------------------------------------------------+
```

### Table Relationships Explained:
- **One-to-Many (`Customer` &rarr; `Booking`):** One customer can make multiple bookings over their lifetime.
- **One-to-Many (`Room` &rarr; `Booking`):** One room can be booked multiple times across different dates.
- **One-to-One (`Booking` &rarr; `Payment`):** Every booking has exactly one primary financial invoice/payment record (`uselist=False`).

---

## 5. Database Initialization & Demo Seeding

### File: `database/init_db.py`

This file handles startup setup:
1. `Base.metadata.create_all(bind=engine)` issues the SQL `CREATE TABLE IF NOT EXISTS` statements for all defined models.
2. It counts existing rooms (`db.query(Room).count()`). If the count is 0, it seeds:
   - 10 realistic rooms (Standard ₹1,500, Deluxe ₹2,800, Suite ₹5,500).
   - 5 sample guests with complete contact credentials.
   - 4 realistic bookings across various lifecycle stages (`Checked-In`, `Confirmed`, `Checked-Out`).
   - 4 matching payment invoice records.
3. This guarantees that whenever faculty inspects the project, the system contains realistic, functional data immediately.

---

## 6. Room Management Logic

### File: `modules/rooms.py`

### 1. `get_all_rooms(db, category, room_status, search)`
- Accepts optional filter arguments.
- Uses `ilike()` for case-insensitive searching on room number and amenities.
- Returns an ordered list of Room instances.

### 2. `create_room(db, room_data)`
- Sanitizes the input string (`room_number.strip()`).
- Checks if a room with that number already exists. If found, raises `HTTPException(400)`.
- Instantiates a new `Room` model and commits it to the database.

### 3. `delete_room(db, room_id)` - Safe Deletion Constraint
- Before deleting a room, checks if any active reservations (`Confirmed` or `Checked-In`) reference this room ID:
  ```python
  active_bookings = db.query(Booking).filter(
      Booking.room_id == room_id,
      Booking.booking_status.in_(["Confirmed", "Checked-In"])
  ).count()
  ```
- If `active_bookings > 0`, deletion is refused with HTTP 400. This protects relational data integrity!

---

## 7. Customer Management Logic

### File: `modules/customers.py`

### 1. `create_customer(db, customer_data)`
- Enforces email address uniqueness.
- Normalizes email strings: `.strip().lower()`.
- Rejects duplicates before executing database insert.

### 2. `get_all_customers(db, search)`
- Iterates over customer rows.
- Uses a query count to dynamically compute `total_bookings` for each guest so the front desk can identify repeat customers.

---

## 8. Room Availability Calculation & Overlap Formula

### File: `modules/reservations.py` -> `check_room_availability()`

This is one of the most critical algorithms evaluated in viva examinations: **How do we prevent double bookings?**

### The Mathematical Overlap Theorem:
Suppose an existing reservation is from date $A_1$ to $A_2$, and a new requested booking is from $B_1$ to $B_2$.
The two intervals **overlap** if and only if:
$$A_1 < B_2 \quad \text{AND} \quad A_2 > B_1$$

### In SQLAlchemy Python Code:
```python
query = db.query(Booking).filter(
    Booking.room_id == room_id,
    Booking.booking_status.in_(["Confirmed", "Checked-In"]),
    Booking.check_in_date < check_out,   # A1 < B2
    Booking.check_out_date > check_in    # A2 > B1
)
```

### Why this logic works:
- If an existing guest departs on Oct 10 ($A_2 = 10$), and a new guest arrives on Oct 10 ($B_1 = 10$), then $A_2 > B_1$ is **False** ($10 > 10$ is False). Thus, **no conflict exists**, and the room can be booked for the new guest on the same day the previous guest leaves!
- If an existing booking is from Oct 10 to Oct 15, and someone requests Oct 12 to Oct 14:
  - $10 < 14$ is True
  - $15 > 12$ is True
  - Both conditions are True &rarr; Conflict detected! The system rejects the booking.

---

## 9. Reservation Creation & Validation Pipeline

### File: `modules/reservations.py` -> `create_reservation()`

When a user submits the "New Reservation" form, the function follows a strict 6-step pipeline:

```
1. Verify Customer exists in DB
              |
2. Verify Room exists & status != 'Maintenance'
              |
3. Validate Dates (check_in < check_out) & compute total_nights
              |
4. Verify Room Availability using Overlap Theorem
              |
5. Generate Unique Booking Reference Code (SH-YYYYMM-XXXX) & Insert Booking
              |
6. Calculate Room Charges, Discount, Tax & Insert Linked Payment Invoice
```

---

## 10. Billing, Tax & Discount Calculations

### File: `modules/billing.py` & `schemas/schemas.py`

### Formula Breakdown:
1. **Room Charges (Subtotal):**
   $$\text{Room Charges} = \text{Total Nights} \times \text{Price Per Night}$$
2. **Promotional Discount:**
   - Validated so it cannot exceed Room Charges:
     ```python
     if discount > room_charges:
         discount = room_charges
     ```
3. **Taxable Amount:**
   $$\text{Taxable Amount} = \text{Room Charges} - \text{Discount}$$
4. **Hotel Occupancy Tax (10% GST):**
   $$\text{Tax Amount} = \text{Taxable Amount} \times 0.10$$
5. **Net Total:**
   $$\text{Total Amount} = \text{Taxable Amount} + \text{Tax Amount}$$
6. **Payment Status Determination:**
   ```python
   if amount_paid >= total_amount:
       payment_status = "Paid"
   elif amount_paid > 0:
       payment_status = "Partially Paid"
   else:
       payment_status = "Pending"
   ```

---

## 11. Front Desk Operations: Check-In & Check-Out

### File: `modules/operations.py`

### 1. `process_check_in(db, request)`
- **Pre-condition:** Booking must exist and its status must be `Confirmed`.
- **Action:**
  - `booking.booking_status = "Checked-In"`
  - `room.status = "Occupied"`
- **Post-condition:** Room is occupied and shown on front desk dashboard.

### 2. `process_check_out(db, request)`
- **Pre-condition:** Booking must be in `Checked-In` status.
- **Financial Settlement:** If guest pays remaining balance at front desk, `amount_paid` is incremented and status updated to `Paid`.
- **Action:**
  - `booking.booking_status = "Checked-Out"`
  - `room.status = "Available"`
- **Post-condition:** Room is immediately freed for future guests.

---

## 12. How Frontend JavaScript Communicates with Python APIs

### Communication Mechanism:
The frontend (`public/assets/app.js`) never communicates directly with the database. It sends standard asynchronous HTTP requests using the JavaScript `fetch()` API.

### Flow Diagram:
```
[User clicks 'Confirm Reservation' in Browser Modal]
                        |
                        v
[JavaScript: app.handleReservationSubmit(event)]
  - Collects form field values
  - Formats JSON payload
  - Calls: fetch('/api/reservations', { method: 'POST', body: JSON })
                        |
                        v  (Network HTTP POST)
[FastAPI: @app.post('/api/reservations')]
  - Deserializes JSON into ReservationCreate schema
  - Validates fields (data types, ranges)
  - Passes data to reservations.create_reservation()
                        |
                        v
[Python Logic executes DB queries via SQLAlchemy]
  - Checks date overlap
  - Inserts Booking and Payment rows
  - Commits transaction
                        |
                        v  (HTTP 201 Created + JSON Response)
[JavaScript receives Response]
  - Parses returned JSON object
  - Displays green Toast notification: "Reservation SH-... confirmed!"
  - Closes modal and updates reservations table dynamically
```

---

## 13. Python Syllabus Mapping (Unit 1 & Unit 2)

| Syllabus Concept | Used In Module | Exact Code Demonstration |
| :--- | :--- | :--- |
| **Variables & Types** | All files | `int`, `float`, `str`, `date`, `datetime`, `bool` |
| **Typecasting** | `reservations.py`, `billing.py` | `float(data.discount_amount)`, `int(delta.days)` |
| **Arithmetic Operators** | `billing.py` | `nights * price_per_night`, `taxable * 0.10` |
| **If-Elif-Else** | `modules/billing.py` | Determining `Paid` vs `Partially Paid` vs `Pending` |
| **Boolean Logic (and/or)**| `modules/rooms.py` | `if category and category.lower() != "all":` |
| **Functions & Parameters**| All modules | `def calculate_nights(check_in: date, check_out: date) -> int:` |
| **Scope & Returns** | All modules | Local variables within functions returning typed objects |
| **Lists** | `schemas/schemas.py` | `List[RoomResponse]`, `List[ReservationResponse]` |
| **Tuples** | `test_app.py` | Status code checks `resp.status_code in (200, 201)` |
| **Dictionaries** | `database/init_db.py` | Seed records: `{"room_number": "101", ...}` |
| **Sets** | `modules/rooms.py` | Set uniqueness operations for filtering |
| **String Manipulation** | `customers.py`, `rooms.py` | `.strip()`, `.lower()`, `.startswith()`, `.replace()` |
| **List Comprehensions** | `main.py`, `customers.py` | `[ReservationResponse.model_validate(b) for b in bookings]` |
| **File Handling** | `modules/operations.py` | `import csv`, `io.StringIO()`, `writer.writerow()` |

---

## 14. Crucial Code Snippets with Line-by-Line Explanations

### Snippet 1: Night Calculation (`modules/reservations.py`)

```python
def calculate_nights(check_in: date, check_out: date) -> int:
    if check_in >= check_out:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid dates: Check-in date must be strictly before check-out date."
        )
    delta = (check_out - check_in).days
    return int(delta)
```

- **Line 1:** Declares function accepting two Python `date` objects, returning an integer.
- **Line 2:** Unit 1 conditional statement validating chronological order.
- **Lines 3-6:** Raises an HTTP 400 Bad Request exception if the guest enters an impossible departure date.
- **Line 7:** Subtracts arrival date from departure date. In Python, subtracting two dates produces a `timedelta` object. `.days` extracts the number of days as a number.
- **Line 8:** Explicit typecast to `int` and return to caller.

---

### Snippet 2: Safe Room Deletion (`modules/rooms.py`)

```python
active_bookings_count = db.query(Booking).filter(
    Booking.room_id == room_id,
    Booking.booking_status.in_(["Confirmed", "Checked-In"])
).count()

if active_bookings_count > 0:
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot delete Room because it has active reservations."
    )

db.delete(room)
db.commit()
```

- **Lines 1-4:** Queries the `bookings` table for records matching this room ID that are either currently in-house (`Checked-In`) or scheduled to arrive (`Confirmed`).
- **Lines 6-10:** If active bookings exist, execution is aborted with an error message informing the front desk manager to cancel the bookings first.
- **Lines 12-13:** If no active bookings exist, SQLAlchemy deletes the room record and commits the transaction to disk.

---

## 15. High-Yield Viva Questions and Model Answers

### Q1: Why did you choose FastAPI over Flask or Django?
> **Answer:** FastAPI provides native asynchronous performance, automatic request data validation via Pydantic, interactive Swagger API documentation (`/docs`) out of the box, and clean dependency injection (`Depends(get_db)`). Django was unnecessarily heavy for this project, and Flask lacks built-in asynchronous typing and automated schema generation.

### Q2: What is an ORM and why did you use SQLAlchemy?
> **Answer:** ORM stands for **Object Relational Mapping**. It allows developers to interact with database tables using Python classes and objects rather than writing raw SQL strings (`SELECT * FROM rooms`). SQLAlchemy protects against SQL injection vulnerabilities and allows our code to run seamlessly on both SQLite and PostgreSQL without changing any business logic.

### Q3: Explain how you prevent double booking of rooms.
> **Answer:** We use the date overlap theorem. When a booking is requested for a room from $\text{check\_in}$ to $\text{check\_out}$, we query the database for any existing bookings for that room that are `Confirmed` or `Checked-In` where:
> `(existing.check_in < new.check_out) AND (existing.check_out > new.check_in)`.
> If this query returns any record, a double booking exists, and the reservation is rejected with an HTTP 400 status.

### Q4: What is the difference between SQLite and PostgreSQL in your project?
> **Answer:** SQLite is a serverless, file-based database stored locally as `stayhome.db`, ideal for fast local testing and offline development. PostgreSQL (hosted on Neon) is an enterprise client-server relational database with connection pooling and multi-user concurrency, used when the application is deployed to production on Vercel.

### Q5: How do you calculate the guest bill and taxes?
> **Answer:** First, the room charge is calculated as $\text{nights} \times \text{price per night}$. Any promotional discount is deducted to determine the taxable amount. A 10% hotel occupancy tax is calculated on the taxable amount and added to produce the final net total. The system then evaluates the amount paid to label the status as `Paid`, `Partially Paid`, or `Pending`.
