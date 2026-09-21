from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import SQLModel, Field, Session, create_engine, select
import bcrypt
import jwt
from datetime import datetime, timedelta

# ------------------- Configuration -------------------
SECRET_KEY = "your-secret-key"  # In production use env variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DATABASE_URL = "sqlite:///./test.db"

# ------------------- Database Setup -------------------
engine = create_engine(DATABASE_URL, echo=False)

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

# ------------------- Utility Functions -------------------

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    payload = decode_access_token(token)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    with Session(engine) as session:
        user = session.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

# ------------------- Request Schemas -------------------
class SignupRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

# ------------------- FastAPI Application -------------------
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# ------------------- Endpoints -------------------
@app.post("/signup", response_model=LoginResponse)
def signup(request: SignupRequest):
    with Session(engine) as session:
        statement = select(User).where(User.email == request.email)
        existing_user = session.exec(statement).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        hashed_password = get_password_hash(request.password)
        user = User(email=request.email, hashed_password=hashed_password)
        session.add(user)
        session.commit()
        session.refresh(user)
        access_token = create_access_token({"sub": str(user.id)})
        return LoginResponse(access_token=access_token)

@app.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        statement = select(User).where(User.email == form_data.username)
        user = session.exec(statement).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Incorrect email or password")
        access_token = create_access_token({"sub": str(user.id)})
        return LoginResponse(access_token=access_token)

@app.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest):
    # Placeholder implementation – in a real app you'd send an email with a reset token.
    return {"message": f"If an account with {request.email} exists, a password reset link has been sent."}

@app.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT – logout is handled on client side by discarding the token.
    return {"message": f"User {current_user.email} logged out successfully"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI application"}

# Example protected route
@app.get("/me")
def read_me(current_user: User = Depends(get_current_user)):
    return {"email": current_user.email, "id": current_user.id}
