from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: str
    short_description: Optional[str] = None
    price: Decimal = Field(..., gt=0, decimal_places=2)
    original_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category: str
    subcategory: Optional[str] = None
    stock_quantity: int = Field(default=0, ge=0)
    sku: Optional[str] = None


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    images: Optional[List[str]] = []
    thumbnail: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = {}
    features: Optional[List[str]] = []
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, Any]] = {}


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    original_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category: Optional[str] = None
    subcategory: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    sku: Optional[str] = None
    images: Optional[List[str]] = None
    thumbnail: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    slug: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    weight: Optional[Decimal] = None
    dimensions: Optional[Dict[str, Any]] = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: UUID
    images: List[str]
    thumbnail: Optional[str]
    specifications: Dict[str, Any]
    features: List[str]
    slug: Optional[str]
    meta_title: Optional[str]
    meta_description: Optional[str]
    is_active: bool
    is_featured: bool
    weight: Optional[Decimal]
    dimensions: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    average_rating: float = 0.0
    review_count: int = 0
    is_in_stock: bool = True
    
    model_config = ConfigDict(from_attributes=True)


class ProductListResponse(BaseModel):
    """Schema for paginated product list"""
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProductFilter(BaseModel):
    """Schema for filtering products"""
    category: Optional[str] = None
    subcategory: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    is_featured: Optional[bool] = None
    is_active: Optional[bool] = True
    in_stock_only: bool = False
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)