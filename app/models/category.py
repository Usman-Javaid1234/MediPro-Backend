from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Category(Base):
    """
    Category model - represents product categories and subcategories
    Supports hierarchical structure (parent-child relationship)
    """
    __tablename__ = "categories"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Category information
    name = Column(String(100), unique=True, nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Hierarchy support (for subcategories)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Display settings
    icon = Column(String(100), nullable=True)  # Icon name or URL
    image = Column(String(500), nullable=True)  # Category image URL
    color = Column(String(50), nullable=True)  # Hex color for UI
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Display order
    display_order = Column(Integer, default=0)  # For sorting categories
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False)  # Show on homepage
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    products = relationship("Product", back_populates="category_rel", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Category {self.name}>"
    
    @property
    def full_path(self):
        """Get full category path (e.g., 'Medical Devices > Vacuum Pumps')"""
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def product_count(self):
        """Get number of products in this category"""
        return len(self.products) if self.products else 0
    
    @property
    def has_subcategories(self):
        """Check if category has subcategories"""
        return len(self.subcategories) > 0 if hasattr(self, 'subcategories') else False