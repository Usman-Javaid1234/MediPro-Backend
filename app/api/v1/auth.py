from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import SignupRequest, LoginRequest, AuthResponse, Token, TokenRefresh
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    - **email**: User's email address
    - **password**: User's password (min 8 characters)
    - **full_name**: Optional full name
    - **phone**: Optional phone number
    """
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.signup(
            email=signup_data.email,
            password=signup_data.password,
            full_name=signup_data.full_name,
            phone=signup_data.phone
        )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user with email and password
    
    - **email**: User's email address
    - **password**: User's password
    """
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.login(
            email=login_data.email,
            password=login_data.password
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using refresh token
    
    - **refresh_token**: Valid refresh token
    """
    auth_service = AuthService(db)
    
    try:
        result = await auth_service.refresh_token(token_data.refresh_token)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )


@router.post("/logout")
async def logout(db: AsyncSession = Depends(get_db)):
    """
    Logout user (client should discard tokens)
    """
    # In a stateless JWT system, logout is handled client-side
    # Optionally implement token blacklisting here
    return {"message": "Logged out successfully"}


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset email
    
    - **email**: User's email address
    """
    auth_service = AuthService(db)
    
    try:
        await auth_service.forgot_password(email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        # Don't reveal if email exists for security
        return {"message": "If the email exists, a reset link will be sent"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password using token from email
    
    - **token**: Password reset token
    - **new_password**: New password
    """
    auth_service = AuthService(db)
    
    try:
        await auth_service.reset_password(token, new_password)
        return {"message": "Password reset successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )