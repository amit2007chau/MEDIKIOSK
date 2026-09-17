from fastapi import APIRouter
from app.api.v1 import admin, auth, clinical, kiosk, operations, patient_auth


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth.router)
api_router.include_router(patient_auth.router)
api_router.include_router(kiosk.router)
api_router.include_router(clinical.router)
api_router.include_router(operations.router)
api_router.include_router(admin.router)