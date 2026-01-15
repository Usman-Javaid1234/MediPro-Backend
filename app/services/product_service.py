from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from uuid import UUID
from typing import Optional
import math

from app.models.product import Product
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductFilter,
    ProductListResponse,
    ProductResponse
)


class ProductService:
    """Product management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_products(self, filters: ProductFilter) -> ProductListResponse:
        """Get paginated list of products with filters"""
        query = select(Product)
        
        # Apply filters
        if filters.category:
            query = query.where(Product.category == filters.category)
        
        if filters.subcategory:
            query = query.where(Product.subcategory == filters.subcategory)
        
        if filters.min_price:
            query = query.where(Product.price >= filters.min_price)
        
        if filters.max_price:
            query = query.where(Product.price <= filters.max_price)
        
        if filters.is_featured is not None:
            query = query.where(Product.is_featured == filters.is_featured)
        
        if filters.is_active is not None:
            query = query.where(Product.is_active == filters.is_active)
        
        if filters.in_stock_only:
            query = query.where(Product.stock_quantity > 0)
        
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Product.name.ilike(search_term),
                    Product.description.ilike(search_term)
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        if filters.sort_by == "price":
            order_column = Product.price
        elif filters.sort_by == "name":
            order_column = Product.name
        else:
            order_column = Product.created_at
        
        if filters.sort_order == "asc":
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # Apply pagination
        offset = (filters.page - 1) * filters.page_size
        query = query.offset(offset).limit(filters.page_size)
        
        # Execute query
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        # Calculate total pages
        total_pages = math.ceil(total / filters.page_size) if total > 0 else 0
        
        return ProductListResponse(
            items=products,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages
        )
    
    async def get_product(self, product_id: UUID) -> Optional[Product]:
        """Get single product by ID"""
        result = await self.db.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def create_product(self, product_data: ProductCreate) -> Product:
        """Create new product"""
        product = Product(**product_data.model_dump())
        
        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        
        return product
    
    async def update_product(
        self,
        product_id: UUID,
        product_data: ProductUpdate
    ) -> Optional[Product]:
        """Update product"""
        product = await self.get_product(product_id)
        
        if not product:
            return None
        
        # Update fields
        update_dict = product_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(product, field, value)
        
        await self.db.commit()
        await self.db.refresh(product)
        
        return product
    
    async def delete_product(self, product_id: UUID) -> bool:
        """Delete product"""
        product = await self.get_product(product_id)
        
        if not product:
            return False
        
        await self.db.delete(product)
        await self.db.commit()
        
        return True