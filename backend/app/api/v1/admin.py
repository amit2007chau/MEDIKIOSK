from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import audit, require_roles
from app.core.database import get_db
from app.core.security import hash_password
from app.models.entities import AuditLog, User
from app.schemas.api import CreateUser, UserOut

router = APIRouter(prefix="/admin", tags=["Administration"])


@router.get("/users", response_model=list[UserOut])
def users(_user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).order_by(User.email).all()


@router.post("/users", response_model=UserOut)
def create_user(payload: CreateUser, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(409, "Email is already in use")
    user = User(email=payload.email.lower(), full_name=payload.full_name, password_hash=hash_password(payload.password), role=payload.role)
    db.add(user)
    db.flush()
    audit(db, actor.id, "CREATE_USER", "User", user.id)
    db.commit()
    return user


@router.post("/users/{user_id}/toggle", response_model=UserOut)
def toggle_user(user_id: str, actor: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "User not found")
    if user.id == actor.id:
        raise HTTPException(400, "You cannot deactivate your own account")
    user.active = not user.active
    audit(db, actor.id, "TOGGLE_USER", "User", user.id)
    db.commit()
    return user


@router.get("/audit-logs")
def logs(_user: User = Depends(require_roles("ADMIN")), db: Session = Depends(get_db)) -> list[dict]:
    return [{"id": item.id, "action": item.action, "resource_type": item.resource_type, "resource_id": item.resource_id, "created_at": item.created_at} for item in db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(200)]


@router.get("/red-flag-rules")
def flag_rules(_user: User = Depends(require_roles("ADMIN"))) -> list[dict]:
    return [{"id": "chest-pain-breath", "when": "Chest pain + severe breathing difficulty", "priority": "HIGH", "action": "Immediate clinical assessment recommended."}, {"id": "severe-breath", "when": "Severe breathing difficulty", "priority": "HIGH", "action": "Immediate clinical assessment recommended."}]

