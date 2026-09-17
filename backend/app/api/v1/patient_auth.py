from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import access_token, hash_password, refresh_token, verify_password
from app.models.entities import Patient, User
from app.schemas.api import (
    PatientAuthResponse,
    PatientLoginRequest,
    PatientOut,
    PatientRegisterRequest,
)


router = APIRouter(
    prefix="/patient-auth",
    tags=["Patient Authentication"],
)


def generate_patient_code(db: Session) -> str:
    """
    Generate a unique patient code for a newly registered patient.

    Demo patients use MK-DEMO-001, MK-DEMO-002, etc.
    Real registered patients use MK-XXXXXXXX.
    """
    while True:
        code = f"MK-{uuid4().hex[:8].upper()}"

        exists = (
            db.query(Patient)
            .filter(Patient.patient_code == code)
            .first()
        )

        if not exists:
            return code


def patient_response(
    user: User,
    patient: Patient,
) -> PatientAuthResponse:
    return PatientAuthResponse(
        access_token=access_token(user.id, "PATIENT"),
        refresh_token=refresh_token(user.id, "PATIENT"),
        role="PATIENT",
        patient=PatientOut.model_validate(patient),
    )


@router.post(
    "/register",
    response_model=PatientAuthResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_patient(
    payload: PatientRegisterRequest,
    db: Session = Depends(get_db),
) -> PatientAuthResponse:
    email = payload.email.strip().lower()

    if payload.password != payload.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    existing_user = (
        db.query(User)
        .filter(User.email == email)
        .one_or_none()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    full_name = (
        f"{payload.first_name.strip()} {payload.last_name.strip()}"
    ).strip()

    user = User(
        email=email,
        full_name=full_name,
        password_hash=hash_password(payload.password),
        role="PATIENT",
        active=True,
    )

    try:
        db.add(user)
        db.flush()

        patient = Patient(
            patient_code=generate_patient_code(db),
            full_name=full_name,
            phone=payload.phone.strip(),
            dob=payload.date_of_birth.strip(),
            sex=payload.gender.strip(),
            user_id=user.id,
            address=payload.address.strip(),
            preferred_language=payload.preferred_language,
        )

        db.add(patient)
        db.commit()
        db.refresh(user)
        db.refresh(patient)

        return patient_response(user, patient)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create patient account because the account already exists",
        )


@router.post(
    "/login",
    response_model=PatientAuthResponse,
)
def login_patient(
    payload: PatientLoginRequest,
    db: Session = Depends(get_db),
) -> PatientAuthResponse:
    email = payload.email.strip().lower()

    user = (
        db.query(User)
        .filter(User.email == email)
        .one_or_none()
    )

    if (
        not user
        or not user.active
        or user.role != "PATIENT"
        or not verify_password(payload.password, user.password_hash)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    patient = (
        db.query(Patient)
        .filter(Patient.user_id == user.id)
        .one_or_none()
    )

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Patient account is unavailable",
        )

    return patient_response(user, patient)