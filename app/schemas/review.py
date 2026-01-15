from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class ReviewBase(BaseModel):
    """Base review schema"""
    rating: int = Field(..., ge=1, le=5, description="Rating must be between 1 and 5")
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    """Schema for creating a review"""
    product_id: UUID


class ReviewUpdate(BaseModel):
    """Schema for updating a review"""
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=255)
    comment: Optional[str] = None


class ReviewUserInfo(BaseModel):
    """Minimal user info for review"""
    id: UUID
    full_name: Optional[str]
    
    model_config = ConfigDict(from_attributes=True)


class ReviewResponse(ReviewBase):
    """Schema for review response"""
    id: UUID
    user_id: UUID
    product_id: UUID
    is_verified_purchase: bool
    is_approved: bool
    is_featured: bool
    helpful_count: int
    user: Optional[ReviewUserInfo] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ReviewListResponse(BaseModel):
    """Schema for paginated review list"""
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    average_rating: float