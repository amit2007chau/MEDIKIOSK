from datetime import datetime, timedelta, timezone
from pathlib import Path
from secrets import token_urlsafe
import json
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.api.deps import get_kiosk_session
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import Answer, Consent, Encounter, KioskSession, MedicalDocument, Patient, TimelineEvent
from app.schemas.api import AnswerRequest, ConsentRequest, DocumentOut, IdentifyRequest, KioskSessionOut, PatientOut
from app.services.clinical import ClinicalExtractionService
from app.services.question_engine import next_question
from app.services.red_flags import RedFlagService
from app.services.summary import SummaryService
from app.services.events import triage_hub
from app.services.storage import DocumentStorage

router = APIRouter(prefix="/kiosk", tags=["Patient kiosk"])
SUPPORTED_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def answers_for(db: Session, encounter_id: str) -> dict[str, str]:
    return {a.question_id: a.raw_answer for a in db.query(Answer).filter(Answer.encounter_id == encounter_id)}


@router.get("/demo-patients", response_model=list[PatientOut])
def demo_patients(db: Session = Depends(get_db)) -> list[Patient]:
    return db.query(Patient).order_by(Patient.patient_code).all()


@router.post("/identify", response_model=KioskSessionOut)
def identify(payload: IdentifyRequest, db: Session = Depends(get_db)) -> KioskSessionOut:
    patient = db.get(Patient, payload.patient_id)
    if not patient:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found")
    encounter = Encounter(patient_id=patient.id, token=f"A{100 + db.query(Encounter).count()}", language=payload.language)
    db.add(encounter)
    db.flush()
    kiosk_token = token_urlsafe(32)
    session = KioskSession(token=kiosk_token, patient_id=patient.id, encounter_id=encounter.id, expires_at=datetime.now(timezone.utc) + timedelta(minutes=30))
    db.add(session)
    db.commit()
    return KioskSessionOut(kiosk_token=kiosk_token, encounter_id=encounter.id, patient=PatientOut.model_validate(patient), token=encounter.token)


@router.post("/consent")
def record_consent(payload: ConsentRequest, session: KioskSession = Depends(get_kiosk_session), db: Session = Depends(get_db)) -> dict:
    db.add(Consent(patient_id=session.patient_id, encounter_id=session.encounter_id, agreed=payload.agreed))
    db.commit()
    return {"agreed": payload.agreed, "message": "Consent recorded" if payload.agreed else "Collection has been stopped. You may ask staff for assistance."}


@router.get("/interview/current")
def current_question(session: KioskSession = Depends(get_kiosk_session), db: Session = Depends(get_db)) -> dict:
    encounter = db.get(Encounter, session.encounter_id)
    question = next_question(answers_for(db, encounter.id), encounter.language)
    return {"question": question, "complete": question is None}


@router.post("/interview/answer")
async def submit_answer(payload: AnswerRequest, session: KioskSession = Depends(get_kiosk_session), db: Session = Depends(get_db)) -> dict:
    encounter = db.get(Encounter, session.encounter_id)
    expected = next_question(answers_for(db, encounter.id), encounter.language)
    if not expected or expected["id"] != payload.question_id:
        raise HTTPException(status.HTTP_409_CONFLICT, "Answer does not match the current question")
    db.add(Answer(encounter_id=encounter.id, category=expected["category"], question_id=payload.question_id, raw_answer=payload.answer, structured_answer=json.dumps({"value": payload.answer, "language": encounter.language}), source="PATIENT_REPORTED"))
    db.add(TimelineEvent(encounter_id=encounter.id, event_date=None, title="Patient-reported information", event_type="CURRENT_VISIT", description=f"{payload.question_id.replace('_', ' ')}: {payload.answer}", source="PATIENT_REPORTED", source_document_id=None, confidence=1.0))
    db.commit()
    new_flags = RedFlagService().evaluate(db, encounter)
    for flag in new_flags:
        await triage_hub.broadcast({"type": "red_flag_created", "flag": {"id": flag.id, "encounter_id": flag.encounter_id, "priority": flag.priority, "reason": flag.reason, "status": flag.status}})
    return {"transcript": payload.answer, "next": next_question(answers_for(db, encounter.id), encounter.language), "potential_red_flags": len(new_flags)}


def process_uploaded_document(document_id: str, content: bytes) -> None:
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        document = db.get(MedicalDocument, document_id)
        if document:
            ClinicalExtractionService().process_document(db, document, content)
    finally:
        db.close()


@router.post("/documents", response_model=DocumentOut)
async def upload_document(background_tasks: BackgroundTasks, category: str = Form(default="Other medical document"), file: UploadFile = File(...), session: KioskSession = Depends(get_kiosk_session), db: Session = Depends(get_db)) -> MedicalDocument:
    if file.content_type not in SUPPORTED_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Only PDF, JPG, JPEG, and PNG files are accepted")
    content = await file.read()
    if not content or len(content) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File is empty or exceeds 10 MB limit")
    safe_name = Path(file.filename or "medical-document").name
    document = MedicalDocument(patient_id=session.patient_id, encounter_id=session.encounter_id, filename=safe_name, content_type=file.content_type, category=category, storage_path="")
    db.add(document)
    db.flush()
    document.storage_path = DocumentStorage().mirror_and_store(document.id, safe_name, content)
    db.commit()
    db.refresh(document)
    background_tasks.add_task(process_uploaded_document, document.id, content)
    return document


@router.get("/documents/{document_id}/source")
def source_document(document_id: str, session: KioskSession = Depends(get_kiosk_session), db: Session = Depends(get_db)) -> FileResponse:
    document = db.get(MedicalDocument, document_id)
    if not document or document.patient_id != session.patient_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Document not found")
    return FileResponse(document.storage_path, media_type=document.content_type, filename=document.filename)


@router.post("/complete")
def complete(session: KioskSession = Depends(get_kiosk_session), db: Session = Depends(get_db)) -> dict:
    encounter = db.get(Encounter, session.encounter_id)
    if next_question(answers_for(db, encounter.id), encounter.language):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Please complete required questions first")
    encounter.status = "COMPLETED"
    encounter.completed_at = datetime.now(timezone.utc)
    session.completed = True
    db.commit()
    summary = SummaryService().generate(db, encounter)
    return {"message": "Your information has been securely submitted for review.", "encounter_id": encounter.id, "summary_status": summary.verification_status}
