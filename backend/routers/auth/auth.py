import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

import settings
from db import User, get_session
from routers.auth.schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


def get_current_user(token: str):
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        payload_sub = payload.get("sub")
        if payload_sub:
            user_id = uuid.UUID(payload_sub)
            return user_id
        raise HTTPException(status_code=401, detail="invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="token expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="invalid token") from None


def _check_password(password: str, hashed: str | bytes) -> bool:
    if isinstance(hashed, str):
        hashed = hashed.encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


@router.post("/register")
async def register(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=401, detail="user already exist")
    password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user = User(name=user.name, email=user.email, password=password)
    session.add(user)
    session.commit()
    return {"message": "user created successfully"}


@router.post("/login")
async def login(email: str, password: str, session: Session = Depends(get_session)):
    existing_user = session.exec(select(User).where(User.email == email)).first()
    if not existing_user:
        raise HTTPException(status_code=401, detail="invalid credentials")
    if not _check_password(password, existing_user.password):
        raise HTTPException(status_code=401, detail="invalid credentials")
    expires = datetime.now(UTC) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    token = jwt.encode(
        {"sub": str(existing_user.id), "exp": expires},
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return {"message": "login successful", "token": token}


@router.get("/me")
async def me(token: str = Depends(get_current_user)):
    return {"message": "user information", "user": token}
