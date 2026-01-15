from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.api.deps import get_current_admin_user
from app.models.user import User
from app.schemas.user import (
    UserResponse,
    UserListResponse,
    AdminUserUpdate
)
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryListResponse
from app.schemas.order import OrderResponse, OrderListResponse, OrderStatusUpdate
from app.services.admin_service import AdminService
from app.services.product_service import ProductService
from app.services.category_service import CategoryService
from app.services.order_service import OrderService
from app.config import settings

router = APIRouter()


# -------------------- Dashboard --------------------

@router.get("/dashboard")
async def get_dashboard_stats(
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get admin dashboard statistics
    
    Returns summary stats for users, products, orders, revenue
    """
    admin_service = AdminService(db)
    return await admin_service.get_dashboard_stats()


# -------------------- User Management --------------------

@router.get("/users", response_model=UserListResponse)
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None,
    is_admin: Optional[bool] = None,
    search: Optional[str] = None,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paginated list of users (Admin only)
    """
    admin_service = AdminService(db)
    return await admin_service.get_users(
        page=page,
        page_size=page_size,
        is_active=is_active,
        is_admin=is_admin,
        search=search
    )


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (Admin only)
    """
    admin_service = AdminService(db)
    user = await admin_service.get_user(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    update_data: AdminUserUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user (Admin only)
    
    Can update: full_name, phone, is_active, is_verified, is_admin
    """
    # Prevent admin from removing their own admin status
    if user_id == admin.id and update_data.is_admin == False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove your own admin privileges"
        )
    
    admin_service = AdminService(db)
    user = await admin_service.update_user(user_id, update_data)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user - soft delete by deactivating (Admin only)
    """
    # Prevent admin from deleting themselves
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    admin_service = AdminService(db)
    deleted = await admin_service.delete_user(user_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return None


@router.post("/users/{user_id}/make-admin", response_model=UserResponse)
async def make_user_admin(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant admin privileges to a user (Admin only)
    """
    admin_service = AdminService(db)
    user = await admin_service.make_admin(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.post("/users/{user_id}/revoke-admin", response_model=UserResponse)
async def revoke_user_admin(
    user_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Revoke admin privileges from a user (Admin only)
    """
    # Prevent admin from revoking their own admin status
    if user_id == admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges"
        )
    
    admin_service = AdminService(db)
    user = await admin_service.revoke_admin(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


# -------------------- Product Management --------------------

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new product (Admin only)
    """
    product_service = ProductService(db)
    return await product_service.create_product(product_data)


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_data: ProductUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a product (Admin only)
    """
    product_service = ProductService(db)
    product = await product_service.update_product(product_id, product_data)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a product (Admin only)
    """
    product_service = ProductService(db)
    deleted = await product_service.delete_product(product_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return None


# -------------------- Category Management --------------------

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new category (Admin only)
    """
    category_service = CategoryService(db)
    return await category_service.create_category(category_data)


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a category (Admin only)
    """
    category_service = CategoryService(db)
    category = await category_service.update_category(category_id, category_data)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a category (Admin only)
    """
    category_service = CategoryService(db)
    deleted = await category_service.delete_category(category_id)
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return None


# -------------------- Order Management --------------------

@router.get("/orders", response_model=OrderListResponse)
async def get_all_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all orders (Admin only)
    """
    order_service = OrderService(db)
    return await order_service.get_all_orders(
        page=page,
        page_size=page_size,
        status_filter=status_filter
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order_admin(
    order_id: UUID,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get order by ID (Admin only - can view any order)
    """
    order_service = OrderService(db)
    order = await order_service.get_order_admin(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.put("/orders/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: UUID,
    status_update: OrderStatusUpdate,
    admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update order status (Admin only)
    """
    order_service = OrderService(db)
    order = await order_service.update_order_status(order_id, status_update.status)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


# -------------------- Initial Admin Setup --------------------

@router.post("/setup", response_model=UserResponse)
async def setup_initial_admin(
    setup_secret: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Create initial admin user from environment variables.
    
    Requires ADMIN_SETUP_SECRET to be provided.
    This endpoint should be called once during initial setup.
    
    - **setup_secret**: The secret key from ADMIN_SETUP_SECRET env var
    """
    # Verify setup secret
    if not settings.ADMIN_SETUP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin setup not configured. Set ADMIN_SETUP_SECRET in environment."
        )
    
    if setup_secret != settings.ADMIN_SETUP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid setup secret"
        )
    
    # Verify admin credentials are configured
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin credentials not configured. Set ADMIN_EMAIL and ADMIN_PASSWORD in environment."
        )
    
    # Create admin user
    admin_user = await AdminService.create_initial_admin(db)
    
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin user"
        )
    
    return admin_user