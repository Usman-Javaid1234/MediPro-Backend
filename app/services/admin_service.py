from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import Optional, List
import math

from app.models.user import User
from app.models.order import Order
from app.models.product import Product
from app.models.review import Review
from app.schemas.user import AdminUserUpdate, UserListResponse, UserResponse
from app.core.supabase import supabase_client
from app.core.security import get_password_hash
from app.config import settings


class AdminService:
    """Admin service for administrative operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # -------------------- User Management --------------------
    
    async def get_users(
        self,
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None,
        is_admin: Optional[bool] = None,
        search: Optional[str] = None
    ) -> UserListResponse:
        """Get paginated list of users"""
        query = select(User)
        count_query = select(func.count(User.id))
        
        # Apply filters
        if is_active is not None:
            query = query.where(User.is_active == is_active)
            count_query = count_query.where(User.is_active == is_active)
        
        if is_admin is not None:
            query = query.where(User.is_admin == is_admin)
            count_query = count_query.where(User.is_admin == is_admin)
        
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (User.email.ilike(search_filter)) |
                (User.full_name.ilike(search_filter))
            )
            count_query = count_query.where(
                (User.email.ilike(search_filter)) |
                (User.full_name.ilike(search_filter))
            )
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = query.order_by(User.created_at.desc()).offset(offset).limit(page_size)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return UserListResponse(
            items=[UserResponse.model_validate(u) for u in users],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1
        )
    
    async def get_user(self, user_id: UUID) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: UUID, update_data: AdminUserUpdate) -> Optional[User]:
        """Update user (admin)"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        # Update fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.phone is not None:
            user.phone = update_data.phone
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
        if update_data.is_verified is not None:
            user.is_verified = update_data.is_verified
        if update_data.is_admin is not None:
            user.is_admin = update_data.is_admin
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def delete_user(self, user_id: UUID) -> bool:
        """Delete user (soft delete by deactivating)"""
        user = await self.get_user(user_id)
        if not user:
            return False
        
        # Soft delete - deactivate instead of hard delete
        user.is_active = False
        await self.db.commit()
        return True
    
    async def make_admin(self, user_id: UUID) -> Optional[User]:
        """Grant admin privileges to a user"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        user.is_admin = True
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def revoke_admin(self, user_id: UUID) -> Optional[User]:
        """Revoke admin privileges from a user"""
        user = await self.get_user(user_id)
        if not user:
            return None
        
        user.is_admin = False
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    # -------------------- Dashboard Stats --------------------
    
    async def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics for admin"""
        
        # Total users
        users_result = await self.db.execute(select(func.count(User.id)))
        total_users = users_result.scalar()
        
        # Active users
        active_users_result = await self.db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar()
        
        # Total products
        products_result = await self.db.execute(select(func.count(Product.id)))
        total_products = products_result.scalar()
        
        # Active products
        active_products_result = await self.db.execute(
            select(func.count(Product.id)).where(Product.is_active == True)
        )
        active_products = active_products_result.scalar()
        
        # Total orders
        orders_result = await self.db.execute(select(func.count(Order.id)))
        total_orders = orders_result.scalar()
        
        # Orders by status
        from app.models.order import OrderStatus
        pending_orders_result = await self.db.execute(
            select(func.count(Order.id)).where(Order.status == OrderStatus.PENDING)
        )
        pending_orders = pending_orders_result.scalar()
        
        # Total revenue
        from sqlalchemy import case
        revenue_result = await self.db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0))
            .where(Order.status.notin_(['cancelled', 'refunded']))
        )
        total_revenue = float(revenue_result.scalar() or 0)
        
        # Total reviews
        reviews_result = await self.db.execute(select(func.count(Review.id)))
        total_reviews = reviews_result.scalar()
        
        # Low stock products (less than 10)
        low_stock_result = await self.db.execute(
            select(func.count(Product.id))
            .where(Product.stock_quantity < 10)
            .where(Product.is_active == True)
        )
        low_stock_products = low_stock_result.scalar()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users
            },
            "products": {
                "total": total_products,
                "active": active_products,
                "low_stock": low_stock_products
            },
            "orders": {
                "total": total_orders,
                "pending": pending_orders
            },
            "revenue": {
                "total": total_revenue
            },
            "reviews": {
                "total": total_reviews
            }
        }
    
    # -------------------- Initial Admin Setup --------------------
    
    @staticmethod
    async def create_initial_admin(db: AsyncSession) -> Optional[User]:
        """
        Create the initial admin user from environment variables.
        This should only be called once during initial setup.
        
        Returns:
            Created admin user or None if already exists or not configured
        """
        if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
            return None
        
        # Check if admin already exists
        result = await db.execute(
            select(User).where(User.email == settings.ADMIN_EMAIL)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            # If user exists but not admin, make them admin
            if not existing_user.is_admin:
                existing_user.is_admin = True
                await db.commit()
                await db.refresh(existing_user)
            return existing_user
        
        # Create admin user in Supabase Auth
        try:
            auth_response = supabase_client.auth.admin.create_user({
                "email": settings.ADMIN_EMAIL,
                "password": settings.ADMIN_PASSWORD,
                "email_confirm": True  # Auto-confirm email
            })
            
            if not auth_response.user:
                return None
            
            # Create user profile in our database
            admin_user = User(
                id=UUID(auth_response.user.id),
                email=settings.ADMIN_EMAIL,
                full_name=settings.ADMIN_FULL_NAME,
                is_active=True,
                is_verified=True,
                is_admin=True
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            return admin_user
            
        except Exception as e:
            print(f"Error creating admin user: {e}")
            return None
