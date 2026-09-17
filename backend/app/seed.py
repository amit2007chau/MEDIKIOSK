"""Idempotent synthetic-demo data seeding. Never use production clinical data here."""
from pathlib import Path
from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models.entities import ClinicalEntity, ClinicalSummary, Encounter, MedicalDocument, Patient, RedFlag, TimelineEvent, User


DEMO_USERS = [
    ("admin@medikiosk.local", "MediKiosk Administrator", "ADMIN"),
    ("doctor@medikiosk.local", "Dr. Anika Rao", "DOCTOR"),
    ("staff@medikiosk.local", "Triage Nurse Meera", "TRIAGE_STAFF"),
]
DEMO_PATIENTS = [
    ("MK-DEMO-001", "Aarav Sharma", "9000001001", "1985-04-22", "male"),
    ("MK-DEMO-002", "Diya Verma", "9000001002", "1974-09-10", "female"),
    ("MK-DEMO-003", "Kabir Singh", "9000001003", "1992-02-14", "male"),
    ("MK-DEMO-004", "Ira Nair", "9000001004", "1988-07-08", "female"),
    ("MK-DEMO-005", "Vihan Patel", "9000001005", "1966-12-01", "male"),
]


def seed() -> None:
    Base.metadata.create_all(engine)
    db = SessionLocal()
    try:
        for email, full_name, role in DEMO_USERS:
            if not db.query(User).filter(User.email == email).first():
                db.add(User(email=email, full_name=full_name, password_hash=hash_password("DemoPass123!"), role=role))
        db.commit()
        patients: list[Patient] = []
        for code, name, phone, dob, sex in DEMO_PATIENTS:
            patient = db.query(Patient).filter(Patient.patient_code == code).one_or_none()
            if not patient:
                patient = Patient(patient_code=code, full_name=name, phone=phone, dob=dob, sex=sex)
                db.add(patient)
                db.flush()
            patients.append(patient)
        db.commit()
        if db.query(Encounter).count() == 0:
            complaint_data = [("Fever", "NORMAL"), ("Chest pain", "HIGH"), ("Headache", "NORMAL"), ("General consultation", "NORMAL"), ("AYUSH consultation", "NORMAL")]
            for index, (patient, (complaint, priority)) in enumerate(zip(patients, complaint_data), start=101):
                encounter = Encounter(patient_id=patient.id, token=f"A{index}", language="en", status="COMPLETED", priority=priority)
                db.add(encounter)
                db.flush()
                db.add(TimelineEvent(encounter_id=encounter.id, event_date=None, title="Patient-reported information", event_type="CURRENT_VISIT", description=f"chief complaint: {complaint}", source="PATIENT_REPORTED", confidence=1.0))
                summary = ClinicalSummary(encounter_id=encounter.id, content=f"Synthetic demo pre-consultation record. Current complaint: {complaint}. This is an intake aid for clinician review, not a diagnosis.")
                db.add(summary)
                if priority == "HIGH":
                    db.add(RedFlag(encounter_id=encounter.id, priority="HIGH", reason="Potential urgent symptom combination detected: Chest pain with breathing difficulty.", recommended_action="Immediate clinical assessment recommended."))
                if index == 101:
                    documents = [
                        ("synthetic-prescription.pdf", "Prescription", "Prescription 2025-06-10\nTab Metformin 500 mg BD", "MEDICATION", "Metformin 500 mg BD", "2025-06-10", 0.94),
                        ("synthetic-lab-report.pdf", "Lab report", "Lab Report 2025-08-14\nHbA1c 7.2 %\nFasting glucose 142 mg/dL", "INVESTIGATION", "HbA1c: 7.2%", "2025-08-14", 0.91),
                        ("synthetic-discharge-summary.pdf", "Discharge summary", "Discharge Summary 2024-11-20\nHospitalized for community acquired pneumonia.", "HOSPITALIZATION", "Community acquired pneumonia hospitalization", "2024-11-20", 0.89),
                    ]
                    for filename, category, text, entity_type, value, event_date, confidence in documents:
                        doc = MedicalDocument(patient_id=patient.id, encounter_id=encounter.id, filename=filename, content_type="application/pdf", category=category, storage_path="", status="PROCESSED", ocr_text=text, confidence=confidence)
                        db.add(doc)
                        db.flush()
                        path = Path("uploads") / f"{doc.id}_{filename}"
                        path.parent.mkdir(exist_ok=True)
                        path.write_text(f"Synthetic demo document only.\n{text}", encoding="utf-8")
                        doc.storage_path = str(path)
                        db.add(ClinicalEntity(encounter_id=encounter.id, entity_type=entity_type, value=value, normalized_value=value.lower(), confidence=confidence, source_document_id=doc.id, source_page=1, source_text=text.splitlines()[-1], event_date=event_date))
                        db.add(TimelineEvent(encounter_id=encounter.id, event_date=event_date, title=entity_type.title(), event_type=entity_type, description=value, source="DOCUMENT", source_document_id=doc.id, confidence=confidence))
            db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed()
