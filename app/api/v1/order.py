from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.order import OrderCreate, OrderResponse, OrderStatusUpdate
from app.models.user import User
from app.services.order_service import OrderService

router = APIRouter()


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new order from cart items
    
    - **shipping_address**: Shipping address details
    - **billing_address**: Optional billing address
    - **customer_name**: Customer name
    - **customer_email**: Customer email
    - **customer_phone**: Customer phone
    - **payment_method**: Payment method (COD, card, etc.)
    - **customer_notes**: Optional notes
    """
    order_service = OrderService(db)
    
    try:
        order = await order_service.create_order(
            user_id=current_user.id,
            order_data=order_data
        )
        return order
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get order details by ID
    
    - **order_id**: Order UUID
    """
    order_service = OrderService(db)
    
    order = await order_service.get_order(order_id, current_user.id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/{order_id}/cancel")
async def cancel_order(
    order_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel an order
    
    - **order_id**: Order UUID
    """
    order_service = OrderService(db)
    
    try:
        order = await order_service.cancel_order(order_id, current_user.id)
        
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        
        return {"message": "Order cancelled successfully", "order": order}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Admin endpoints
@router.put("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """
    Update order status (Admin only)
    
    - **order_id**: Order UUID
    - **status**: New order status
    """
    order_service = OrderService(db)
    
    order = await order_service.update_order_status(
        order_id=order_id,
        new_status=status_update.status
    )
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order