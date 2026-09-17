from datetime import datetime, timezone
from fastapi import Depends, Header, HTTPException, status
import jwt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.entities import KioskSession, User


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Authentication required")
    try:
        payload = decode_token(authorization.removeprefix("Bearer "))
    except jwt.PyJWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    user = db.get(User, payload["sub"])
    if not user or not user.active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User is unavailable")
    return user


def require_roles(*roles: str):
    def check(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You do not have permission for this action")
        return user
    return check


def get_kiosk_session(x_kiosk_session: str | None = Header(default=None), db: Session = Depends(get_db)) -> KioskSession:
    if not x_kiosk_session:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kiosk session required")
    session = db.query(KioskSession).filter(KioskSession.token == x_kiosk_session).one_or_none()
    if not session or session.completed or session.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Kiosk session expired")
    return session


def audit(db: Session, actor_id: str | None, action: str, resource_type: str, resource_id: str, details: str = "{}") -> None:
    from app.models.entities import AuditLog
    db.add(AuditLog(actor_id=actor_id, action=action, resource_type=resource_type, resource_id=resource_id, details=details))

