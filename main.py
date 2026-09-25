from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, SessionLocal
import models
from routers import auth_router, slots_router, reservations_router, sms_router, camera_router, facilities_router
import asyncio
import json

# Initialize DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="ParkEazy Centralized Multi-Parking Platform API",
    description="Marketplace API for discovering enrolled parking facilities in Chennai (Malls, D-Mart, Hospitals, Tech Parks, Airports), real-time YOLO slot occupancy, reservations, and SMS notifications.",
    version="2.1.0"
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth_router.router)
app.include_router(facilities_router.router)
app.include_router(slots_router.router)
app.include_router(reservations_router.router)
app.include_router(sms_router.router)
app.include_router(camera_router.router)

# Seed Enrolled Parking Facilities with Chennai Addresses & Chennai International Airport
def seed_facilities_and_slots():
    db = SessionLocal()
    try:
        # Check if addresses need updating to Chennai
        f_existing = db.query(models.ParkingFacility).first()
        if f_existing and "Chennai" not in f_existing.address:
            # Wipe existing facility data to re-seed with Chennai locations
            db.query(models.ParkingSlot).delete()
            db.query(models.ParkingFacility).delete()
            db.commit()

        fac_count = db.query(models.ParkingFacility).count()
        if fac_count == 0:
            # 1. Seed Facilities with Chennai Addresses
            f1 = models.ParkingFacility(
                name="Phoenix Marketcity Mall",
                category="Shopping Mall",
                address="Velachery Main Rd, Velachery, Chennai",
                distance_km=1.2,
                price_per_hour=40.0,
                opening_hours="09:30 AM - 11:00 PM",
                is_open=True,
                image_category="mall",
                camera_id="CAM-01-PHOENIX"
            )
            f2 = models.ParkingFacility(
                name="D-Mart Supermarket",
                category="Supermarket",
                address="Arcot Rd, Vadapalani, Chennai",
                distance_km=2.4,
                price_per_hour=20.0,
                opening_hours="08:00 AM - 10:00 PM",
                is_open=True,
                image_category="supermarket",
                camera_id="CAM-02-DMART"
            )
            f3 = models.ParkingFacility(
                name="City Care Multispecialty Hospital",
                category="Hospital",
                address="Greams Rd, Thousand Lights, Chennai",
                distance_km=3.8,
                price_per_hour=30.0,
                opening_hours="24/7 Open Emergency",
                is_open=True,
                image_category="hospital",
                camera_id="CAM-03-HOSPITAL"
            )
            f4 = models.ParkingFacility(
                name="Global Tech Park & Offices",
                category="Office & Tech Park",
                address="Rajiv Gandhi Salai (OMR), Taramani, Chennai",
                distance_km=4.5,
                price_per_hour=50.0,
                opening_hours="06:00 AM - 10:00 PM",
                is_open=True,
                image_category="office",
                camera_id="CAM-04-TECHPARK"
            )
            f5 = models.ParkingFacility(
                name="Chennai International Airport (MAA)",
                category="Airport Parking",
                address="GST Rd, Meenambakkam, Chennai",
                distance_km=12.0,
                price_per_hour=80.0,
                opening_hours="24/7 Open",
                is_open=True,
                image_category="airport",
                camera_id="CAM-05-AIRPORT"
            )
            db.add_all([f1, f2, f3, f4, f5])
            db.commit()

            # Refresh facilities to get IDs
            db.refresh(f1)
            db.refresh(f2)
            db.refresh(f3)
            db.refresh(f4)
            db.refresh(f5)

            # 2. Seed Slots linked to Facilities (5 slots per facility)
            slots = [
                # Phoenix Mall Slots (Velachery, Chennai)
                models.ParkingSlot(facility_id=f1.id, slot_number="A1", zone="Zone A - Phoenix Lot", slot_type="Standard Car", floor="Level 1", status="Available", price_per_hour=40.0, x_pos=140, y_pos=160),
                models.ParkingSlot(facility_id=f1.id, slot_number="A2", zone="Zone A - Phoenix Lot", slot_type="Standard Car", floor="Level 1", status="Occupied", price_per_hour=40.0, x_pos=340, y_pos=160, current_vehicle="TN-07-MJ-4821"),
                models.ParkingSlot(facility_id=f1.id, slot_number="A3", zone="Zone A - Phoenix Lot", slot_type="EV Charging", floor="Level 1", status="Available", price_per_hour=75.0, x_pos=540, y_pos=160),
                models.ParkingSlot(facility_id=f1.id, slot_number="A4", zone="Zone A - Phoenix Lot", slot_type="Standard Car", floor="Level 1", status="Available", price_per_hour=40.0, x_pos=740, y_pos=160),
                models.ParkingSlot(facility_id=f1.id, slot_number="A5", zone="Zone A - Phoenix Lot", slot_type="Premium SUV", floor="Level 1", status="Occupied", price_per_hour=60.0, x_pos=940, y_pos=160, current_vehicle="TN-03-CC-1122"),

                # D-Mart Slots (Vadapalani, Chennai)
                models.ParkingSlot(facility_id=f2.id, slot_number="B1", zone="Zone B - D-Mart Lot", slot_type="Standard Car", floor="Ground Floor", status="Occupied", price_per_hour=20.0, x_pos=140, y_pos=430, current_vehicle="TN-09-AX-7721"),
                models.ParkingSlot(facility_id=f2.id, slot_number="B2", zone="Zone B - D-Mart Lot", slot_type="Bike / Scooter", floor="Ground Floor", status="Available", price_per_hour=15.0, x_pos=340, y_pos=430),
                models.ParkingSlot(facility_id=f2.id, slot_number="B3", zone="Zone B - D-Mart Lot", slot_type="EV Charging", floor="Ground Floor", status="Available", price_per_hour=50.0, x_pos=540, y_pos=430),
                models.ParkingSlot(facility_id=f2.id, slot_number="B4", zone="Zone B - D-Mart Lot", slot_type="Bike / Scooter", floor="Ground Floor", status="Occupied", price_per_hour=15.0, x_pos=740, y_pos=430, current_vehicle="TN-04-HB-2024"),
                models.ParkingSlot(facility_id=f2.id, slot_number="B5", zone="Zone B - D-Mart Lot", slot_type="Standard Car", floor="Ground Floor", status="Available", price_per_hour=20.0, x_pos=940, y_pos=430),

                # Hospital Slots (Thousand Lights, Chennai)
                models.ParkingSlot(facility_id=f3.id, slot_number="H1", zone="Hospital Emergency", slot_type="Standard Car", floor="Ground Floor", status="Available", price_per_hour=30.0),
                models.ParkingSlot(facility_id=f3.id, slot_number="H2", zone="Hospital Emergency", slot_type="EV Charging", floor="Ground Floor", status="Available", price_per_hour=60.0),
                models.ParkingSlot(facility_id=f3.id, slot_number="H3", zone="Doctor Reserved", slot_type="Standard Car", floor="Ground Floor", status="Occupied", price_per_hour=30.0, current_vehicle="TN-06-DOC-101"),
                models.ParkingSlot(facility_id=f3.id, slot_number="H4", zone="Visitor Parking", slot_type="Standard Car", floor="Ground Floor", status="Available", price_per_hour=30.0),
                models.ParkingSlot(facility_id=f3.id, slot_number="H5", zone="Visitor Parking", slot_type="Bike / Scooter", floor="Ground Floor", status="Available", price_per_hour=15.0),

                # Tech Park Slots (OMR Taramani, Chennai)
                models.ParkingSlot(facility_id=f4.id, slot_number="TP1", zone="Tech Park Tower A", slot_type="Premium SUV", floor="Basement 1", status="Available", price_per_hour=50.0),
                models.ParkingSlot(facility_id=f4.id, slot_number="TP2", zone="Tech Park Tower A", slot_type="EV Charging", floor="Basement 1", status="Available", price_per_hour=80.0),
                models.ParkingSlot(facility_id=f4.id, slot_number="TP3", zone="Tech Park Tower B", slot_type="Bike / Scooter", floor="Basement 1", status="Occupied", price_per_hour=25.0, current_vehicle="TN-22-BIKE-88"),
                models.ParkingSlot(facility_id=f4.id, slot_number="TP4", zone="Tech Park Tower B", slot_type="Standard Car", floor="Basement 1", status="Available", price_per_hour=50.0),
                models.ParkingSlot(facility_id=f4.id, slot_number="TP5", zone="Tech Park Tower B", slot_type="EV Charging", floor="Basement 1", status="Available", price_per_hour=80.0),

                # Chennai Airport Slots (Meenambakkam, Chennai)
                models.ParkingSlot(facility_id=f5.id, slot_number="AP1", zone="Chennai Airport Terminal T2/T4", slot_type="Standard Car", floor="Level 2", status="Available", price_per_hour=80.0),
                models.ParkingSlot(facility_id=f5.id, slot_number="AP2", zone="Chennai Airport Terminal T2/T4", slot_type="EV Fast Charge", floor="Level 2", status="Available", price_per_hour=120.0),
                models.ParkingSlot(facility_id=f5.id, slot_number="AP3", zone="Chennai Airport Terminal T2/T4", slot_type="Standard Car", floor="Level 2", status="Occupied", price_per_hour=80.0, current_vehicle="TN-01-AP-9900"),
                models.ParkingSlot(facility_id=f5.id, slot_number="AP4", zone="Chennai Airport Terminal T2/T4", slot_type="Standard Car", floor="Level 2", status="Available", price_per_hour=80.0),
                models.ParkingSlot(facility_id=f5.id, slot_number="AP5", zone="Chennai Airport Terminal T2/T4", slot_type="Bike / Scooter", floor="Level 2", status="Available", price_per_hour=30.0),
            ]
            db.add_all(slots)
            db.commit()
            print("Successfully seeded 5 Chennai enrolled parking facilities and slots.")
    finally:
        db.close()

seed_facilities_and_slots()

@app.get("/")
def root():
    return {
        "app": "ParkEazy Centralized Multi-Parking Platform API (Chennai Region)",
        "status": "ONLINE",
        "docs": "/docs",
        "facilities": "/api/facilities",
        "camera_stream": "/api/camera/stream"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
