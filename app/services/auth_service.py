from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Dict, Any

from app.core.supabase import supabase_client
from app.core.security import create_access_token, create_refresh_token
from app.models.user import User
from app.schemas.auth import Token


class AuthService:
    """Authentication service for user signup, login, and token management"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def signup(
        self,
        email: str,
        password: str,
        full_name: str = None,
        phone: str = None
    ) -> Dict[str, Any]:
        """
        Register a new user using Supabase Auth
        
        Args:
            email: User email
            password: User password
            full_name: Optional full name
            phone: Optional phone number
        
        Returns:
            Dict with user data and session tokens
        
        Raises:
            Exception: If signup fails
        """
        # Create user in Supabase Auth
        auth_response = supabase_client.auth.sign_up({
            "email": email,
            "password": password,
        })
        
        if not auth_response.user:
            raise Exception("Failed to create user")
        
        # Create user profile in our database
        user = User(
            id=UUID(auth_response.user.id),
            email=email,
            full_name=full_name,
            phone=phone,
            is_active=True,
            is_verified=False
        )
        
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone
            },
            "session": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 1800  # 30 minutes
            }
        }
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user using Supabase Auth
        
        Args:
            email: User email
            password: User password
        
        Returns:
            Dict with user data and session tokens
        
        Raises:
            Exception: If login fails
        """
        # Authenticate with Supabase
        print(email)
        print(password)
        auth_response = supabase_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if not auth_response.user:
            raise Exception("Invalid credentials")
        
        # Get user from database
        result = await self.db.execute(
            select(User).where(User.id == UUID(auth_response.user.id))
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise Exception("User not found")
        
        # Create tokens
        access_token = create_access_token({"sub": str(user.id), "email": user.email})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "phone": user.phone
            },
            "session": {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 1800  # 30 minutes
            }
        }
    
    async def refresh_token(self, refresh_token: str) -> Token:
        """
        Refresh access token using refresh token
        
        Args:
            refresh_token: Valid refresh token
        
        Returns:
            New token pair
        
        Raises:
            Exception: If refresh fails
        """
        # Refresh session with Supabase
        auth_response = supabase_client.auth.refresh_session(refresh_token)
        
        if not auth_response.user:
            raise Exception("Invalid refresh token")
        
        # Create new tokens
        access_token = create_access_token({
            "sub": auth_response.user.id,
            "email": auth_response.user.email
        })
        new_refresh_token = create_refresh_token({"sub": auth_response.user.id})
        
        return Token(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=1800
        )
    
    async def forgot_password(self, email: str) -> None:
        """
        Send password reset email
        
        Args:
            email: User email
        """
        # Use Supabase password reset
        supabase_client.auth.reset_password_email(email)
    
    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset password using token
        
        Args:
            token: Password reset token
            new_password: New password
        
        Raises:
            Exception: If reset fails
        """
        # Use Supabase to update password
        # This would typically be handled on the frontend with Supabase client
        # Backend just validates the process
        pass