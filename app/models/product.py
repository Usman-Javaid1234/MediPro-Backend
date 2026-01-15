from sqlalchemy import Column, String, Text, Numeric, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Product(Base):
    """
    Product model - represents medical devices/products
    """
    __tablename__ = "products"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Product information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    short_description = Column(String(500), nullable=True)
    
    # Pricing
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2), nullable=True)  # For showing discounts
    
    # Category and classification
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # Kept for backward compatibility
    subcategory = Column(String(100), nullable=True)
    
    # Inventory
    stock_quantity = Column(Integer, default=0, nullable=False)
    sku = Column(String(100), unique=True, nullable=True, index=True)
    
    # Media
    images = Column(JSONB, default=list)  # Array of image URLs
    thumbnail = Column(String(500), nullable=True)  # Main product image
    
    # Product details
    specifications = Column(JSONB, default=dict)  # Technical specifications
    features = Column(JSONB, default=list)  # List of features
    
    # SEO and metadata
    slug = Column(String(255), unique=True, nullable=True, index=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_featured = Column(Boolean, default=False, index=True)
    
    # Shipping
    weight = Column(Numeric(10, 2), nullable=True)  # in kg
    dimensions = Column(JSONB, default=dict)  # length, width, height
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    category_rel = relationship("Category", back_populates="products")
    cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product {self.name}>"
    
    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        if not self.reviews:
            return 0.0
        return sum(review.rating for review in self.reviews) / len(self.reviews)
    
    @property
    def review_count(self):
        """Get total number of reviews"""
        return len(self.reviews) if self.reviews else 0
    
    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0