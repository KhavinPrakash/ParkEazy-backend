from pydantic import BaseModel, EmailStr
from typing import Optional, List
import datetime

# User Schemas
class UserRegister(BaseModel):
    full_name: str
    email: str
    phone_number: str
    password: str
    vehicle_number: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    full_name: str
    email: str
    phone_number: str
    vehicle_number: Optional[str] = None

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Parking Slot Schemas
class ParkingSlotResponse(BaseModel):
    id: int
    facility_id: Optional[int] = None
    slot_number: str
    zone: str
    slot_type: str
    floor: str
    status: str
    price_per_hour: float
    x_pos: int
    y_pos: int
    width: int
    height: int
    current_vehicle: Optional[str] = None

    class Config:
        from_attributes = True

class SlotStatusUpdate(BaseModel):
    status: str
    current_vehicle: Optional[str] = None

# Multi-Facility Marketplace Schemas
class ParkingFacilityResponse(BaseModel):
    id: int
    name: str
    category: str
    address: str
    distance_km: float
    price_per_hour: float
    opening_hours: str
    is_open: bool
    image_category: str
    camera_id: str
    total_slots: int
    available_slots: int
    occupied_slots: int
    reserved_slots: int

    class Config:
        from_attributes = True

class FacilityDetailResponse(ParkingFacilityResponse):
    slots: List[ParkingSlotResponse] = []

    class Config:
        from_attributes = True

# Reservation Schemas
class ReservationCreate(BaseModel):
    slot_id: int
    vehicle_number: str
    hours: int
    payment_method: str # e.g. "UPI", "Credit Card", "NetBanking"

class ReservationResponse(BaseModel):
    id: int
    booking_id: str
    slot_id: int
    slot_number: str
    zone: str
    vehicle_number: str
    hours: int
    total_amount: float
    status: str
    created_at: datetime.datetime
    start_time: datetime.datetime
    end_time: datetime.datetime
    payment_transaction_id: str

    class Config:
        from_attributes = True

# Dashboard Stats Schema
class DashboardStats(BaseModel):
    total_slots: int
    available_slots: int
    occupied_slots: int
    reserved_slots: int
    occupancy_percentage: float
    total_facilities: int

# Payment Schemas
class PaymentRequest(BaseModel):
    reservation_id: int
    payment_method: str
    amount: float

class SMSLogResponse(BaseModel):
    id: int
    phone_number: str
    message: str
    sent_at: datetime.datetime
    status: str

    class Config:
        from_attributes = True
