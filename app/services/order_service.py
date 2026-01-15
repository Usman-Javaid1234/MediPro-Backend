from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from uuid import UUID
from typing import Optional
from datetime import datetime
import math

from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.cart import CartItem
from app.models.product import Product
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse, OrderItemResponse


class OrderService:
    """Order management service"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(self, user_id: UUID, order_data: OrderCreate) -> Order:
        """
        Create a new order from user's cart
        
        Args:
            user_id: User UUID
            order_data: Order details
        
        Returns:
            Created order
        
        Raises:
            ValueError: If cart is empty or product unavailable
        """
        # Get user's cart items
        cart_result = await self.db.execute(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == user_id)
        )
        cart_items = cart_result.scalars().all()
        
        if not cart_items:
            raise ValueError("Cart is empty")
        
        # Calculate totals and validate stock
        subtotal = 0
        order_items = []
        
        for cart_item in cart_items:
            product = cart_item.product
            
            if not product or not product.is_active:
                raise ValueError(f"Product '{cart_item.product_id}' is not available")
            
            if product.stock_quantity < cart_item.quantity:
                raise ValueError(f"Insufficient stock for '{product.name}'")
            
            item_subtotal = float(product.price) * cart_item.quantity
            subtotal += item_subtotal
            
            order_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "product_sku": product.sku,
                "quantity": cart_item.quantity,
                "price_at_purchase": product.price,
                "subtotal": item_subtotal
            })
        
        # Calculate shipping (free over 5000 PKR)
        shipping_cost = 0 if subtotal >= 5000 else 250
        total_amount = subtotal + shipping_cost
        
        # Generate order number
        order_number = f"MP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(user_id)[:4].upper()}"
        
        # Create order
        order = Order(
            user_id=user_id,
            order_number=order_number,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax_amount=0,
            discount_amount=0,
            total_amount=total_amount,
            status=OrderStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            shipping_address=order_data.shipping_address.model_dump(),
            billing_address=order_data.billing_address.model_dump() if order_data.billing_address else None,
            customer_name=order_data.customer_name,
            customer_email=order_data.customer_email,
            customer_phone=order_data.customer_phone,
            payment_method=order_data.payment_method,
            customer_notes=order_data.customer_notes
        )
        
        self.db.add(order)
        await self.db.flush()  # Get order ID
        
        # Create order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.id,
                **item_data
            )
            self.db.add(order_item)
            
            # Reduce product stock
            product_result = await self.db.execute(
                select(Product).where(Product.id == item_data["product_id"])
            )
            product = product_result.scalar_one()
            product.stock_quantity -= item_data["quantity"]
        
        # Clear user's cart
        await self.db.execute(
            CartItem.__table__.delete().where(CartItem.user_id == user_id)
        )
        
        await self.db.commit()
        await self.db.refresh(order)
        
        # Load items relationship
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order.id)
        )
        return result.scalar_one()
    
    async def get_order(self, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Get order by ID (user can only view their own orders)"""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
            .where(Order.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_order_admin(self, order_id: UUID) -> Optional[Order]:
        """Get order by ID (admin can view any order)"""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_user_orders(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 10,
        status_filter: Optional[str] = None
    ) -> OrderListResponse:
        """Get paginated orders for a user"""
        query = select(Order).where(Order.user_id == user_id)
        count_query = select(func.count(Order.id)).where(Order.user_id == user_id)
        
        if status_filter:
            try:
                status_enum = OrderStatus(status_filter)
                query = query.where(Order.status == status_enum)
                count_query = count_query.where(Order.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = (
            query
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return OrderListResponse(
            items=[self._order_to_response(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1
        )
    
    async def get_all_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[str] = None
    ) -> OrderListResponse:
        """Get all orders (admin)"""
        query = select(Order)
        count_query = select(func.count(Order.id))
        
        if status_filter:
            try:
                status_enum = OrderStatus(status_filter)
                query = query.where(Order.status == status_enum)
                count_query = count_query.where(Order.status == status_enum)
            except ValueError:
                pass
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        offset = (page - 1) * page_size
        query = (
            query
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return OrderListResponse(
            items=[self._order_to_response(o) for o in orders],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=math.ceil(total / page_size) if total > 0 else 1
        )
    
    async def update_order_status(
        self,
        order_id: UUID,
        new_status: OrderStatus
    ) -> Optional[Order]:
        """Update order status (admin only)"""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return None
        
        order.status = new_status
        
        # Update payment status based on order status
        if new_status == OrderStatus.DELIVERED:
            order.payment_status = PaymentStatus.PAID
            order.delivered_at = datetime.utcnow()
        elif new_status == OrderStatus.CANCELLED:
            if order.payment_status == PaymentStatus.PAID:
                order.payment_status = PaymentStatus.REFUNDED
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    async def cancel_order(self, order_id: UUID, user_id: UUID) -> Optional[Order]:
        """Cancel an order (user can only cancel their own pending orders)"""
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items))
            .where(Order.id == order_id)
            .where(Order.user_id == user_id)
        )
        order = result.scalar_one_or_none()
        
        if not order:
            return None
        
        # Can only cancel pending or confirmed orders
        if order.status not in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
            raise ValueError("Order cannot be cancelled at this stage")
        
        order.status = OrderStatus.CANCELLED
        
        # Restore product stock
        for item in order.items:
            if item.product_id:
                product_result = await self.db.execute(
                    select(Product).where(Product.id == item.product_id)
                )
                product = product_result.scalar_one_or_none()
                if product:
                    product.stock_quantity += item.quantity
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return order
    
    def _order_to_response(self, order: Order) -> OrderResponse:
        """Convert Order model to response schema"""
        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            user_id=order.user_id,
            total_amount=order.total_amount,
            subtotal=order.subtotal,
            shipping_cost=order.shipping_cost,
            tax_amount=order.tax_amount,
            discount_amount=order.discount_amount,
            status=order.status,
            payment_status=order.payment_status,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            customer_phone=order.customer_phone,
            payment_method=order.payment_method,
            payment_id=order.payment_id,
            tracking_number=order.tracking_number,
            courier_service=order.courier_service,
            estimated_delivery_date=order.estimated_delivery_date,
            delivered_at=order.delivered_at,
            customer_notes=order.customer_notes,
            items=[
                OrderItemResponse(
                    id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    product_sku=item.product_sku,
                    quantity=item.quantity,
                    price_at_purchase=item.price_at_purchase,
                    subtotal=item.subtotal,
                    created_at=item.created_at
                )
                for item in order.items
            ],
            created_at=order.created_at,
            updated_at=order.updated_at
        )