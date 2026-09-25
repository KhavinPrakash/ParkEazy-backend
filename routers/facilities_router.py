import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import models, schemas
from database import get_db
from yolo_detector import detector_instance

router = APIRouter(prefix="/api/facilities", tags=["Enrolled Parking Facilities Marketplace"])

def sync_yolo_for_facilities(db: Session):
    """Sync YOLO camera detection status with database parking slots safely."""
    try:
        updated = False
        now = datetime.datetime.utcnow()

        # 1. Auto-expire completed reservations and release their slots back to Available
        expired_reservations = db.query(models.Reservation).filter(
            models.Reservation.status == "Active",
            models.Reservation.end_time < now
        ).all()
        for res in expired_reservations:
            res.status = "Completed"
            if res.slot and res.slot.status == "Reserved":
                res.slot.status = "Available"
                res.slot.current_vehicle = None
                updated = True

        # 2. Sync YOLO camera detection status for unreserved slots
        yolo_states = detector_instance.get_slot_states()
        slots = db.query(models.ParkingSlot).filter(models.ParkingSlot.status != "Reserved").all()
        for slot in slots:
            if slot.slot_number in yolo_states:
                new_status = yolo_states[slot.slot_number]
                if new_status in ["Available", "Occupied"] and slot.status != new_status:
                    if slot.status == "Occupied" and new_status == "Available":
                        slot.status = "Available"
                        slot.current_vehicle = None
                        updated = True
                    elif slot.status == "Available" and new_status == "Occupied":
                        slot.status = "Occupied"
                        slot.current_vehicle = "DETECTED_VEHICLE"
                        updated = True
        if updated:
            db.commit()
    except Exception as e:
        db.rollback()

@router.get("/", response_model=List[schemas.ParkingFacilityResponse])
def get_all_facilities(db: Session = Depends(get_db)):
    sync_yolo_for_facilities(db)
    facilities = db.query(models.ParkingFacility).all()
    
    res = []
    for fac in facilities:
        slots = db.query(models.ParkingSlot).filter(models.ParkingSlot.facility_id == fac.id).all()
        t_slots = len(slots)
        a_slots = sum(1 for s in slots if s.status == "Available")
        o_slots = sum(1 for s in slots if s.status == "Occupied")
        r_slots = sum(1 for s in slots if s.status == "Reserved")
        
        res.append(schemas.ParkingFacilityResponse(
            id=fac.id,
            name=fac.name,
            category=fac.category,
            address=fac.address,
            distance_km=fac.distance_km,
            price_per_hour=fac.price_per_hour,
            opening_hours=fac.opening_hours,
            is_open=fac.is_open,
            image_category=fac.image_category,
            camera_id=fac.camera_id,
            total_slots=t_slots if t_slots > 0 else 10,
            available_slots=a_slots,
            occupied_slots=o_slots,
            reserved_slots=r_slots
        ))
    return res

@router.get("/search", response_model=List[schemas.ParkingFacilityResponse])
def search_facilities(q: str = Query(..., min_length=1), db: Session = Depends(get_db)):
    sync_yolo_for_facilities(db)
    query_str = f"%{q.strip()}%"
    facilities = db.query(models.ParkingFacility).filter(
        (models.ParkingFacility.name.ilike(query_str)) |
        (models.ParkingFacility.category.ilike(query_str)) |
        (models.ParkingFacility.address.ilike(query_str))
    ).all()
    
    res = []
    for fac in facilities:
        slots = db.query(models.ParkingSlot).filter(models.ParkingSlot.facility_id == fac.id).all()
        t_slots = len(slots)
        a_slots = sum(1 for s in slots if s.status == "Available")
        o_slots = sum(1 for s in slots if s.status == "Occupied")
        r_slots = sum(1 for s in slots if s.status == "Reserved")
        
        res.append(schemas.ParkingFacilityResponse(
            id=fac.id,
            name=fac.name,
            category=fac.category,
            address=fac.address,
            distance_km=fac.distance_km,
            price_per_hour=fac.price_per_hour,
            opening_hours=fac.opening_hours,
            is_open=fac.is_open,
            image_category=fac.image_category,
            camera_id=fac.camera_id,
            total_slots=t_slots if t_slots > 0 else 10,
            available_slots=a_slots,
            occupied_slots=o_slots,
            reserved_slots=r_slots
        ))
    return res

@router.get("/{facility_id}", response_model=schemas.FacilityDetailResponse)
def get_facility_detail(facility_id: int, db: Session = Depends(get_db)):
    sync_yolo_for_facilities(db)
    fac = db.query(models.ParkingFacility).filter(models.ParkingFacility.id == facility_id).first()
    if not fac:
        raise HTTPException(status_code=404, detail="Parking facility not found")
    
    slots = db.query(models.ParkingSlot).filter(models.ParkingSlot.facility_id == fac.id).all()
    t_slots = len(slots)
    a_slots = sum(1 for s in slots if s.status == "Available")
    o_slots = sum(1 for s in slots if s.status == "Occupied")
    r_slots = sum(1 for s in slots if s.status == "Reserved")

    return schemas.FacilityDetailResponse(
        id=fac.id,
        name=fac.name,
        category=fac.category,
        address=fac.address,
        distance_km=fac.distance_km,
        price_per_hour=fac.price_per_hour,
        opening_hours=fac.opening_hours,
        is_open=fac.is_open,
        image_category=fac.image_category,
        camera_id=fac.camera_id,
        total_slots=t_slots if t_slots > 0 else 10,
        available_slots=a_slots,
        occupied_slots=o_slots,
        reserved_slots=r_slots,
        slots=slots
    )
