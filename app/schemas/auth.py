from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class Token(BaseModel):
    """Schema for JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """Schema for token payload data"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None


class TokenRefresh(BaseModel):
    """Schema for refreshing token"""
    refresh_token: str


class SignupRequest(BaseModel):
    """Schema for user signup"""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Schema for authentication response"""
    user: dict
    session: Token