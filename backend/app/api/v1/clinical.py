from datetime import datetime, timezone
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import audit, get_current_user, require_roles
from app.core.database import get_db
from app.models.entities import Answer, ClinicalEntity, ClinicalSummary, Encounter, MedicalDocument, Patient, RedFlag, TimelineEvent, User
from app.schemas.api import SummaryUpdate
from app.services.summary import FHIRService

router = APIRouter(tags=["Clinical review"])
CLINICAL_ROLES = ("DOCTOR", "ADMIN")


def patient_detail(db: Session, patient: Patient) -> dict:
    return {"id": patient.id, "patient_code": patient.patient_code, "full_name": patient.full_name, "phone": patient.phone, "dob": patient.dob, "sex": patient.sex}


def encounter_detail(db: Session, encounter: Encounter) -> dict:
    patient = db.get(Patient, encounter.patient_id)
    return {"id": encounter.id, "token": encounter.token, "department": encounter.department, "language": encounter.language, "status": encounter.status, "priority": encounter.priority, "created_at": encounter.created_at, "patient": patient_detail(db, patient)}


@router.get("/patients", tags=["Patients"])
def patients(_user: User = Depends(require_roles(*CLINICAL_ROLES)), db: Session = Depends(get_db)) -> list[dict]:
    return [patient_detail(db, patient) for patient in db.query(Patient).order_by(Patient.created_at.desc()).all()]


@router.get("/patients/{patient_id}", tags=["Patients"])
def patient(patient_id: str, _user: User = Depends(require_roles(*CLINICAL_ROLES)), db: Session = Depends(get_db)) -> dict:
    record = db.get(Patient, patient_id)
    if not record:
        raise HTTPException(404, "Patient not found")
    return patient_detail(db, record)


@router.get("/encounters", tags=["Encounters"])
def encounters(_user: User = Depends(require_roles(*CLINICAL_ROLES)), db: Session = Depends(get_db)) -> list[dict]:
    return [encounter_detail(db, e) for e in db.query(Encounter).order_by(Encounter.created_at.desc()).all()]


@router.get("/encounters/{encounter_id}", tags=["Encounters"])
def encounter(encounter_id: str, _user: User = Depends(require_roles(*CLINICAL_ROLES)), db: Session = Depends(get_db)) -> dict:
    record = db.get(Encounter, encounter_id)
    if not record:
        raise HTTPException(404, "Encounter not found")
    detail = encounter_detail(db, record)
    detail["answers"] = [{"id": a.id, "question_id": a.question_id, "raw_answer": a.raw_answer, "source": a.source} for a in db.query(Answer).filter(Answer.encounter_id == record.id)]
    detail["documents"] = [document_response(d) for d in db.query(MedicalDocument).filter(MedicalDocument.encounter_id == record.id)]
    detail["entities"] = [entity_response(e) for e in db.query(ClinicalEntity).filter(ClinicalEntity.encounter_id == record.id)]
    detail["timeline"] = [timeline_response(t) for t in db.query(TimelineEvent).filter(TimelineEvent.encounter_id == record.id).order_by(TimelineEvent.event_date.desc().nullslast())]
    detail["red_flags"] = [flag_response(f) for f in db.query(RedFlag).filter(RedFlag.encounter_id == record.id)]
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == record.id).one_or_none()
    detail["summary"] = summary_response(summary) if summary else None
    return detail


def document_response(document: MedicalDocument) -> dict:
    return {"id": document.id, "filename": document.filename, "category": document.category, "status": document.status, "confidence": document.confidence, "source_url": f"/api/v1/documents/{document.id}/source", "created_at": document.created_at}


def entity_response(entity: ClinicalEntity) -> dict:
    return {"id": entity.id, "type": entity.entity_type, "value": entity.value, "normalized_value": entity.normalized_value, "confidence": entity.confidence, "source_document_id": entity.source_document_id, "source_page": entity.source_page, "source_text": entity.source_text, "event_date": entity.event_date, "verification_status": entity.verification_status}


def timeline_response(event: TimelineEvent) -> dict:
    return {"id": event.id, "date": event.event_date, "title": event.title, "type": event.event_type, "description": event.description, "source": event.source, "source_document_id": event.source_document_id, "confidence": event.confidence}


def flag_response(flag: RedFlag) -> dict:
    return {"id": flag.id, "encounter_id": flag.encounter_id, "priority": flag.priority, "reason": flag.reason, "recommended_action": flag.recommended_action, "status": flag.status, "created_at": flag.created_at}


def summary_response(summary: ClinicalSummary) -> dict:
    return {"id": summary.id, "encounter_id": summary.encounter_id, "content": summary.content, "verification_status": summary.verification_status, "verified_by": summary.verified_by, "verified_at": summary.verified_at, "updated_at": summary.updated_at}


@router.get("/documents/{document_id}/source", tags=["Documents"])
def view_document(document_id: str, _user: User = Depends(require_roles(*CLINICAL_ROLES)), db: Session = Depends(get_db)) -> FileResponse:
    document = db.get(MedicalDocument, document_id)
    if not document or not Path(document.storage_path).is_file():
        raise HTTPException(404, "Document not found")
    return FileResponse(document.storage_path, media_type=document.content_type, filename=document.filename)


@router.get("/encounters/{encounter_id}/summary", tags=["Summary"])
def get_summary(encounter_id: str, _user: User = Depends(require_roles(*CLINICAL_ROLES)), db: Session = Depends(get_db)) -> dict:
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter_id).one_or_none()
    if not summary:
        raise HTTPException(404, "Summary not found")
    return summary_response(summary)


@router.put("/encounters/{encounter_id}/summary", tags=["Summary"])
def edit_summary(encounter_id: str, payload: SummaryUpdate, user: User = Depends(require_roles("DOCTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter_id).one_or_none()
    if not summary:
        raise HTTPException(404, "Summary not found")
    if summary.verification_status == "VERIFIED":
        raise HTTPException(409, "Verified summaries are immutable")
    summary.content = payload.content
    audit(db, user.id, "EDIT_SUMMARY", "ClinicalSummary", summary.id)
    db.commit()
    return summary_response(summary)


@router.post("/encounters/{encounter_id}/summary/verify", tags=["Verification"])
def verify_summary(encounter_id: str, user: User = Depends(require_roles("DOCTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter_id).one_or_none()
    if not summary:
        raise HTTPException(404, "Summary not found")
    summary.verification_status = "VERIFIED"
    summary.verified_by = user.id
    summary.verified_at = datetime.now(timezone.utc)
    audit(db, user.id, "VERIFY_SUMMARY", "ClinicalSummary", summary.id)
    db.commit()
    return summary_response(summary)


@router.get("/encounters/{encounter_id}/fhir", tags=["FHIR"])
def fhir(encounter_id: str, _user: User = Depends(require_roles("DOCTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    record = db.get(Encounter, encounter_id)
    if not record:
        raise HTTPException(404, "Encounter not found")
    return FHIRService().bundle(db, record)


@router.post("/encounters/{encounter_id}/integrations/{target}", tags=["Integrations"])
def integration(encounter_id: str, target: str, user: User = Depends(require_roles("DOCTOR", "ADMIN")), db: Session = Depends(get_db)) -> dict:
    if target not in {"his", "abdm"}:
        raise HTTPException(404, "Unknown integration")
    if not db.get(Encounter, encounter_id):
        raise HTTPException(404, "Encounter not found")
    audit(db, user.id, f"MOCK_{target.upper()}_SYNC", "Encounter", encounter_id)
    db.commit()
    return {"target": target.upper(), "mode": "mock", "status": "SUCCESS", "message": f"FHIR-compatible record accepted by mock {target.upper()} adapter."}

