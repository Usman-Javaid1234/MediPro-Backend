from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.core.security import verify_supabase_token
from app.core.exceptions import InvalidTokenException, UnauthorizedException, ForbiddenException
from app.models.user import User

# HTTP Bearer token security scheme
security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UUID:
    """
    Extract and validate user ID from JWT token
    
    Args:
        credentials: HTTP Authorization credentials with Bearer token
    
    Returns:
        User UUID from token
    
    Raises:
        InvalidTokenException: If token is invalid or expired
    """
    token = credentials.credentials
    
    # Verify Supabase token
    payload = verify_supabase_token(token)
    
    if payload is None:
        raise InvalidTokenException()
    
    user_id = payload.get("sub")
    if user_id is None:
        raise InvalidTokenException()
    
    try:
        return UUID(user_id)
    except ValueError:
        raise InvalidTokenException()


async def get_current_user(
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from database
    
    Args:
        user_id: User UUID from token
        db: Database session
    
    Returns:
        User object
    
    Raises:
        UnauthorizedException: If user not found or inactive
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user is None:
        raise UnauthorizedException(detail="User not found")
    
    if not user.is_active:
        raise UnauthorizedException(detail="User account is inactive")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (additional check)
    
    Args:
        current_user: Current user from token
    
    Returns:
        Active user object
    
    Raises:
        UnauthorizedException: If user is inactive
    """
    if not current_user.is_active:
        raise UnauthorizedException(detail="User account is inactive")
    
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current admin user - requires admin privileges
    
    Args:
        current_user: Current user from token
    
    Returns:
        Admin user object
    
    Raises:
        ForbiddenException: If user is not an admin
    """
    if not current_user.is_admin:
        raise ForbiddenException(detail="Admin privileges required")
    
    return current_user


def get_optional_current_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)
) -> Optional[UUID]:
    """
    Extract user ID from token if provided (optional authentication)
    
    Args:
        credentials: Optional HTTP Authorization credentials
    
    Returns:
        User UUID or None if no token provided
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_supabase_token(token)
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        return UUID(user_id)
    except ValueError:
        return None


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    
    Args:
        credentials: Optional HTTP Authorization credentials
        db: Database session
    
    Returns:
        User object or None
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_supabase_token(token)
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        uuid_id = UUID(user_id)
    except ValueError:
        return None
    
    result = await db.execute(
        select(User).where(User.id == uuid_id)
    )
    return result.scalar_one_or_none()