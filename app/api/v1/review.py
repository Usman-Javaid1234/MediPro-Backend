from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional

from app.database import get_db
from app.api.deps import get_current_user
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewResponse, ReviewListResponse
from app.models.user import User
from app.services.review_service import ReviewService

router = APIRouter()


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    review_data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a product review
    
    - **product_id**: Product UUID
    - **rating**: Rating 1-5 stars
    - **title**: Optional review title
    - **comment**: Optional review text
    """
    review_service = ReviewService(db)
    
    try:
        review = await review_service.create_review(
            user_id=current_user.id,
            review_data=review_data
        )
        return review
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/product/{product_id}", response_model=ReviewListResponse)
async def get_product_reviews(
    product_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    rating: Optional[int] = Query(None, ge=1, le=5),
    db: AsyncSession = Depends(get_db)
):
    """
    Get reviews for a product
    
    - **product_id**: Product UUID
    - **page**: Page number
    - **page_size**: Items per page
    - **rating**: Filter by rating (1-5)
    """
    review_service = ReviewService(db)
    
    reviews = await review_service.get_product_reviews(
        product_id=product_id,
        page=page,
        page_size=page_size,
        rating_filter=rating
    )
    
    return reviews


@router.put("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: UUID,
    update_data: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a review (only by review author)
    
    - **review_id**: Review UUID
    - **rating**: New rating
    - **title**: New title
    - **comment**: New comment
    """
    review_service = ReviewService(db)
    
    try:
        review = await review_service.update_review(
            review_id=review_id,
            user_id=current_user.id,
            update_data=update_data
        )
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found or you don't have permission to update it"
            )
        
        return review
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a review (only by review author)
    
    - **review_id**: Review UUID
    """
    review_service = ReviewService(db)
    
    deleted = await review_service.delete_review(
        review_id=review_id,
        user_id=current_user.id
    )
    
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or you don't have permission to delete it"
        )
    
    return None


@router.get("/my-reviews", response_model=ReviewListResponse)
async def get_my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's reviews
    
    - **page**: Page number
    - **page_size**: Items per page
    """
    review_service = ReviewService(db)
    
    reviews = await review_service.get_user_reviews(
        user_id=current_user.id,
        page=page,
        page_size=page_size
    )
    
    return reviews