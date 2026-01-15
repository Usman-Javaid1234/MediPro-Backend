from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.database import get_db
from app.schemas.product import (
    ProductResponse, 
    ProductListResponse, 
    ProductFilter
)
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    is_featured: Optional[bool] = None,
    in_stock_only: bool = False,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of products with filtering and pagination
    
    - **category**: Filter by category
    - **subcategory**: Filter by subcategory
    - **min_price**: Minimum price filter
    - **max_price**: Maximum price filter
    - **is_featured**: Filter featured products
    - **in_stock_only**: Show only in-stock products
    - **search**: Search in product name and description
    - **sort_by**: Sort field (created_at, price, name)
    - **sort_order**: Sort direction (asc, desc)
    - **page**: Page number
    - **page_size**: Items per page
    """
    product_service = ProductService(db)
    
    filters = ProductFilter(
        category=category,
        subcategory=subcategory,
        min_price=min_price,
        max_price=max_price,
        is_featured=is_featured,
        in_stock_only=in_stock_only,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size
    )
    
    products = await product_service.get_products(filters)
    return products


@router.get("/featured", response_model=ProductListResponse)
async def get_featured_products(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Get featured products
    
    - **limit**: Number of products to return (max 50)
    """
    product_service = ProductService(db)
    
    filters = ProductFilter(
        is_featured=True,
        is_active=True,
        page=1,
        page_size=limit
    )
    
    products = await product_service.get_products(filters)
    return products


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single product by ID
    
    - **product_id**: Product UUID
    """
    product_service = ProductService(db)
    
    product = await product_service.get_product(product_id)
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product