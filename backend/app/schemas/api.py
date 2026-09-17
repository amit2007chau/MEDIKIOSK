from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(ORMModel):
    id: str
    email: str
    full_name: str
    role: str
    active: bool


TokenResponse.model_rebuild()


class PatientOut(ORMModel):
    id: str
    patient_code: str
    full_name: str
    phone: str
    dob: str
    sex: str
    address: str = ""
    preferred_language: str = "en"


class IdentifyRequest(BaseModel):
    patient_id: str
    language: str = Field(pattern="^(en|hi)$")


class KioskSessionOut(BaseModel):
    kiosk_token: str
    encounter_id: str
    patient: PatientOut
    token: str


class ConsentRequest(BaseModel):
    agreed: bool


class AnswerRequest(BaseModel):
    question_id: str
    answer: str = Field(min_length=1, max_length=2000)
    input_method: str = Field(default="text", pattern="^(text|touch|voice)$")


class DocumentOut(ORMModel):
    id: str
    filename: str
    content_type: str
    category: str
    status: str
    confidence: float
    created_at: datetime


class FlagOut(ORMModel):
    id: str
    encounter_id: str
    priority: str
    reason: str
    recommended_action: str
    status: str
    created_at: datetime


class FlagUpdate(BaseModel):
    status: str = Field(pattern="^(ACKNOWLEDGED|SEEN|ESCALATED|RESOLVED)$")


class SummaryUpdate(BaseModel):
    content: str = Field(min_length=1, max_length=10000)


class CreateUser(BaseModel):
    email: str = Field(min_length=3, max_length=255, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    full_name: str = Field(min_length=2)
    password: str = Field(min_length=8)
    role: str = Field(pattern="^(ADMIN|DOCTOR|TRIAGE_STAFF)$")

class PatientRegisterRequest(BaseModel):
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    date_of_birth: str = Field(
        min_length=4,
        max_length=20,
    )

    gender: str = Field(
        min_length=1,
        max_length=20,
    )

    phone: str = Field(
        min_length=7,
        max_length=32,
    )

    email: str = Field(
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    address: str = Field(
        min_length=2,
        max_length=500,
    )

    preferred_language: str = Field(
        default="en",
        pattern=r"^(en|hi)$",
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )

    confirm_password: str = Field(
        min_length=8,
        max_length=128,
    )


class PatientLoginRequest(BaseModel):
    email: str = Field(
        min_length=3,
        max_length=255,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class PatientAuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    patient: PatientOut