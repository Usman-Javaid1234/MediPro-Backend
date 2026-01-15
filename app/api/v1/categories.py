from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
    CategoryTree,
    CategorySlugCheck,
    CategoryWithSubcategories
)
from app.services.category_service import CategoryService

router = APIRouter()


@router.get("/", response_model=CategoryListResponse)
async def get_categories(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    parent_id: Optional[UUID] = None,
    is_active: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of categories with filtering and pagination
    
    - **parent_id**: Filter by parent category (null for main categories)
    - **is_active**: Filter by active status
    - **is_featured**: Filter by featured status
    - **search**: Search in name and description
    - **page**: Page number
    - **page_size**: Items per page
    """
    category_service = CategoryService(db)
    
    categories = await category_service.get_categories(
        page=page,
        page_size=page_size,
        parent_id=parent_id,
        is_active=is_active,
        is_featured=is_featured,
        search=search
    )
    
    return categories


@router.get("/main", response_model=List[CategoryResponse])
async def get_main_categories(db: AsyncSession = Depends(get_db)):
    """
    Get all main categories (categories without parent)
    """
    category_service = CategoryService(db)
    categories = await category_service.get_main_categories()
    return categories


@router.get("/tree", response_model=List[CategoryTree])
async def get_category_tree(db: AsyncSession = Depends(get_db)):
    """
    Get hierarchical category tree structure
    Useful for navigation menus and category selectors
    """
    category_service = CategoryService(db)
    tree = await category_service.get_category_tree()
    return tree


@router.get("/check-slug/{slug}", response_model=CategorySlugCheck)
async def check_slug_availability(
    slug: str,
    category_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Check if a slug is available
    
    - **slug**: Slug to check
    - **category_id**: Optional category ID to exclude from check (for updates)
    """
    category_service = CategoryService(db)
    available = await category_service.check_slug_availability(slug, category_id)
    
    return CategorySlugCheck(slug=slug, available=available)


@router.get("/{category_id}", response_model=CategoryWithSubcategories)
async def get_category(
    category_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single category by ID with its subcategories
    
    - **category_id**: Category UUID
    """
    category_service = CategoryService(db)
    category = await category_service.get_category(category_id)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.get("/slug/{slug}", response_model=CategoryWithSubcategories)
async def get_category_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get single category by slug with its subcategories
    
    - **slug**: Category slug
    """
    category_service = CategoryService(db)
    category = await category_service.get_category_by_slug(slug)
    
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return category


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """
    Create a new category (Admin only)
    
    - **name**: Category name (unique)
    - **slug**: URL-friendly identifier (unique)
    - **parent_id**: Optional parent category for subcategories
    - **description**: Optional description
    - **icon**: Optional icon name/URL
    - **image**: Optional category image URL
    - **color**: Optional hex color for UI
    - **display_order**: Order for sorting (default: 0)
    - **is_active**: Active status (default: true)
    - **is_featured**: Featured on homepage (default: false)
    """
    category_service = CategoryService(db)
    
    try:
        category = await category_service.create_category(category_data)
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    category_data: CategoryUpdate,
    db: AsyncSession = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """
    Update a category (Admin only)
    
    - **category_id**: Category UUID
    """
    category_service = CategoryService(db)
    
    try:
        category = await category_service.update_category(category_id, category_data)
        
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        return category
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: UUID,
    force: bool = Query(False, description="Force delete even if category has products/subcategories"),
    db: AsyncSession = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """
    Delete a category (Admin only)
    
    - **category_id**: Category UUID
    - **force**: If true, delete even if category has products or subcategories
    
    **Warning:** 
    - Products in deleted category will become uncategorized
    - Subcategories will become main categories
    """
    category_service = CategoryService(db)
    
    try:
        deleted = await category_service.delete_category(category_id, force)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )
        
        return None
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/reorder", status_code=status.HTTP_200_OK)
async def reorder_categories(
    category_orders: List[dict],
    db: AsyncSession = Depends(get_db)
    # TODO: Add admin authentication dependency
):
    """
    Update display order for multiple categories (Admin only)
    
    **Request body example:**
    ```json
    [
        {"id": "uuid-1", "display_order": 1},
        {"id": "uuid-2", "display_order": 2},
        {"id": "uuid-3", "display_order": 3}
    ]
    ```
    """
    category_service = CategoryService(db)
    
    await category_service.reorder_categories(category_orders)
    
    return {"message": "Categories reordered successfully"}