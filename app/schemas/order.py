from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from app.models.order import OrderStatus, PaymentStatus


class OrderItemCreate(BaseModel):
    """Schema for creating order item from cart"""
    product_id: UUID
    quantity: int
    price_at_purchase: Decimal


class ShippingAddress(BaseModel):
    """Schema for shipping address"""
    full_name: str
    phone: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state: Optional[str] = None
    postal_code: str
    country: str = "Pakistan"
    landmark: Optional[str] = None


class OrderCreate(BaseModel):
    """Schema for creating an order"""
    shipping_address: ShippingAddress
    billing_address: Optional[ShippingAddress] = None
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    payment_method: str = "COD"  # Cash on Delivery default
    customer_notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Schema for order item response"""
    id: UUID
    product_id: Optional[UUID]
    product_name: str
    product_sku: Optional[str]
    quantity: int
    price_at_purchase: Decimal
    subtotal: Decimal
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Schema for order response"""
    id: UUID
    order_number: str
    user_id: UUID
    total_amount: Decimal
    subtotal: Decimal
    shipping_cost: Decimal
    tax_amount: Decimal
    discount_amount: Decimal
    status: OrderStatus
    payment_status: PaymentStatus
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]]
    customer_name: str
    customer_email: str
    customer_phone: str
    payment_method: str
    payment_id: Optional[str]
    tracking_number: Optional[str]
    courier_service: Optional[str]
    estimated_delivery_date: Optional[datetime]
    delivered_at: Optional[datetime]
    customer_notes: Optional[str]
    items: List[OrderItemResponse] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class OrderListResponse(BaseModel):
    """Schema for paginated order list"""
    items: List[OrderResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class OrderStatusUpdate(BaseModel):
    """Schema for updating order status"""
    status: OrderStatus


class OrderTrackingUpdate(BaseModel):
    """Schema for updating order tracking"""
    tracking_number: str
    courier_service: str
    estimated_delivery_date: Optional[datetime] = None