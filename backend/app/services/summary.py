import json
from sqlalchemy.orm import Session
from app.models.entities import Answer, ClinicalEntity, ClinicalSummary, Encounter, Patient, RedFlag, TimelineEvent


class SummaryService:
    def generate(self, db: Session, encounter: Encounter) -> ClinicalSummary:
        patient = db.get(Patient, encounter.patient_id)
        answers = list(db.query(Answer).filter(Answer.encounter_id == encounter.id).order_by(Answer.created_at))
        entities = list(db.query(ClinicalEntity).filter(ClinicalEntity.encounter_id == encounter.id))
        flags = list(db.query(RedFlag).filter(RedFlag.encounter_id == encounter.id))
        current = next((a.raw_answer for a in answers if a.question_id == "chief_complaint"), "Not recorded")
        answer_lines = "; ".join(f"{a.question_id.replace('_', ' ')}: {a.raw_answer}" for a in answers)
        evidence = "; ".join(e.value for e in entities) or "No previous document information extracted."
        alert = " ".join(f.reason for f in flags) or "No configured potential red flags detected."
        content = (f"Pre-consultation record for {patient.full_name}. Current complaint: {current}. "
                   f"Patient-reported history: {answer_lines}. Previous-record evidence: {evidence}. "
                   f"Safety notice: {alert} This is an organized intake summary for clinician review, not a diagnosis.")
        summary = db.query(ClinicalSummary).filter(ClinicalSummary.encounter_id == encounter.id).one_or_none()
        if summary is None:
            summary = ClinicalSummary(encounter_id=encounter.id, content=content)
            db.add(summary)
        elif summary.verification_status != "VERIFIED":
            summary.content = content
        db.commit()
        db.refresh(summary)
        return summary


class FHIRService:
    def bundle(self, db: Session, encounter: Encounter) -> dict:
        patient = db.get(Patient, encounter.patient_id)
        entities = db.query(ClinicalEntity).filter(ClinicalEntity.encounter_id == encounter.id).all()
        return {"resourceType": "Bundle", "type": "collection", "entry": [
            {"resource": {"resourceType": "Patient", "id": patient.id, "identifier": [{"value": patient.patient_code}], "name": [{"text": patient.full_name}], "gender": patient.sex.lower()}},
            {"resource": {"resourceType": "Encounter", "id": encounter.id, "status": "finished" if encounter.status == "COMPLETED" else "in-progress", "subject": {"reference": f"Patient/{patient.id}"}}},
            *[{"resource": {"resourceType": "MedicationStatement" if entity.entity_type == "MEDICATION" else "Observation", "status": "active", "valueString": entity.value, "derivedFrom": [{"display": "Source document evidence"}]}} for entity in entities]
        ]}

