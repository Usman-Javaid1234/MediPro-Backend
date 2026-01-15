from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    is_active: bool
    is_verified: bool
    is_admin: bool = False
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class UserAdminResponse(UserResponse):
    """Schema for admin viewing user details (includes more info)"""
    pass


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserPasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserPasswordReset(BaseModel):
    """Schema for password reset request"""
    email: EmailStr


class UserPasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str = Field(..., min_length=8)


# Admin-specific schemas
class AdminUserUpdate(BaseModel):
    """Schema for admin updating a user"""
    full_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserListResponse(BaseModel):
    """Schema for paginated user list (admin)"""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int