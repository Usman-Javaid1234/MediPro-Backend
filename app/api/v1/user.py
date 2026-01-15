from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.user import UserResponse, UserUpdate, UserPasswordChange
from app.schemas.order import OrderListResponse
from app.models.user import User
from app.services.user_service import UserService
from app.services.order_service import OrderService

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile
    
    - **full_name**: Update full name
    - **phone**: Update phone number
    """
    user_service = UserService(db)
    
    updated_user = await user_service.update_user(
        user_id=current_user.id,
        update_data=update_data
    )
    
    return updated_user


@router.put("/me/password")
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change current user's password
    
    - **current_password**: Current password
    - **new_password**: New password (min 8 characters)
    """
    user_service = UserService(db)
    
    try:
        await user_service.change_password(
            user_id=current_user.id,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        return {"message": "Password changed successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me/orders", response_model=OrderListResponse)
async def get_user_orders(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's order history
    
    - **page**: Page number (default: 1)
    - **page_size**: Items per page (default: 20)
    """
    order_service = OrderService(db)
    
    orders = await order_service.get_user_orders(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return orders