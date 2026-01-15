from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.supabase import supabase_client


class UserService:
    """User management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user(self, user_id: UUID) -> User:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_user(self, user_id: UUID, update_data: UserUpdate) -> User:
        """Update user profile"""
        user = await self.get_user(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Update fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        if update_data.phone is not None:
            user.phone = update_data.phone
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def change_password(
        self,
        user_id: UUID,
        current_password: str,
        new_password: str
    ) -> None:
        """Change user password"""
        user = await self.get_user(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Use Supabase to update password
        # This requires the user to be authenticated
        supabase_client.auth.update_user({
            "password": new_password
        })