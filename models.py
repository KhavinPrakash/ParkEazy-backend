import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone_number = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    vehicle_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    reservations = relationship("Reservation", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class ParkingFacility(Base):
    __tablename__ = "parking_facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True) # e.g. Phoenix Mall, D-Mart
    category = Column(String, nullable=False, default="Shopping Mall") # Shopping Mall, Supermarket, Hospital, Office, Airport
    address = Column(String, nullable=False)
    distance_km = Column(Float, nullable=False, default=1.2)
    price_per_hour = Column(Float, nullable=False, default=40.0) # Base price in INR (₹)
    opening_hours = Column(String, default="09:00 AM - 11:00 PM")
    is_open = Column(Boolean, default=True)
    image_category = Column(String, default="mall")
    camera_id = Column(String, default="CAM-01-NORTH")

    slots = relationship("ParkingSlot", back_populates="facility")

class ParkingSlot(Base):
    __tablename__ = "parking_slots"

    id = Column(Integer, primary_key=True, index=True)
    facility_id = Column(Integer, ForeignKey("parking_facilities.id"), nullable=True)
    slot_number = Column(String, index=True, nullable=False) # e.g. A1, A2, B1
    zone = Column(String, nullable=False, default="Zone A") # Zone A, Zone B, EV Zone
    slot_type = Column(String, nullable=False, default="Standard") # Standard, EV Charging, Compact
    floor = Column(String, nullable=False, default="Ground Floor")
    status = Column(String, nullable=False, default="Available") # Available, Occupied, Reserved
    price_per_hour = Column(Float, nullable=False, default=50.0) # Price in INR (₹)
    x_pos = Column(Integer, default=0)
    y_pos = Column(Integer, default=0)
    width = Column(Integer, default=120)
    height = Column(Integer, default=80)
    current_vehicle = Column(String, nullable=True)

    facility = relationship("ParkingFacility", back_populates="slots")
    reservations = relationship("Reservation", back_populates="slot")

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    slot_id = Column(Integer, ForeignKey("parking_slots.id"), nullable=False)
    vehicle_number = Column(String, nullable=False)
    hours = Column(Integer, nullable=False, default=1)
    total_amount = Column(Float, nullable=False) # In INR (₹)
    status = Column(String, nullable=False, default="Active") # Active, Completed, Cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    end_time = Column(DateTime, nullable=False)

    user = relationship("User", back_populates="reservations")
    slot = relationship("ParkingSlot", back_populates="reservations")
    payment = relationship("Payment", back_populates="reservation", uselist=False)

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String, unique=True, index=True, nullable=False)
    reservation_id = Column(Integer, ForeignKey("reservations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False) # In INR (₹)
    payment_method = Column(String, nullable=False) # UPI, Card, NetBanking
    payment_status = Column(String, nullable=False, default="SUCCESS")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="payments")
    reservation = relationship("Reservation", back_populates="payment")

class SMSLog(Base):
    __tablename__ = "sms_logs"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=False)
    message = Column(String, nullable=False)
    sent_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String, default="DELIVERED")
