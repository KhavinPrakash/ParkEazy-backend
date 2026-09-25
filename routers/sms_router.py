from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import models, schemas, auth
from database import get_db

router = APIRouter(prefix="/api/sms", tags=["SMS Acknowledgements"])

@router.get("/my-sms", response_model=List[schemas.SMSLogResponse])
def get_user_sms_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    logs = db.query(models.SMSLog).filter(
        models.SMSLog.phone_number == current_user.phone_number
    ).order_by(models.SMSLog.sent_at.desc()).all()
    return logs
