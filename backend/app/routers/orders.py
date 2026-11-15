"""Checkout: turns the cart into an order and reserves stock atomically."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, SessionDep
from app.models import CartItem, Order, OrderItem, OrderStatus, Product
from app.schemas import OrderIn, OrderOut

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(payload: OrderIn, user: CurrentUser, session: SessionDep) -> OrderOut:
    cart = list(
        await session.scalars(
            select(CartItem).where(CartItem.user_id == user.id).order_by(CartItem.id)
        )
    )
    if not cart:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Корзина пуста")

    order = Order(
        user_id=user.id,
        status=OrderStatus.pending,
        customer_name=payload.customer_name,
        phone=payload.phone,
        address=payload.address,
        comment=payload.comment,
        total=Decimal("0"),
    )
    session.add(order)
    await session.flush()

    total = Decimal("0")
    for item in cart:
        # row lock: two parallel checkouts must not oversell the last unit
        product = await session.scalar(
            select(Product).where(Product.id == item.product_id).with_for_update()
        )
        if product is None or not product.is_active:
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Один из товаров больше недоступен — обновите корзину"
            )
        if product.stock < item.quantity:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"«{product.title}»: на складе осталось {product.stock} шт.",
            )

        product.stock -= item.quantity
        total += product.price * item.quantity
        session.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                title=product.title,
                price=product.price,
                quantity=item.quantity,
            )
        )

    order.total = total
    await session.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await session.commit()

    created = await session.scalar(
        select(Order).where(Order.id == order.id).options(selectinload(Order.items))
    )
    return OrderOut.model_validate(created)


@router.get("", response_model=list[OrderOut])
async def my_orders(user: CurrentUser, session: SessionDep) -> list[OrderOut]:
    rows = await session.scalars(
        select(Order)
        .where(Order.user_id == user.id)
        .options(selectinload(Order.items))
        .order_by(Order.id.desc())
    )
    return [OrderOut.model_validate(row) for row in rows]


@router.get("/{order_id}", response_model=OrderOut)
async def my_order(order_id: int, user: CurrentUser, session: SessionDep) -> OrderOut:
    order = await session.scalar(
        select(Order)
        .where(Order.id == order_id, Order.user_id == user.id)
        .options(selectinload(Order.items))
    )
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заказ не найден")
    return OrderOut.model_validate(order)
