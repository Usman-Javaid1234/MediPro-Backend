from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
import math

from app.models.review import Review
from app.models.order import Order, OrderItem
from app.schemas.review import ReviewCreate, ReviewUpdate, ReviewListResponse


class ReviewService:
    """Product review management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_review(
        self,
        user_id: UUID,
        review_data: ReviewCreate
    ) -> Review:
        """Create a product review"""
        # Check if user already reviewed this product
        existing = await self.db.execute(
            select(Review).where(
                Review.user_id == user_id,
                Review.product_id == review_data.product_id
            )
        )
        
        if existing.scalar_one_or_none():
            raise ValueError("You have already reviewed this product")
        
        # Check if user purchased this product
        order_result = await self.db.execute(
            select(OrderItem)
            .join(Order)
            .where(
                Order.user_id == user_id,
                OrderItem.product_id == review_data.product_id
            )
        )
        is_verified_purchase = order_result.scalar_one_or_none() is not None
        
        # Create review
        review = Review(
            user_id=user_id,
            product_id=review_data.product_id,
            rating=review_data.rating,
            title=review_data.title,
            comment=review_data.comment,
            is_verified_purchase=is_verified_purchase
        )
        
        self.db.add(review)
        await self.db.commit()
        await self.db.refresh(review)
        
        return review
    
    async def get_product_reviews(
        self,
        product_id: UUID,
        page: int = 1,
        page_size: int = 10,
        rating_filter: Optional[int] = None
    ) -> ReviewListResponse:
        """Get paginated reviews for a product"""
        query = select(Review).where(
            Review.product_id == product_id,
            Review.is_approved == True
        ).options(selectinload(Review.user))
        
        if rating_filter:
            query = query.where(Review.rating == rating_filter)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()
        
        # Calculate average rating
        avg_query = select(func.avg(Review.rating)).where(
            Review.product_id == product_id,
            Review.is_approved == True
        )
        avg_rating = (await self.db.execute(avg_query)).scalar() or 0.0
        
        # Get reviews
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        reviews = result.scalars().all()
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ReviewListResponse(
            items=reviews,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            average_rating=float(avg_rating)
        )
    
    async def update_review(
        self,
        review_id: UUID,
        user_id: UUID,
        update_data: ReviewUpdate
    ) -> Optional[Review]:
        """Update a review"""
        result = await self.db.execute(
            select(Review).where(
                Review.id == review_id,
                Review.user_id == user_id
            )
        )
        review = result.scalar_one_or_none()
        
        if not review:
            return None
        
        # Update fields
        if update_data.rating is not None:
            review.rating = update_data.rating
        if update_data.title is not None:
            review.title = update_data.title
        if update_data.comment is not None:
            review.comment = update_data.comment
        
        await self.db.commit()
        await self.db.refresh(review)
        
        return review
    
    async def delete_review(self, review_id: UUID, user_id: UUID) -> bool:
        """Delete a review"""
        result = await self.db.execute(
            select(Review).where(
                Review.id == review_id,
                Review.user_id == user_id
            )
        )
        review = result.scalar_one_or_none()
        
        if not review:
            return False
        
        await self.db.delete(review)
        await self.db.commit()
        
        return True
    
    async def get_user_reviews(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 10
    ) -> ReviewListResponse:
        """Get user's reviews"""
        query = select(Review).where(Review.user_id == user_id)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar()
        
        # Get reviews
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query
            .options(selectinload(Review.product))
            .order_by(Review.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        reviews = result.scalars().all()
        
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return ReviewListResponse(
            items=reviews,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            average_rating=0.0  # Not applicable for user reviews
        )