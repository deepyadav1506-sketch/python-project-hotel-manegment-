# StayHome: Python-Based Hotel Management System
## Academic Project Report

**Author:** Individual Developer  
**Discipline:** Artificial Intelligence & Data Science (Semester III)  
**Course:** Introduction to Python Programming  
**Evaluation:** Laboratory Project & Viva Voce  

---

## 1. Introduction

The hospitality sector relies heavily on real-time information processing to coordinate room inventory, guest allocations, reservations, and financial accounting. Traditional manual record-keeping and rudimentary spreadsheet systems are prone to double bookings, delayed billing reconciliations, and lack of concurrent operational visibility.

**StayHome** is a modern, web-enabled Hotel Management System engineered using the **Python** programming language, the **FastAPI** web framework, and the **SQLAlchemy** Object-Relational Mapping (ORM) toolkit. The system automates room inventory management, guest profiles, reservation pipelines with mathematical double-booking prevention, automated billing with tax calculations, and front-desk check-in/check-out lifecycles.

---

## 2. Problem Statement

Hotels face several operational challenges:
1. **Double Bookings:** Simultaneous or overlapping booking requests frequently lead to conflicting reservations when availability checks are not automated.
2. **Billing Errors:** Manual calculation of night durations, discounts, and room occupancy taxes introduces financial discrepancies.
3. **Decoupled Inventory Tracking:** When guests check in or depart, room statuses (Available, Occupied, Maintenance) must update synchronously across all administrative channels.
4. **Data Integrity Hazards:** Accidental deletion of rooms or customers that have historical or active financial records compromises accounting audits.

---

## 3. Project Objectives

The primary objectives of the StayHome system are:
1. **Develop a Modular Python Architecture:** Implement clean, maintainable backend services adhering to Python fundamentals (Variables, Functions, Conditionals, Data Structures, File Handling).
2. **Prevent Reservation Overlaps:** Implement a rigorous mathematical overlap validation algorithm to completely eliminate duplicate bookings for the same room.
3. **Automate Folio Billing:** Dynamically compute room charges based on stay duration, apply validated discounts, add government hotel occupancy taxes (10% GST), and generate printable invoices.
4. **Synchronize Front-Desk States:** Seamlessly link reservation check-ins and check-outs with immediate room operational state updates.
5. **Ensure Cloud Deployment Readiness:** Architect the database layer to function offline on SQLite while deploying seamlessly to Neon PostgreSQL on Vercel.

---

## 4. Proposed System & Architecture

The StayHome platform utilizes a **Three-Tier Architecture**:

```
+-------------------------------------------------------+
|                    CLIENT TIER                        |
|  - HTML5 Responsive Single-Page Application (SPA)     |
|  - Custom CSS3 Executive Navy & Sky Blue Palette      |
|  - Vanilla JavaScript Controller (app.js)             |
+-------------------------------------------------------+
                           |
                     HTTP JSON REST
                           |
                           v
+-------------------------------------------------------+
|                 APPLICATION SERVER TIER               |
|  - FastAPI (ASGI High-Performance Web Engine)         |
|  - Pydantic v2 (Schema Validation & Serialization)    |
|  - Business Modules:                                  |
|      * rooms.py                                       |
|      * customers.py                                   |
|      * reservations.py                                |
|      * billing.py                                     |
|      * operations.py                                  |
+-------------------------------------------------------+
                           |
                    SQLAlchemy ORM
                           |
                           v
+-------------------------------------------------------+
|                    DATA PERSISTENCE                   |
|  - Development: Local SQLite (stayhome.db)            |
|  - Production: Neon Cloud PostgreSQL                  |
+-------------------------------------------------------+
```

---

## 5. Database Design & Entity Relationships

The relational schema consists of four core tables:

### 1. `rooms` Table
- `id` (INT, Primary Key, Indexed)
- `room_number` (VARCHAR(20), Unique, Indexed)
- `room_type` (VARCHAR(50), Standard / Deluxe / Suite)
- `price_per_night` (FLOAT)
- `capacity` (INT)
- `status` (VARCHAR(30), Available / Occupied / Maintenance)
- `amenities` (VARCHAR(255))
- `created_at` (DATETIME)

### 2. `customers` Table
- `id` (INT, Primary Key, Indexed)
- `full_name` (VARCHAR(100), Indexed)
- `email` (VARCHAR(120), Unique, Indexed)
- `phone` (VARCHAR(25))
- `address` (VARCHAR(255))
- `id_proof` (VARCHAR(100))
- `created_at` (DATETIME)

### 3. `bookings` Table
- `id` (INT, Primary Key, Indexed)
- `booking_code` (VARCHAR(30), Unique, Indexed)
- `customer_id` (INT, Foreign Key &rarr; `customers.id`)
- `room_id` (INT, Foreign Key &rarr; `rooms.id`)
- `check_in_date` (DATE)
- `check_out_date` (DATE)
- `total_nights` (INT)
- `guests_count` (INT)
- `special_requests` (TEXT)
- `booking_status` (VARCHAR(30), Confirmed / Checked-In / Checked-Out / Cancelled)
- `created_at` (DATETIME)

### 4. `payments` Table
- `id` (INT, Primary Key, Indexed)
- `invoice_number` (VARCHAR(40), Unique, Indexed)
- `booking_id` (INT, Foreign Key &rarr; `bookings.id`, Unique)
- `room_charges` (FLOAT)
- `discount_amount` (FLOAT)
- `tax_amount` (FLOAT)
- `total_amount` (FLOAT)
- `amount_paid` (FLOAT)
- `payment_method` (VARCHAR(50))
- `payment_status` (VARCHAR(30), Pending / Partially Paid / Paid)
- `payment_date` (DATETIME)
- `notes` (TEXT)

---

## 6. Implementation Methodology

### 6.1 Mathematical Overlap Verification
To guarantee that a room cannot be reserved twice for overlapping intervals, the algorithm checks:
$$\text{Existing Check-In} < \text{Requested Check-Out} \quad \text{AND} \quad \text{Existing Check-Out} > \text{Requested Check-In}$$
If any active booking (`Confirmed` or `Checked-In`) satisfies this condition, the request is rejected immediately with an HTTP 400 Bad Request error.

### 6.2 Billing & Tax Engine
Upon booking confirmation, the system creates a financial ledger entry:
1. $\text{Room Charges} = \text{total\_nights} \times \text{price\_per\_night}$
2. $\text{Taxable Amount} = \text{Room Charges} - \min(\text{discount}, \text{Room Charges})$
3. $\text{Tax (10\%)} = \text{round}(\text{Taxable Amount} \times 0.10, 2)$
4. $\text{Total Net} = \text{Taxable Amount} + \text{Tax}$

### 6.3 Safe Deletion Constraints
The system queries active foreign key references before allowing deletion of rooms or customers. If a room has pending or in-house stays, deletion is halted with an informative message.

---

## 7. Results & Verification

The system was verified through an automated test suite (`test_app.py`):

| Test Case ID | Test Description | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Real-time Dashboard KPI Aggregation | Accurate counts for rooms, stays, and revenue | Matches DB records exactly | **PASS** |
| **TC-02** | Unique Room Creation & Price Update | Room added; duplicate numbers rejected | Correctly inserted & updated | **PASS** |
| **TC-03** | Customer Email Uniqueness | Duplicate registration blocked (HTTP 400) | Blocked with 400 error | **PASS** |
| **TC-04** | Invalid Date Validation | Departure before arrival rejected (HTTP 400) | Blocked with 400 error | **PASS** |
| **TC-05** | Overlapping Booking Prevention | Double booking of same room rejected | Conflict detected & blocked | **PASS** |
| **TC-06** | Guest Check-In Workflow | Booking marked Checked-In; Room marked Occupied | States updated synchronously | **PASS** |
| **TC-07** | Guest Check-Out & Settlement | Room returned to Available; balance settled | Room freed, balance ₹0.0 | **PASS** |
| **TC-08** | Printable Invoice Generation | Complete itemized charges and A4 styling | Formatted invoice returned | **PASS** |
| **TC-09** | CSV Data Export | Downloadable CSV format using Python file handling | Valid CSV string generated | **PASS** |

---

## 8. Limitations

1. **Payment Gateway Integration:** The current payment module records cash, card, and UPI transactions at the front desk but does not integrate external merchant webhooks (e.g. Razorpay or Stripe).
2. **Multi-Property Tenancy:** The current implementation supports a single hotel property with multiple rooms rather than a multi-franchise chain.

---

## 9. Conclusion & Future Roadmap

**StayHome** demonstrates the power and simplicity of Python for developing full-stack business management applications. By combining FastAPI, SQLAlchemy, and a clean responsive frontend, the application provides commercial-grade reliability while demonstrating foundational Python syllabus concepts.

Future enhancements include implementing the Phase 2 enterprise modules outlined on the dashboard:
- Housekeeping staff dispatch and room turnaround queues.
- Restaurant and Room-Service Point-of-Sale (POS) integration.
- Automated email/SMS reservation confirmation alerts.
