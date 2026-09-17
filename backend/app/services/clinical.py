import re
from sqlalchemy.orm import Session
from app.models.entities import ClinicalEntity, MedicalDocument, TimelineEvent


class MockOCRProvider:
    def extract(self, filename: str, _content: bytes) -> tuple[str, float]:
        name = filename.lower()
        if "lab" in name:
            return "Lab Report 2025-08-14\nHbA1c 7.2 %\nFasting glucose 142 mg/dL", 0.91
        if "discharge" in name:
            return "Discharge Summary 2024-11-20\nHospitalized for community acquired pneumonia.\nFollow-up advised.", 0.89
        return "Prescription 2025-06-10\nTab Metformin 500 mg BD\nTab Paracetamol 500 mg SOS", 0.94


class ClinicalExtractionService:
    medicine_pattern = re.compile(r"(?:Tab|Tablet)\s+([A-Za-z]+)\s+(\d+\s*mg)\s*([A-Za-z]+)?", re.I)
    lab_pattern = re.compile(r"(HbA1c|Fasting glucose)\s+([\d.]+\s*(?:%|mg/dL))", re.I)

    def process_document(self, db: Session, document: MedicalDocument, content: bytes) -> list[ClinicalEntity]:
        text, confidence = MockOCRProvider().extract(document.filename, content)
        document.ocr_text, document.confidence, document.status = text, confidence, "PROCESSED"
        created: list[ClinicalEntity] = []
        for medicine, dose, frequency in self.medicine_pattern.findall(text):
            created.append(ClinicalEntity(encounter_id=document.encounter_id, entity_type="MEDICATION", value=f"{medicine} {dose} {frequency or ''}".strip(), normalized_value=medicine.lower(), confidence=confidence, source_document_id=document.id, source_page=1, source_text=f"Tab {medicine} {dose} {frequency}".strip(), event_date="2025-06-10"))
        for investigation, value in self.lab_pattern.findall(text):
            created.append(ClinicalEntity(encounter_id=document.encounter_id, entity_type="INVESTIGATION", value=f"{investigation}: {value}", normalized_value=investigation.lower(), confidence=confidence, source_document_id=document.id, source_page=1, source_text=f"{investigation} {value}", event_date="2025-08-14"))
        for entity in created:
            db.add(entity)
            db.add(TimelineEvent(encounter_id=document.encounter_id, event_date=entity.event_date, title=entity.entity_type.title(), event_type=entity.entity_type, description=entity.value, source="DOCUMENT", source_document_id=document.id, confidence=entity.confidence))
        db.commit()
        return created

