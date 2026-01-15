from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional

from app.models.cart import CartItem
from app.models.product import Product
from app.schemas.cart import CartResponse


class CartService:
    """Shopping cart management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_cart(self, user_id: UUID) -> CartResponse:
        """Get user's cart with all items"""
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
        )
        cart_items = result.scalars().all()
        
        return CartResponse.from_items(cart_items)
    
    async def add_to_cart(
        self,
        user_id: UUID,
        product_id: UUID,
        quantity: int
    ) -> CartItem:
        """Add item to cart or update quantity if exists"""
        # Check if product exists and is available
        product_result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        product = product_result.scalar_one_or_none()
        
        if not product:
            raise ValueError("Product not found")
        
        if not product.is_active:
            raise ValueError("Product is not available")
        
        if product.stock_quantity < quantity:
            raise ValueError("Insufficient stock")
        
        # Check if item already in cart
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if cart_item:
            # Update existing quantity
            cart_item.quantity += quantity
            
            if cart_item.quantity > product.stock_quantity:
                raise ValueError("Insufficient stock")
        else:
            # Create new cart item
            cart_item = CartItem(
                user_id=user_id,
                product_id=product_id,
                quantity=quantity
            )
            self.db.add(cart_item)
        
        await self.db.commit()
        await self.db.refresh(cart_item)
        
        # Load product relationship
        await self.db.refresh(cart_item, ['product'])
        
        return cart_item
    
    async def update_cart_item(
        self,
        item_id: UUID,
        user_id: UUID,
        quantity: int
    ) -> Optional[CartItem]:
        """Update cart item quantity"""
        result = await self.db.execute(
            select(CartItem)
            .where(CartItem.id == item_id, CartItem.user_id == user_id)
            .options(selectinload(CartItem.product))
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return None
        
        # Check stock
        if cart_item.product.stock_quantity < quantity:
            raise ValueError("Insufficient stock")
        
        cart_item.quantity = quantity
        
        await self.db.commit()
        await self.db.refresh(cart_item)
        
        return cart_item
    
    async def remove_from_cart(
        self,
        item_id: UUID,
        user_id: UUID
    ) -> bool:
        """Remove item from cart"""
        result = await self.db.execute(
            select(CartItem).where(
                CartItem.id == item_id,
                CartItem.user_id == user_id
            )
        )
        cart_item = result.scalar_one_or_none()
        
        if not cart_item:
            return False
        
        await self.db.delete(cart_item)
        await self.db.commit()
        
        return True
    
    async def clear_cart(self, user_id: UUID) -> None:
        """Clear all items from user's cart"""
        result = await self.db.execute(
            select(CartItem).where(CartItem.user_id == user_id)
        )
        cart_items = result.scalars().all()
        
        for item in cart_items:
            await self.db.delete(item)
        
        await self.db.commit()