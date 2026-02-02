import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr
from src.models.user import UserStatus


class UserBase(BaseModel):
    username: str
    email: EmailStr
    phone: str | None = None
    student_id: str | None = None
    discord_id: int | None = None
    notion_id: str | None = None
    status: UserStatus | None = None


class UserCreate(UserBase):
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
