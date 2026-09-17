from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def uid() -> str:
    return str(uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
    )

    password_hash: Mapped[str] = mapped_column(
        String(512),
    )

    role: Mapped[str] = mapped_column(
        String(32),
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    patient_code: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
    )

    phone: Mapped[str] = mapped_column(
        String(32),
        default="",
    )

    dob: Mapped[str] = mapped_column(
        String(20),
        default="",
    )

    sex: Mapped[str] = mapped_column(
        String(20),
        default="",
    )

    # Links a registered patient to their login account.
    #
    # Nullable is intentional because the existing demo patients
    # do not have login accounts.
    user_id: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=True,
        index=True,
    )

    address: Mapped[str] = mapped_column(
        String(500),
        default="",
    )

    preferred_language: Mapped[str] = mapped_column(
        String(20),
        default="en",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


class Encounter(Base):
    __tablename__ = "encounters"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    token: Mapped[str] = mapped_column(
        String(20),
        index=True,
    )

    department: Mapped[str] = mapped_column(
        String(100),
        default="General OPD",
    )

    language: Mapped[str] = mapped_column(
        String(8),
        default="en",
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="IN_PROGRESS",
    )

    priority: Mapped[str] = mapped_column(
        String(16),
        default="NORMAL",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class KioskSession(Base):
    __tablename__ = "kiosk_sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    token: Mapped[str] = mapped_column(
        String(80),
        unique=True,
        index=True,
    )

    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )


class Consent(Base):
    __tablename__ = "consents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    agreed: Mapped[bool] = mapped_column(
        Boolean,
    )

    scope: Mapped[str] = mapped_column(
        String(255),
        default="clinical intake and document processing",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(64),
    )

    question_id: Mapped[str] = mapped_column(
        String(64),
    )

    raw_answer: Mapped[str] = mapped_column(
        Text,
    )

    structured_answer: Mapped[str] = mapped_column(
        Text,
        default="{}",
    )

    source: Mapped[str] = mapped_column(
        String(32),
        default="PATIENT_REPORTED",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


class MedicalDocument(Base):
    __tablename__ = "medical_documents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    patient_id: Mapped[str] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
    )

    content_type: Mapped[str] = mapped_column(
        String(100),
    )

    category: Mapped[str] = mapped_column(
        String(64),
        default="Other medical document",
    )

    storage_path: Mapped[str] = mapped_column(
        String(512),
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="UPLOADED",
    )

    ocr_text: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )


class ClinicalEntity(Base):
    __tablename__ = "clinical_entities"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(64),
    )

    value: Mapped[str] = mapped_column(
        String(512),
    )

    normalized_value: Mapped[str] = mapped_column(
        String(512),
        default="",
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    source_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("medical_documents.id"),
        nullable=True,
    )

    source_page: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    source_text: Mapped[str] = mapped_column(
        Text,
        default="",
    )

    event_date: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="UNVERIFIED",
    )


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    event_date: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
    )

    event_type: Mapped[str] = mapped_column(
        String(64),
    )

    description: Mapped[str] = mapped_column(
        Text,
    )

    source: Mapped[str] = mapped_column(
        String(64),
    )

    source_document_id: Mapped[str | None] = mapped_column(
        ForeignKey("medical_documents.id"),
        nullable=True,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=1.0,
    )


class RedFlag(Base):
    __tablename__ = "red_flags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        index=True,
    )

    priority: Mapped[str] = mapped_column(
        String(16),
    )

    reason: Mapped[str] = mapped_column(
        Text,
    )

    recommended_action: Mapped[str] = mapped_column(
        Text,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        default="NEW",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )

    acknowledged_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )


class ClinicalSummary(Base):
    __tablename__ = "clinical_summaries"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    encounter_id: Mapped[str] = mapped_column(
        ForeignKey("encounters.id"),
        unique=True,
        index=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
    )

    verification_status: Mapped[str] = mapped_column(
        String(32),
        default="DRAFT",
    )

    verified_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=uid,
    )

    actor_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(128),
    )

    resource_type: Mapped[str] = mapped_column(
        String(64),
    )

    resource_id: Mapped[str] = mapped_column(
        String(64),
    )

    details: Mapped[str] = mapped_column(
        Text,
        default="{}",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
    )