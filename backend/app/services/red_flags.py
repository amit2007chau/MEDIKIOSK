from sqlalchemy.orm import Session
from app.models.entities import Answer, Encounter, RedFlag


class RedFlagService:
    """Deterministic, configurable-in-code safety rules; never a diagnostic service."""
    def evaluate(self, db: Session, encounter: Encounter) -> list[RedFlag]:
        answers = {a.question_id: a.raw_answer.lower() for a in db.query(Answer).filter(Answer.encounter_id == encounter.id)}
        complaint = answers.get("chief_complaint", "")
        breath = answers.get("breathing_difficulty", "")
        rules: list[tuple[bool, str, str]] = [
            ("chest" in complaint and breath in {"severe", "yes"}, "Chest pain with breathing difficulty", "Immediate clinical assessment recommended."),
            (breath == "severe" or "severe" in breath, "Severe breathing difficulty reported", "Immediate clinical assessment recommended."),
            ("loss of consciousness" in complaint, "Loss of consciousness reported", "Immediate clinical assessment recommended."),
            ("bleeding" in complaint and "severe" in complaint, "Severe bleeding reported", "Immediate clinical assessment recommended."),
        ]
        existing = {flag.reason for flag in db.query(RedFlag).filter(RedFlag.encounter_id == encounter.id)}
        flags = [RedFlag(encounter_id=encounter.id, priority="HIGH", reason=f"Potential urgent symptom combination detected: {reason}.", recommended_action=action) for applies, reason, action in rules if applies and f"Potential urgent symptom combination detected: {reason}." not in existing]
        if flags:
            encounter.priority = "HIGH"
            db.add_all(flags)
            db.commit()
        return flags

