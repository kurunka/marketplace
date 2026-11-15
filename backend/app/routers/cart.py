"""Cart for the authenticated user. Server-side, so it survives device changes."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.deps import CurrentUser, SessionDep
from app.models import CartItem, Product
from app.schemas import CartItemIn, CartItemOut, CartItemPatch, CartOut

router = APIRouter(prefix="/cart", tags=["cart"])


async def _cart_payload(session: SessionDep, user_id: int) -> CartOut:
    rows = await session.scalars(
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product).selectinload(Product.category))
        .order_by(CartItem.id)
    )
    items = list(rows)
    total = sum((item.product.price * item.quantity for item in items), Decimal("0"))
    return CartOut(
        items=[CartItemOut.model_validate(item) for item in items],
        total=total,
        count=sum(item.quantity for item in items),
    )


@router.get("", response_model=CartOut)
async def get_cart(user: CurrentUser, session: SessionDep) -> CartOut:
    return await _cart_payload(session, user.id)


@router.post("", response_model=CartOut, status_code=status.HTTP_201_CREATED)
async def add_to_cart(payload: CartItemIn, user: CurrentUser, session: SessionDep) -> CartOut:
    product = await session.get(Product, payload.product_id)
    if product is None or not product.is_active:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")

    existing = await session.scalar(
        select(CartItem).where(
            CartItem.user_id == user.id, CartItem.product_id == payload.product_id
        )
    )
    wanted = payload.quantity + (existing.quantity if existing else 0)
    if wanted > product.stock:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"На складе только {product.stock} шт.",
        )

    if existing:
        existing.quantity = wanted
    else:
        session.add(CartItem(user_id=user.id, product_id=payload.product_id, quantity=wanted))

    await session.commit()
    return await _cart_payload(session, user.id)


@router.patch("/{item_id}", response_model=CartOut)
async def update_item(
    item_id: int, payload: CartItemPatch, user: CurrentUser, session: SessionDep
) -> CartOut:
    item = await session.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Позиция не найдена")

    product = await session.get(Product, item.product_id)
    if product is not None and payload.quantity > product.stock:
        raise HTTPException(status.HTTP_409_CONFLICT, f"На складе только {product.stock} шт.")

    item.quantity = payload.quantity
    await session.commit()
    return await _cart_payload(session, user.id)


@router.delete("/{item_id}", response_model=CartOut)
async def remove_item(item_id: int, user: CurrentUser, session: SessionDep) -> CartOut:
    await session.execute(
        delete(CartItem).where(CartItem.id == item_id, CartItem.user_id == user.id)
    )
    await session.commit()
    return await _cart_payload(session, user.id)


@router.delete("", response_model=CartOut)
async def clear_cart(user: CurrentUser, session: SessionDep) -> CartOut:
    await session.execute(delete(CartItem).where(CartItem.user_id == user.id))
    await session.commit()
    return await _cart_payload(session, user.id)
