# StayHome - Python-Based Hotel Management System

![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)
![Database](https://img.shields.io/badge/Database-SQLite%20%7C%20Neon%20PostgreSQL-336791.svg)
![Deployment](https://img.shields.io/badge/Deployment-Vercel-black.svg)

**StayHome** is a professional, full-stack, web-based Hotel Management System designed and built using **Python (FastAPI)** on the backend, **SQLAlchemy ORM** for database abstraction, and a responsive modern dashboard on the frontend with **HTML5, CSS3, and JavaScript**.

Developed for academic evaluation by an Artificial Intelligence & Data Science student, the codebase illustrates core **Introduction to Python Programming** syllabus concepts (Units 1 & 2) in an enterprise hospitality setting.

---

## 🌟 Key Features

### 1. Interactive Administration Dashboard
- Real-time KPI statistics queried directly from database records:
  - Total hotel rooms & available inventory
  - Occupied rooms & in-house guest count
  - Registered customer profiles
  - Active & confirmed reservations
  - Today's scheduled check-ins and check-outs
  - Total collected revenue ledger
- Quick action shortcuts for front desk staff.
- Recent reservations live audit table.

### 2. Room Management
- Complete CRUD (Create, Read, Update, Delete) operations.
- Categories: **Standard**, **Deluxe**, and **Suite**.
- Operational statuses: **Available**, **Occupied**, and **Maintenance**.
- Multi-criteria search and category filtering.
- **Safe deletion constraint**: Prevents accidental deletion of rooms with active or upcoming reservations.

### 3. Customer Directory
- Register and maintain guest profiles (Name, Phone, Unique Email, Address, Govt ID).
- String normalization and email uniqueness validation.
- Per-customer stay duration and booking history tally.
- Safe deletion validation.

### 4. Reservation Engine & Double-Booking Prevention
- Dynamic check-in and check-out date picker.
- Automatic night duration calculation (`(check_out - check_in).days`).
- **Mathematical Date Overlap Algorithm**:
  $$\text{Overlap} \iff (\text{Existing Check-In} < \text{New Check-Out}) \land (\text{Existing Check-Out} > \text{New Check-In})$$
- Real-time room availability lookup ensuring zero duplicate bookings.
- Unique booking reference code generation (e.g., `SH-202611-4821`).

### 5. Front Desk Operations (Check-In & Check-Out)
- **Check-In**: Verifies confirmed bookings, activates key status, and transitions room status to `Occupied`.
- **Check-Out**: Computes remaining folio balance, collects settlement payments, marks booking `Checked-Out`, and returns room to `Available`.

### 6. Billing, Invoices & Payments
- Automated pricing: $\text{Charges} = \text{Nights} \times \text{Price Per Night}$.
- Promotional discount handling.
- Hotel occupancy service tax (10% GST).
- Multiple payment modes: Cash, Credit/Debit Card, UPI, Bank Transfer.
- Payment statuses: `Paid`, `Partially Paid`, and `Pending`.
- **Printable Official Hotel Invoice**: Formatted A4 receipt with hotel details, guest folio, itemized breakdown, and print styles.

### 7. Data Export (CSV)
- Export Room inventory, Customer registry, or Booking ledger to CSV directly from Python backend using `csv` and `io.StringIO`.

### 8. Enterprise Roadmap Placeholders
- High-fidelity preview modules labeled **"Coming Soon (Phase 2)"** for Staff Management, Housekeeping, Restaurant POS, Inventory, Maintenance, Offers & Discounts, Reports, and System Settings.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Language** | Python 3.10+ | Core programming logic and backend calculations |
| **Web Framework** | FastAPI | High-performance asynchronous REST API framework |
| **ASGI Server** | Uvicorn | Production-ready ASGI web server |
| **ORM / Database Layer** | SQLAlchemy 2.0+ | Object Relational Mapping and schema definition |
| **Local Database** | SQLite 3 | Zero-configuration file database for local development |
| **Production Database** | Neon PostgreSQL | Cloud serverless PostgreSQL with connection pooling |
| **Validation** | Pydantic v2 | Strict request/response schema validation |
| **Frontend Structure** | HTML5 Semantic | Responsive single-page application structure |
| **Frontend Styling** | Custom CSS3 | Navy blue, white, and sky blue executive palette |
| **Frontend Logic** | Vanilla JavaScript | Asynchronous API fetching (`fetch`), routing, DOM state |
| **Deployment** | Vercel | Serverless hosting with `@vercel/python` builder |

---

## 📁 Project Directory Structure

```text
StayHome/
│
├── main.py                     # Central FastAPI application & route definitions
├── test_app.py                 # Automated verification test suite
│
├── database/                   # Database configuration and ORM
│   ├── __init__.py
│   ├── database.py             # SQLAlchemy engine, session maker & get_db dependency
│   ├── models.py               # ORM Models: Room, Customer, Booking, Payment
│   └── init_db.py              # Schema creation and realistic seed demo data
│
├── modules/                    # Modular Python Business Logic
│   ├── __init__.py
│   ├── rooms.py                # Room CRUD, category filters, safe deletion
│   ├── customers.py            # Customer registration, email validation
│   ├── reservations.py         # Date overlap checks, night calculation, booking
│   ├── billing.py              # Invoicing, tax/discount math, payment recording
│   └── operations.py           # Check-in, check-out, KPI aggregation, CSV export
│
├── schemas/                    # Pydantic Schemas & DTOs
│   ├── __init__.py
│   └── schemas.py              # Request/Response models with field validations
│
├── public/                     # Frontend Web Assets
│   ├── index.html              # Single Page Application Dashboard
│   └── assets/
│       ├── style.css           # Premium Navy Blue UI & Print Styles
│       └── app.js              # Frontend controller, REST client, live estimates
│
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules for virtual environments and secrets
├── vercel.json                 # Vercel serverless deployment configuration
│
├── README.md                   # Project documentation (this file)
├── PYTHON_CODE_GUIDE.md        # Comprehensive Python syllabus explanation & viva guide
├── PROJECT_REPORT.md           # Academic project report
├── PRESENTATION_GUIDE.md       # 20-slide presentation blueprint
└── VIVA_QUESTIONS.md           # Detailed Viva Q&A with model answers
```

---

## 🚀 Local Installation and Execution

### Step 1: Clone or Navigate to Project Folder
```bash
cd "Python Project"
```

### Step 2: Create and Activate Virtual Environment
```bash
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Initialize the Database (Auto-Seeded)
```bash
python -m database.init_db
```
*Note: The application also automatically initializes the database and seeds realistic demo data on the first launch.*

### Step 5: Start the Development Server
```bash
uvicorn main:app --reload --port 8000
```

### Step 6: Open the Application in Your Browser
- **StayHome Dashboard**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc API Reference**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 🧪 Running Automated Tests

Run the built-in test suite to verify all backend modules, double booking prevention, date validation, check-in/out workflows, and billing:

```bash
python test_app.py
```

Expected output:
```text
>>> INITIATING STAYHOME AUTOMATED VERIFICATION SUITE <<<
  ✓ Dashboard Stats OK
  ✓ Room Creation and Filtering OK
  ✓ Customer Registration and Uniqueness OK
  ✓ Reservation Creation & Billing Calculation OK
  ✓ Double Booking Prevention (Overlap Check) OK
  ✓ Check-In and Check-Out Lifecycle OK
  ✓ Printable Invoice Generation OK
  ✓ Safe Deletion & CSV Export OK
=================================================================
  ALL 8/8 BACKEND MODULE TESTS COMPLETED SUCCESSFULLY!
=================================================================
```

---

## 🌐 Deploying to Vercel with Neon PostgreSQL

### Step 1: Set Up Neon Serverless PostgreSQL Database
1. Go to [https://neon.tech](https://neon.tech) and create a free account.
2. Click **Create Project**, name it `stayhome-db`, and select your preferred region.
3. In the Neon Dashboard, copy your connection string (format: `postgresql://user:password@ep-sample.us-east-2.aws.neon.tech/neondb?sslmode=require`).

### Step 2: Push Project to GitHub
```bash
git init
git add .
git commit -m "Initial commit of StayHome Hotel Management System"
git branch -M main
git remote add origin https://github.com/<your-username>/stayhome-hotel.git
git push -u origin main
```

### Step 3: Deploy to Vercel
1. Log in to [https://vercel.com](https://vercel.com).
2. Click **Add New** &rarr; **Project**.
3. Import your GitHub repository `stayhome-hotel`.
4. In **Environment Variables**, add:
   - `DATABASE_URL`: Your Neon PostgreSQL connection string.
   - `APP_ENV`: `production`
   - `DEBUG`: `False`
5. Click **Deploy**. Vercel will install dependencies from `requirements.txt` and launch the application via `main.py`!

---

## 👨‍🎓 Academic Integrity & Evaluation Notes

This project was built from scratch without external dependencies beyond standard Python, FastAPI, and SQLAlchemy libraries. For an in-depth code walkthrough and line-by-line viva examination preparation, please review [PYTHON_CODE_GUIDE.md](file:///c:/Users/DEEPAK%20YADAV/OneDrive/Documents/Project%20folder/Python%20Project/PYTHON_CODE_GUIDE.md).
