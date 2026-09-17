from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.api.deps import audit, require_roles
from app.core.database import get_db
from app.models.entities import Encounter, Patient, RedFlag, User
from app.api.v1.clinical import flag_response
from app.schemas.api import FlagUpdate

router = APIRouter(tags=["Triage and operations"])


@router.get("/red-flags")
def flags(_user: User = Depends(require_roles("TRIAGE_STAFF", "DOCTOR", "ADMIN")), db: Session = Depends(get_db)) -> list[dict]:
    output = []
    for flag in db.query(RedFlag).order_by(RedFlag.created_at.desc()).all():
        item = flag_response(flag)
        encounter = db.get(Encounter, flag.encounter_id)
        patient = db.get(Patient, encounter.patient_id) if encounter else None
        item["token"] = encounter.token if encounter else "—"
        item["department"] = encounter.department if encounter else "—"
        item["patient"] = patient.full_name if patient else "Restricted"
        output.append(item)
    return output


@router.patch("/red-flags/{flag_id}")
def update_flag(flag_id: str, payload: FlagUpdate, user: User = Depends(require_roles("TRIAGE_STAFF", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    flag = db.get(RedFlag, flag_id)
    if not flag:
        raise HTTPException(404, "Red flag not found")
    flag.status = payload.status
    if payload.status == "ACKNOWLEDGED":
        flag.acknowledged_by = user.id
    audit(db, user.id, f"TRIAGE_{payload.status}", "RedFlag", flag.id)
    db.commit()
    return flag_response(flag)


@router.get("/dashboard/doctor")
def doctor_dashboard(_user: User = Depends(require_roles("DOCTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    encounters = db.query(Encounter).all()
    return {
        "today_patients": len(encounters),
        "pending_reviews": db.query(Encounter).filter(Encounter.status == "COMPLETED").count(),
        "high_priority_cases": db.query(RedFlag).filter(RedFlag.priority == "HIGH", RedFlag.status != "RESOLVED").count(),
        "completed_consultations": db.query(Encounter).filter(Encounter.status == "COMPLETED").count(),
        "recent_encounters": [{"id": e.id, "token": e.token, "status": e.status, "priority": e.priority, "patient": db.get(Patient, e.patient_id).full_name} for e in sorted(encounters, key=lambda item: item.created_at, reverse=True)[:8]],
    }


@router.get("/dashboard/staff")
def staff_dashboard(_user: User = Depends(require_roles("TRIAGE_STAFF", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    flags = db.query(RedFlag).all()
    return {"new_alerts": sum(flag.status == "NEW" for flag in flags), "high_priority": sum(flag.priority == "HIGH" and flag.status != "RESOLVED" for flag in flags), "active_queue": len(flags)}

