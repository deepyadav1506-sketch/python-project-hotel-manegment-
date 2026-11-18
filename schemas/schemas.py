"""
StayHome Hotel Management System - Pydantic Validation Schemas
File: schemas/schemas.py

Purpose:
    Defines Pydantic models for validating request data entering our API
    and structuring response data returned to the frontend JavaScript.

Syllabus Concepts Covered:
    - Object-Oriented Programming (Base classes, inheritance).
    - Type hints and Type casting (str, int, float, date, Optional).
    - Data validation, constraint checks, and field defaults.
"""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr


# ==============================================================================
# ROOM SCHEMAS
# ==============================================================================

class RoomBase(BaseModel):
    """Base schema holding shared room attributes."""
    room_number: str = Field(..., min_length=1, max_length=20, description="Unique room identifier e.g. 101, 205")
    room_type: str = Field(..., description="Category: 'Standard', 'Deluxe', or 'Suite'")
    price_per_night: float = Field(..., gt=0, description="Base cost per night (must be positive)")
    capacity: int = Field(2, ge=1, le=10, description="Maximum number of guests allowed")
    status: str = Field("Available", description="'Available', 'Occupied', or 'Maintenance'")
    amenities: Optional[str] = Field("Free Wi-Fi, AC, Smart TV", description="Comma-separated list of amenities")


class RoomCreate(RoomBase):
    """Schema for validating new room creation requests."""
    pass


class RoomUpdate(BaseModel):
    """Schema for updating existing room details (all fields optional)."""
    room_number: Optional[str] = Field(None, min_length=1, max_length=20)
    room_type: Optional[str] = None
    price_per_night: Optional[float] = Field(None, gt=0)
    capacity: Optional[int] = Field(None, ge=1, le=10)
    status: Optional[str] = None
    amenities: Optional[str] = None


class RoomResponse(RoomBase):
    """Schema for returning room data to frontend."""
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ==============================================================================
# CUSTOMER SCHEMAS
# ==============================================================================

class CustomerBase(BaseModel):
    """Base schema holding shared customer attributes."""
    full_name: str = Field(..., min_length=2, max_length=100, description="Customer's full legal name")
    email: EmailStr = Field(..., description="Valid email address for confirmations")
    phone: str = Field(..., min_length=7, max_length=25, description="Primary contact phone number")
    address: Optional[str] = Field(None, max_length=255, description="Residential or billing address")
    id_proof: Optional[str] = Field(None, max_length=100, description="Govt ID type or number")


class CustomerCreate(CustomerBase):
    """Schema for adding a new customer."""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating customer info."""
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=7, max_length=25)
    address: Optional[str] = None
    id_proof: Optional[str] = None


class CustomerResponse(CustomerBase):
    """Schema for customer responses returned to frontend."""
    id: int
    created_at: Optional[datetime] = None
    total_bookings: Optional[int] = 0

    class Config:
        from_attributes = True


# ==============================================================================
# RESERVATION / BOOKING SCHEMAS
# ==============================================================================

class ReservationCreate(BaseModel):
    """Schema for creating a new hotel reservation."""
    customer_id: int = Field(..., description="ID of customer making the booking")
    room_id: int = Field(..., description="ID of room being reserved")
    check_in_date: date = Field(..., description="Check-in date (YYYY-MM-DD)")
    check_out_date: date = Field(..., description="Check-out date (YYYY-MM-DD)")
    guests_count: int = Field(1, ge=1, description="Number of guests staying")
    special_requests: Optional[str] = Field(None, description="Optional guest preferences")
    discount_amount: float = Field(0.0, ge=0.0, description="Promotional discount applied")
    payment_method: str = Field("Cash", description="Initial payment method: Cash, Credit Card, UPI, etc.")
    initial_payment: float = Field(0.0, ge=0.0, description="Advance payment received at booking time")


class ReservationUpdate(BaseModel):
    """Schema for modifying reservation dates or status."""
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    guests_count: Optional[int] = Field(None, ge=1)
    special_requests: Optional[str] = None
    booking_status: Optional[str] = None


class BookingCustomerSummary(BaseModel):
    """Minimal customer details nested in booking response."""
    id: int
    full_name: str
    email: str
    phone: str

    class Config:
        from_attributes = True


class BookingRoomSummary(BaseModel):
    """Minimal room details nested in booking response."""
    id: int
    room_number: str
    room_type: str
    price_per_night: float

    class Config:
        from_attributes = True


class BookingPaymentSummary(BaseModel):
    """Minimal billing summary nested in booking response."""
    id: int
    invoice_number: str
    room_charges: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    payment_status: str
    payment_method: str

    class Config:
        from_attributes = True


class ReservationResponse(BaseModel):
    """Complete booking response returned to frontend."""
    id: int
    booking_code: str
    customer_id: int
    room_id: int
    check_in_date: date
    check_out_date: date
    total_nights: int
    guests_count: int
    special_requests: Optional[str] = None
    booking_status: str
    created_at: Optional[datetime] = None

    customer: Optional[BookingCustomerSummary] = None
    room: Optional[BookingRoomSummary] = None
    payment: Optional[BookingPaymentSummary] = None

    class Config:
        from_attributes = True


# ==============================================================================
# CHECK-IN & CHECK-OUT SCHEMAS
# ==============================================================================

class CheckInRequest(BaseModel):
    """Payload to perform guest check-in."""
    booking_id: int


class CheckOutRequest(BaseModel):
    """Payload to perform guest checkout and optional final settlement."""
    booking_id: int
    amount_paid_now: float = Field(0.0, ge=0.0, description="Any settlement amount paid during checkout")
    payment_method: Optional[str] = "Cash"
    notes: Optional[str] = None


# ==============================================================================
# BILLING & PAYMENT SCHEMAS
# ==============================================================================

class PaymentRecordRequest(BaseModel):
    """Payload for recording a payment transaction against an invoice."""
    amount: float = Field(..., gt=0, description="Amount paid in this transaction")
    payment_method: str = Field("Cash", description="Cash, Credit Card, UPI, etc.")
    notes: Optional[str] = None


class PaymentResponse(BaseModel):
    """Schema for returning payment details to frontend."""
    id: int
    invoice_number: str
    booking_id: int
    room_charges: float
    discount_amount: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    balance_due: Optional[float] = 0.0
    payment_method: str
    payment_status: str
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceResponse(BaseModel):
    """Full printable invoice payload with itemized breakdown."""
    invoice_number: str
    booking_code: str
    invoice_date: str
    
    # Hotel Details
    hotel_name: str = "StayHome Luxury Hotel & Suites"
    hotel_address: str = "100 Hospitality Way, Silicon Valley, CA 94016"
    hotel_phone: str = "+1 (800) 555-STAY"
    hotel_email: str = "support@stayhome-hotel.com"

    # Guest Details
    customer_name: str
    customer_email: str
    customer_phone: str
    customer_address: Optional[str] = ""

    # Stay Details
    room_number: str
    room_type: str
    price_per_night: float
    check_in_date: str
    check_out_date: str
    total_nights: int
    guests_count: int

    # Financial Breakdown
    room_charges: float
    discount_amount: float
    tax_rate_percent: float
    tax_amount: float
    total_amount: float
    amount_paid: float
    balance_due: float
    payment_status: str
    payment_method: str
    notes: Optional[str] = None


# ==============================================================================
# DASHBOARD STATS SCHEMA
# ==============================================================================

class DashboardStatsResponse(BaseModel):
    """Statistics displayed on the main administrative dashboard."""
    total_rooms: int
    available_rooms: int
    occupied_rooms: int
    maintenance_rooms: int
    total_customers: int
    active_reservations: int
    today_checkins: int
    today_checkouts: int
    total_revenue: float
    pending_payments_count: int
    recent_bookings: List[ReservationResponse] = []
