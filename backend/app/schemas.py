from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    name: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1500)


class ChatResponse(BaseModel):
    reply: str


class MessageResponse(BaseModel):
    role: str
    content: str
    created_at: datetime
