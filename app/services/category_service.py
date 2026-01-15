from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional, List
import math
import re

from app.models.category import Category
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryListResponse,
    CategoryTree,
    CategoryWithSubcategories
)


class CategoryService:
    """Category management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    def generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from category name"""
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug
    
    async def check_slug_availability(self, slug: str, category_id: Optional[UUID] = None) -> bool:
        """Check if slug is available"""
        query = select(Category).where(Category.slug == slug)
        
        if category_id:
            query = query.where(Category.id != category_id)
        
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()
        
        return existing is None
    
    async def create_category(self, category_data: CategoryCreate) -> Category:
        """Create a new category"""
        # Check if slug is available
        is_available = await self.check_slug_availability(category_data.slug)
        if not is_available:
            raise ValueError(f"Slug '{category_data.slug}' is already in use")
        
        # If parent_id provided, verify parent exists
        if category_data.parent_id:
            parent_result = await self.db.execute(
                select(Category).where(Category.id == category_data.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            if not parent:
                raise ValueError("Parent category not found")
        
        # Create category
        category = Category(**category_data.model_dump())
        
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        
        return category
    
    async def get_category(self, category_id: UUID) -> Optional[Category]:
        """Get category by ID"""
        result = await self.db.execute(
            select(Category)
            .where(Category.id == category_id)
            .options(selectinload(Category.subcategories))
            .options(selectinload(Category.products))
        )
        return result.scalar_one_or_none()
    
    async def get_category_by_slug(self, slug: str) -> Optional[Category]:
        """Get category by slug"""
        result = await self.db.execute(
            select(Category)
            .where(Category.slug == slug)
            .options(selectinload(Category.subcategories))
            .options(selectinload(Category.products))
        )
        return result.scalar_one_or_none()
    
    async def get_categories(
        self,
        page: int = 1,
        page_size: int = 50,
        parent_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None
    ) -> CategoryListResponse:
        """Get paginated list of categories"""
        query = select(Category)
        
        # Apply filters
        if parent_id is not None:
            query = query.where(Category.parent_id == parent_id)
        
        if is_active is not None:
            query = query.where(Category.is_active == is_active)
        
        if is_featured is not None:
            query = query.where(Category.is_featured == is_featured)
        
        if search:
            search_term = f"%{search}%"
            query = query.where(
                or_(
                    Category.name.ilike(search_term),
                    Category.description.ilike(search_term)
                )
            )
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting and pagination
        query = query.order_by(Category.display_order.asc(), Category.name.asc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)
        
        # Execute query
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        # Calculate total pages
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return CategoryListResponse(
            items=categories,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
    
    async def get_main_categories(self) -> List[Category]:
        """Get all main categories (no parent)"""
        result = await self.db.execute(
            select(Category)
            .where(Category.parent_id.is_(None), Category.is_active == True)
            .order_by(Category.display_order.asc(), Category.name.asc())
        )
        return result.scalars().all()
    
    async def get_category_tree(self) -> List[CategoryTree]:
        """Get hierarchical category tree"""
        # Get all active categories
        result = await self.db.execute(
            select(Category)
            .where(Category.is_active == True)
            .options(selectinload(Category.subcategories))
            .options(selectinload(Category.products))
            .order_by(Category.display_order.asc(), Category.name.asc())
        )
        all_categories = result.scalars().all()
        
        # Build tree structure
        category_map = {cat.id: cat for cat in all_categories}
        tree = []
        
        for category in all_categories:
            if category.parent_id is None:
                # This is a root category
                tree.append(self._build_category_tree_node(category, category_map))
        
        return tree
    
    def _build_category_tree_node(self, category: Category, category_map: dict) -> CategoryTree:
        """Build a single node in the category tree"""
        subcategories = [
            self._build_category_tree_node(category_map[subcat.id], category_map)
            for subcat in category.subcategories
            if subcat.id in category_map and subcat.is_active
        ]
        
        return CategoryTree(
            id=category.id,
            name=category.name,
            slug=category.slug,
            icon=category.icon,
            image=category.image,
            color=category.color,
            product_count=category.product_count,
            subcategories=subcategories
        )
    
    async def update_category(
        self,
        category_id: UUID,
        category_data: CategoryUpdate
    ) -> Optional[Category]:
        """Update category"""
        category = await self.get_category(category_id)
        
        if not category:
            return None
        
        # Check slug availability if slug is being updated
        if category_data.slug and category_data.slug != category.slug:
            is_available = await self.check_slug_availability(category_data.slug, category_id)
            if not is_available:
                raise ValueError(f"Slug '{category_data.slug}' is already in use")
        
        # Check parent_id if being updated
        if category_data.parent_id:
            # Prevent circular reference
            if category_data.parent_id == category_id:
                raise ValueError("Category cannot be its own parent")
            
            # Verify parent exists
            parent_result = await self.db.execute(
                select(Category).where(Category.id == category_data.parent_id)
            )
            parent = parent_result.scalar_one_or_none()
            if not parent:
                raise ValueError("Parent category not found")
        
        # Update fields
        update_dict = category_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(category, field, value)
        
        await self.db.commit()
        await self.db.refresh(category)
        
        return category
    
    async def delete_category(self, category_id: UUID, force: bool = False) -> bool:
        """
        Delete category
        
        Args:
            category_id: Category ID to delete
            force: If True, delete even if category has products or subcategories
        
        Returns:
            True if deleted, False if not found
        
        Raises:
            ValueError: If category has products/subcategories and force=False
        """
        category = await self.get_category(category_id)
        
        if not category:
            return False
        
        # Check if category has products
        if not force and category.product_count > 0:
            raise ValueError(
                f"Category has {category.product_count} products. "
                "Set force=True to delete anyway (products will be uncategorized)."
            )
        
        # Check if category has subcategories
        if not force and category.has_subcategories:
            raise ValueError(
                "Category has subcategories. "
                "Set force=True to delete anyway (subcategories will become main categories)."
            )
        
        await self.db.delete(category)
        await self.db.commit()
        
        return True
    
    async def reorder_categories(self, category_orders: List[dict]) -> bool:
        """
        Update display order for multiple categories
        
        Args:
            category_orders: List of {"id": UUID, "display_order": int}
        """
        for item in category_orders:
            result = await self.db.execute(
                select(Category).where(Category.id == item["id"])
            )
            category = result.scalar_one_or_none()
            
            if category:
                category.display_order = item["display_order"]
        
        await self.db.commit()
        return True