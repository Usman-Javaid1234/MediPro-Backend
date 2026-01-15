from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from decimal import Decimal


class CartItemBase(BaseModel):
    """Base cart item schema"""
    product_id: UUID
    quantity: int = Field(..., ge=1, description="Quantity must be at least 1")


class CartItemCreate(CartItemBase):
    """Schema for adding item to cart"""
    pass


class CartItemUpdate(BaseModel):
    """Schema for updating cart item quantity"""
    quantity: int = Field(..., ge=1)


class ProductInCart(BaseModel):
    """Minimal product info for cart item"""
    id: UUID
    name: str
    price: Decimal
    thumbnail: Optional[str]
    stock_quantity: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class CartItemResponse(BaseModel):
    """Schema for cart item response"""
    id: UUID
    product_id: UUID
    quantity: int
    product: ProductInCart
    subtotal: float
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CartResponse(BaseModel):
    """Schema for full cart response"""
    items: list[CartItemResponse]
    total_items: int
    subtotal: float
    
    @classmethod
    def from_items(cls, items: list):
        """Create cart response from list of cart items"""
        total_items = sum(item.quantity for item in items)
        subtotal = sum(item.subtotal for item in items)
        
        return cls(
            items=items,
            total_items=total_items,
            subtotal=subtotal
        )