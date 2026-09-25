import datetime
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/reservations", tags=["Reservations & Booking"])

@router.post("/", response_model=schemas.ReservationResponse)
def create_reservation(
    req: schemas.ReservationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    slot = db.query(models.ParkingSlot).filter(models.ParkingSlot.id == req.slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Parking slot not found")
    
    if slot.status == "Occupied":
        raise HTTPException(status_code=400, detail="Slot is currently occupied by another vehicle")
    
    # Calculate price in INR (₹)
    total_amount = slot.price_per_hour * req.hours
    booking_id = f"PE-{uuid.uuid4().hex[:8].upper()}"
    start = datetime.datetime.utcnow()
    end = start + datetime.timedelta(hours=req.hours)
    
    # 1. Create Reservation record
    new_res = models.Reservation(
        booking_id=booking_id,
        user_id=current_user.id,
        slot_id=slot.id,
        vehicle_number=req.vehicle_number,
        hours=req.hours,
        total_amount=total_amount,
        status="Active",
        start_time=start,
        end_time=end
    )
    db.add(new_res)
    db.commit()
    db.refresh(new_res)
    
    # 2. Update Slot status to Reserved
    slot.status = "Reserved"
    slot.current_vehicle = req.vehicle_number
    
    # 3. Create Payment record (Simulated instant transaction)
    txn_id = f"TXN-PARK-{uuid.uuid4().hex[:10].upper()}"
    new_pay = models.Payment(
        transaction_id=txn_id,
        reservation_id=new_res.id,
        user_id=current_user.id,
        amount=total_amount,
        payment_method=req.payment_method,
        payment_status="SUCCESS"
    )
    db.add(new_pay)
    
    # 4. Dispatch SMS Acknowledgement to Registered Mobile Number
    sms_message = (
        f"ParkEazy Booking Confirmed! Booking ID: {booking_id}. "
        f"Slot: {slot.slot_number} ({slot.zone}). Vehicle: {req.vehicle_number}. "
        f"Duration: {req.hours}hr(s). Paid: Rs.{total_amount:.2f} via {req.payment_method}. "
        f"Show this SMS at entry gate. Thank you!"
    )
    sms_entry = models.SMSLog(
        phone_number=current_user.phone_number,
        message=sms_message,
        status="DELIVERED"
    )
    db.add(sms_entry)
    db.commit()

    return schemas.ReservationResponse(
        id=new_res.id,
        booking_id=new_res.booking_id,
        slot_id=slot.id,
        slot_number=slot.slot_number,
        zone=slot.zone,
        vehicle_number=new_res.vehicle_number,
        hours=new_res.hours,
        total_amount=new_res.total_amount,
        status=new_res.status,
        created_at=new_res.created_at,
        start_time=new_res.start_time,
        end_time=new_res.end_time,
        payment_transaction_id=txn_id
    )

@router.get("/my-bookings", response_model=List[schemas.ReservationResponse])
def get_user_reservations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    reservations = db.query(models.Reservation).filter(
        models.Reservation.user_id == current_user.id
    ).order_by(models.Reservation.created_at.desc()).all()
    
    result = []
    for r in reservations:
        txn_id = r.payment.transaction_id if r.payment else "TXN-SIMULATED"
        result.append(schemas.ReservationResponse(
            id=r.id,
            booking_id=r.booking_id,
            slot_id=r.slot_id,
            slot_number=r.slot.slot_number if r.slot else f"Slot #{r.slot_id}",
            zone=r.slot.zone if r.slot else "Zone A",
            vehicle_number=r.vehicle_number,
            hours=r.hours,
            total_amount=r.total_amount,
            status=r.status,
            created_at=r.created_at,
            start_time=r.start_time,
            end_time=r.end_time,
            payment_transaction_id=txn_id
        ))
    return result

@router.post("/{reservation_id}/cancel")
def cancel_reservation(
    reservation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    res = db.query(models.Reservation).filter(
        models.Reservation.id == reservation_id,
        models.Reservation.user_id == current_user.id
    ).first()
    if not res:
        raise HTTPException(status_code=404, detail="Reservation not found")
    
    res.status = "Cancelled"
    if res.slot:
        res.slot.status = "Available"
        res.slot.current_vehicle = None
    db.commit()
    return {"message": f"Reservation {res.booking_id} cancelled successfully."}
