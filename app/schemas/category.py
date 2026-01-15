from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CategoryBase(BaseModel):
    """Base category schema"""
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    color: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    is_featured: bool = False


class CategoryCreate(CategoryBase):
    """Schema for creating a category"""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    parent_id: Optional[UUID] = None
    icon: Optional[str] = None
    image: Optional[str] = None
    color: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Schema for category response"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    product_count: int = 0
    has_subcategories: bool = False
    full_path: str
    
    model_config = ConfigDict(from_attributes=True)


class CategoryWithSubcategories(CategoryResponse):
    """Category with its subcategories"""
    subcategories: List['CategoryResponse'] = []
    
    model_config = ConfigDict(from_attributes=True)


class CategoryTree(BaseModel):
    """Hierarchical category tree structure"""
    id: UUID
    name: str
    slug: str
    icon: Optional[str] = None
    image: Optional[str] = None
    color: Optional[str] = None
    product_count: int = 0
    subcategories: List['CategoryTree'] = []
    
    model_config = ConfigDict(from_attributes=True)


class CategoryListResponse(BaseModel):
    """Schema for paginated category list"""
    items: List[CategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CategorySlugCheck(BaseModel):
    """Schema for checking slug availability"""
    slug: str
    available: bool