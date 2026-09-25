from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import get_db
from yolo_detector import detector_instance

router = APIRouter(prefix="/api/slots", tags=["Parking Slots"])

def sync_yolo_slots_with_db(db: Session):
    """
    Synchronizes YOLO AI detector real-time slot states with database models.
    When a vehicle exits a slot in the YOLO video feed, slot status automatically
    becomes 'Available' in the database and available for booking in the app!
    """
    yolo_states = detector_instance.get_slot_states()
    db_slots = db.query(models.ParkingSlot).all()
    updated = False

    for slot in db_slots:
        if slot.slot_number in yolo_states:
            new_status = yolo_states[slot.slot_number]
            # If slot was occupied and vehicle exited, set to Available
            if slot.status != new_status:
                # Do not override if user actively reserved it via app unless YOLO detects vehicle exit
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

@router.get("/", response_model=List[schemas.ParkingSlotResponse])
def get_all_slots(db: Session = Depends(get_db)):
    sync_yolo_slots_with_db(db)
    return db.query(models.ParkingSlot).all()

@router.get("/stats", response_model=schemas.DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    sync_yolo_slots_with_db(db)
    slots = db.query(models.ParkingSlot).all()
    total = len(slots)
    available = sum(1 for s in slots if s.status == "Available")
    occupied = sum(1 for s in slots if s.status == "Occupied")
    reserved = sum(1 for s in slots if s.status == "Reserved")

    occ_percentage = ((occupied + reserved) / total * 100) if total > 0 else 0.0

    return schemas.DashboardStats(
        total_slots=total,
        available_slots=available,
        occupied_slots=occupied,
        reserved_slots=reserved,
        occupancy_percentage=round(occ_percentage, 1)
    )

@router.put("/{slot_id}/status", response_model=schemas.ParkingSlotResponse)
def update_slot_status(
    slot_id: int,
    update_data: schemas.SlotStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    slot = db.query(models.ParkingSlot).filter(models.ParkingSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Parking slot not found")

    slot.status = update_data.status
    if update_data.current_vehicle is not None:
        slot.current_vehicle = update_data.current_vehicle
    db.commit()
    db.refresh(slot)
    return slot
