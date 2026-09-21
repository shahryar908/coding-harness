from fastapi import APIRouter,Depends,HTTPException
from db import get_session,User
from routers.auth.schemas import UserCreate
from sqlmodel import Session,select
import bcrypt
import jwt
import uuid


router = APIRouter(prefix="/auth",tags=["auth"])


def get_current_user(token:str):
    try: 
       payload=jwt.decode(token,"secret_key",algorithms=["HS256"])
       payload_sub=payload.get("sub")
       if payload_sub:
           user_id=uuid.UUID(payload_sub)
           return user_id
       raise HTTPException(status_code=401,detail="invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401,detail="token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401,detail="invalid token")

@router.post("/register")
async def register(user:UserCreate,session:Session = Depends(get_session)):
    existing_user=session.exec(select(User).where(User.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=401,detail="user already exist")
    password=bcrypt.hashpw(user.password.encode("utf-8"),bcrypt.gensalt())
    user=User(name=user.name,email=user.email,password=password)
    session.add(user)
    session.commit()
    return {"message":"user created successfully"}

@router.post("/login")
async def login(email:str,password:str,session:Session = Depends(get_session)):
    existing_user=session.exec(select(User).where(User.email == email)).first()
    if not existing_user:
        raise HTTPException(status_code=401,detail="invalid credentials")
    if not bcrypt.checkpw(password.encode("utf-8"),existing_user.password):
        raise HTTPException(status_code=401,detail="invalid credentials")
    token=jwt.encode({"sub":str(existing_user.id)},"secret_key",algorithm="HS256")
    return {"message":"login successful","token":token}



@router.get("/me")
async def me(token:str = Depends(get_current_user)):
    return {"message":"user information","user":token}