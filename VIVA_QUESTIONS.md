# StayHome: Comprehensive Viva Voce Questions & Model Answers

> **Course:** Introduction to Python Programming  
> **Student Background:** Third-Semester Artificial Intelligence & Data Science  
> **Project:** StayHome - Python-Based Hotel Management System  

This guide contains realistic viva questions that faculty members and external examiners frequently ask during project evaluations, along with clear, understandable answers that a 3rd-semester student can confidently explain.

---

## Category 1: Python Fundamentals (Unit 1 Syllabus)

### Q1: What data types are used in this project?
**Answer:**  
Our project uses both primitive and standard Python types:
- `int`: Used for IDs (`room_id`, `customer_id`), guest counts, and night counts (`total_nights`).
- `float`: Used for monetary calculations, prices, tax amounts, and bill totals (`price_per_night`, `discount_amount`, `tax_amount`).
- `str`: Used for room numbers (`"101"`), names, emails, phone numbers, booking codes, and statuses.
- `bool`: Used for truth checks, such as availability checks (`is_available`).
- `date` and `datetime`: From Python's standard `datetime` module, used for tracking check-in/out calendar dates and timestamps.

---

### Q2: How does Python calculate the number of nights between two dates?
**Answer:**  
In `modules/reservations.py`, we subtract the check-in date from the check-out date:
```python
delta = (check_out - check_in).days
```
In Python, subtracting two `datetime.date` objects returns a `timedelta` object. We access its `.days` attribute, which gives the exact integer count of days. We also validate that `check_in < check_out` using an `if` condition to prevent negative or zero nights.

---

### Q3: Where did you use conditional statements (if-elif-else) in your code?
**Answer:**  
We use conditional statements in multiple places:
1. **Date Validation:** In `modules/reservations.py`, `if check_in >= check_out:` raises an HTTP 400 error.
2. **Payment Status:** In `modules/reservations.py` and `modules/billing.py`:
   ```python
   if initial_paid >= total_amount:
       payment_status = "Paid"
   elif initial_paid > 0:
       payment_status = "Partially Paid"
   else:
       payment_status = "Pending"
   ```
3. **Discount Capping:** Ensuring a discount does not exceed room charges:
   ```python
   if discount > room_charges:
       discount = room_charges
   ```

---

### Q4: What is the purpose of functions and return statements in your project?
**Answer:**  
Functions allow us to organize code into reusable, modular blocks with specific tasks (modular programming). For example:
- `get_available_rooms_for_dates()` accepts dates and returns a list of free rooms.
- `calculate_nights()` takes two dates and returns an integer.
- `process_check_in()` takes a booking ID and returns a dictionary confirming check-in.
Functions prevent code duplication and make the logic easy to test and debug.

---

### Q5: What is variable scope and how is it used here?
**Answer:**  
Variable scope determines where a variable is accessible in code:
- **Local Scope:** Variables created inside a function (e.g., `taxable_amount` inside `create_reservation()`) exist only while that function runs and are destroyed when it returns.
- **Global / Module Scope:** Variables defined at the top level of a file (e.g., `engine`, `Base` in `database.py`, and `app` in `main.py`) are accessible across the entire module and can be imported into other files.

---

## Category 2: Python Data Structures & File Handling (Unit 2 Syllabus)

### Q6: Where did you use Lists and Tuples in the project?
**Answer:**  
- **Lists:** Used whenever multiple items are stored and returned. For example, `get_all_rooms()` returns a `List[Room]`, and `recent_bookings` in dashboard stats is a list of booking objects. In Pydantic schemas, we use `List[RoomResponse]`.
- **Tuples:** Used for immutable status checks. For instance:
  ```python
  if booking.booking_status in ("Confirmed", "Checked-In"):
  ```
  Tuples ensure that the valid status choices cannot be accidentally modified at runtime.

---

### Q7: Where did you use Dictionaries and List Comprehensions?
**Answer:**  
- **Dictionaries:** In `database/init_db.py`, the initial seed data is defined as a list of dictionaries, where each key matches a database column (e.g., `{"room_number": "101", "room_type": "Standard", "price_per_night": 1500.0}`). When updating records in `update_room()`, Pydantic models are converted to dictionaries using `.model_dump(exclude_unset=True)`.
- **List Comprehensions:** Used for concise, readable data transformation. In `main.py`:
  ```python
  return [ReservationResponse.model_validate(b) for b in bookings]
  ```
  This iterates through all ORM booking objects and transforms each one into a validated response schema in a single readable line.

---

### Q8: How did you implement File Handling without creating unnecessary files on disk?
**Answer:**  
In `modules/operations.py`, we implement CSV export using Python's standard `csv` module and `io.StringIO`:
```python
output = io.StringIO()
writer = csv.writer(output)
writer.writerow(["Room ID", "Room Number", "Category", "Price", ...])
for r in rooms:
    writer.writerow([r.id, r.room_number, ...])
return output.getvalue()
```
`io.StringIO` acts as an in-memory text file. This avoids writing temporary files to the server's hard drive, preventing storage clutter while allowing the browser to download the generated CSV instantly.

---

### Q9: Where did you use string manipulation methods?
**Answer:**  
We use string methods for input sanitization and search filtering:
- `.strip()` removes leading and trailing whitespace from guest names, emails, and room numbers.
- `.lower()` normalizes email addresses so `"Guest@Example.com"` and `"guest@example.com"` are treated as identical.
- `.startswith()` and `.replace()` in `database.py` normalize cloud database URLs from `postgres://` to `postgresql://`.

---

## Category 3: FastAPI & REST API Architecture

### Q10: What is FastAPI and what role does it play in StayHome?
**Answer:**  
FastAPI is a high-performance Python web framework for building RESTful APIs. In our project:
1. It exposes endpoints like `/api/rooms`, `/api/reservations`, `/api/dashboard/stats`.
2. It receives HTTP requests (GET, POST, PUT, DELETE) from the browser's JavaScript.
3. It validates request payloads against Pydantic schemas.
4. It calls our Python business logic modules and returns JSON responses with proper HTTP status codes.

---

### Q11: What is Dependency Injection and how does `Depends(get_db)` work?
**Answer:**  
Dependency injection is a design pattern where a function receives dependencies it needs from an external provider rather than creating them internally.  
In FastAPI, `db: Session = Depends(get_db)` tells FastAPI:
1. Run `get_db()` before executing the endpoint function.
2. Open a fresh database session and pass it into the function.
3. After the endpoint finishes (or even if an error is raised), execute the `finally:` block in `get_db()` to automatically close the session. This prevents database connection leaks.

---

### Q12: What are the differences between GET, POST, PUT, and DELETE methods in your API?
**Answer:**  
- **GET:** Used to retrieve data without modifying database state (e.g., `GET /api/rooms` fetches all rooms).
- **POST:** Used to create a new record (e.g., `POST /api/reservations` creates a new booking and invoice).
- **PUT:** Used to update an existing record (e.g., `PUT /api/rooms/5` updates room 5's price or status).
- **DELETE:** Used to remove a record (e.g., `DELETE /api/rooms/5` safely removes a room).

---

### Q13: What are HTTP status codes and which ones are used in StayHome?
**Answer:**  
HTTP status codes tell the client the outcome of their request:
- `200 OK`: Request succeeded (e.g., data retrieved or updated).
- `201 Created`: A new record was successfully created (e.g., new room or reservation added).
- `400 Bad Request`: Client sent invalid data (e.g., check-in date after check-out date, or double booking conflict).
- `404 Not Found`: The requested record does not exist (e.g., room ID 999 not found).

---

## Category 4: SQLAlchemy & Database Concepts

### Q14: What is an ORM and why is SQLAlchemy beneficial?
**Answer:**  
ORM stands for **Object Relational Mapping**. It bridges object-oriented Python code and relational database tables.  
Instead of writing raw SQL strings like `SELECT * FROM rooms WHERE status='Available'`, we write clean Python:
```python
db.query(Room).filter(Room.status == "Available").all()
```
**Benefits:**
1. Eliminates SQL injection vulnerabilities because inputs are automatically parameterized.
2. Allows switching between databases (SQLite in development, PostgreSQL in production) without changing a single line of business code.
3. Maps database tables directly to Python objects with automatic type conversions.

---

### Q15: Explain the primary keys and foreign keys in your database models.
**Answer:**  
- **Primary Key (PK):** A column that uniquely identifies every row in a table. In our models, `id = Column(Integer, primary_key=True)` serves as the primary key for `rooms`, `customers`, `bookings`, and `payments`.
- **Foreign Key (FK):** A column that points to the primary key of another table, establishing a relationship.
  - In `bookings`, `customer_id = Column(Integer, ForeignKey("customers.id"))` links the booking to a specific customer.
  - In `bookings`, `room_id = Column(Integer, ForeignKey("rooms.id"))` links the booking to a specific room.
  - In `payments`, `booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True)` creates a one-to-one relationship with the booking.

---

### Q16: What is the difference between SQLite and PostgreSQL?
**Answer:**  
- **SQLite:** A lightweight, serverless database engine that stores all data in a single local file (`stayhome.db`). It requires zero setup and is ideal for local development and demonstration.
- **PostgreSQL:** A client-server relational database with advanced concurrency, multi-user support, and transaction pooling. We use PostgreSQL (hosted on Neon) for production deployment on Vercel so data persists reliably across serverless function restarts.

---

## Category 5: Hotel Operations & Business Logic

### Q17: How does your code prevent double bookings?
**Answer:**  
We implement the mathematical **Interval Overlap Theorem**. When a guest requests dates from $B_1$ (check-in) to $B_2$ (check-out), we query existing active bookings ($A_1$ to $A_2$) for that room. A collision occurs if and only if:
$$A_1 < B_2 \quad \text{AND} \quad A_2 > B_1$$
In Python code:
```python
db.query(Booking).filter(
    Booking.room_id == room_id,
    Booking.booking_status.in_(["Confirmed", "Checked-In"]),
    Booking.check_in_date < check_out,
    Booking.check_out_date > check_in
)
```
If this query returns any records, the room is occupied or reserved during those dates, and the system rejects the booking with an HTTP 400 error.

---

### Q18: What is safe deletion and why is it important in hotel management?
**Answer:**  
Safe deletion prevents deleting a room or customer that is currently referenced by active bookings.  
If the manager tries to delete a room that currently has guests staying in it, our `delete_room()` function counts active bookings:
```python
if active_bookings_count > 0:
    raise HTTPException(status_code=400, detail="Cannot delete room with active bookings.")
```
This protects relational data integrity and prevents corrupting accounting ledgers.

---

### Q19: Explain the billing calculation logic and taxes.
**Answer:**  
In `modules/billing.py`:
1. **Base Charges:** $\text{Room Charges} = \text{total\_nights} \times \text{price\_per\_night}$.
2. **Discount:** Optional discount deducted from room charges (validated so it never exceeds room charges).
3. **Tax:** We calculate a 10% Hotel Occupancy Service Tax on the taxable amount:
   ```python
   tax_amount = round((room_charges - discount) * 0.10, 2)
   ```
4. **Total Amount:** $\text{Taxable Amount} + \text{Tax Amount}$.
5. **Balance Due:** $\max(0, \text{Total Amount} - \text{Amount Paid})$.

---

### Q20: What happens behind the scenes when a guest checks in and checks out?
**Answer:**  
- **Check-In (`process_check_in`):**
  1. Verifies that the reservation status is `Confirmed`.
  2. Updates `booking.booking_status = "Checked-In"`.
  3. Updates `room.status = "Occupied"`.
  4. Both updates commit in a single database transaction.
- **Check-Out (`process_check_out`):**
  1. Verifies that the guest is currently `Checked-In`.
  2. Collects any remaining balance payment and updates `amount_paid`.
  3. Updates `booking.booking_status = "Checked-Out"`.
  4. Sets `room.status = "Available"` so new guests can reserve it.

---

### Q21: How does the frontend JavaScript connect to the Python backend?
**Answer:**  
The frontend is a Single-Page Application (SPA) using vanilla JavaScript in `public/assets/app.js`. It uses the browser's asynchronous `fetch()` API to send HTTP requests to our FastAPI backend:
1. When a form is submitted (e.g., adding a customer), JS gathers the form fields into a JavaScript object.
2. It sends `fetch('/api/customers', { method: 'POST', body: JSON.stringify(data) })`.
3. FastAPI processes the request and responds with a JSON object.
4. JS parses the response, displays a toast notification (e.g., "Customer registered!"), and updates the DOM table dynamically without refreshing the page.
