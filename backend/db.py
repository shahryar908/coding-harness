from sqlmodel import SQLModel,Field,create_engine,Session
from pydantic import BaseModel
import uuid
from datetime import datetime
from typing import Optional



class User(SQLModel,table=True):
    id:uuid.UUID = Field(default_factory=uuid.uuid4,primary_key=True)
    name:str    
    email:str
    password:str
    created_at:datetime = Field(default_factory=datetime.now)
    updated_at:datetime = Field(default_factory=datetime.now)



engine = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

