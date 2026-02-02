import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from backend.src.models.user import UserStatus

class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: str | None
    student_id: str | None
    discord_id: int | None
    notion_id: str | None
    status: UserStatus | None


class UserCreate(BaseModel):
    password: str

class UserResponse(BaseModel):
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    student_id: Optional[int] = None
    discord_id: Optional[int] = None
    status: UserStatus = None