"""Admin area: product CRUD, order list, status transitions, simple stats."""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.deps import AdminUser, SessionDep
from app.models import Order, OrderStatus, Product
from app.schemas import OrderOut, OrderStatusPatch, ProductIn, ProductOut, ProductPatch

router = APIRouter(prefix="/admin", tags=["admin"])

# allowed status moves — keeps the order lifecycle sane
TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.pending: {OrderStatus.paid, OrderStatus.cancelled},
    OrderStatus.paid: {OrderStatus.shipped, OrderStatus.cancelled},
    OrderStatus.shipped: {OrderStatus.done},
    OrderStatus.done: set(),
    OrderStatus.cancelled: set(),
}


@router.get("/stats")
async def stats(admin: AdminUser, session: SessionDep) -> dict:
    orders_count = await session.scalar(select(func.count()).select_from(Order)) or 0
    revenue = await session.scalar(
        select(func.coalesce(func.sum(Order.total), 0)).where(
            Order.status.in_([OrderStatus.paid, OrderStatus.shipped, OrderStatus.done])
        )
    )
    pending = await session.scalar(
        select(func.count()).select_from(Order).where(Order.status == OrderStatus.pending)
    )
    products_count = await session.scalar(select(func.count()).select_from(Product)) or 0
    out_of_stock = await session.scalar(
        select(func.count()).select_from(Product).where(Product.stock == 0)
    )
    return {
        "orders_count": orders_count,
        "revenue": str(revenue or 0),
        "pending_orders": pending or 0,
        "products_count": products_count,
        "out_of_stock": out_of_stock or 0,
    }


# ── products ──────────────────────────────────────────────────────────
@router.get("/products", response_model=list[ProductOut])
async def admin_products(
    admin: AdminUser, session: SessionDep, limit: int = Query(default=100, le=500)
) -> list[ProductOut]:
    rows = await session.scalars(
        select(Product)
        .options(selectinload(Product.category))
        .order_by(Product.id.desc())
        .limit(limit)
    )
    return [ProductOut.model_validate(row) for row in rows]


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductIn, admin: AdminUser, session: SessionDep) -> ProductOut:
    clash = await session.scalar(select(Product.id).where(Product.slug == payload.slug))
    if clash:
        raise HTTPException(status.HTTP_409_CONFLICT, "Такой slug уже занят")

    product = Product(**payload.model_dump())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return ProductOut.model_validate(product)


@router.patch("/products/{product_id}", response_model=ProductOut)
async def update_product(
    product_id: int, payload: ProductPatch, admin: AdminUser, session: SessionDep
) -> ProductOut:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, field, value)

    await session.commit()
    await session.refresh(product)
    return ProductOut.model_validate(product)


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, admin: AdminUser, session: SessionDep) -> None:
    product = await session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    # soft delete: order history must keep pointing at something
    product.is_active = False
    await session.commit()


# ── orders ────────────────────────────────────────────────────────────
@router.get("/orders", response_model=list[OrderOut])
async def admin_orders(
    admin: AdminUser,
    session: SessionDep,
    order_status: OrderStatus | None = Query(default=None, alias="status"),
) -> list[OrderOut]:
    stmt = select(Order).options(selectinload(Order.items)).order_by(Order.id.desc())
    if order_status is not None:
        stmt = stmt.where(Order.status == order_status)
    rows = await session.scalars(stmt)
    return [OrderOut.model_validate(row) for row in rows]


@router.patch("/orders/{order_id}", response_model=OrderOut)
async def change_order_status(
    order_id: int, payload: OrderStatusPatch, admin: AdminUser, session: SessionDep
) -> OrderOut:
    order = await session.scalar(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Заказ не найден")

    if payload.status not in TRANSITIONS[order.status]:
        allowed = ", ".join(sorted(s.value for s in TRANSITIONS[order.status])) or "нет"
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Из «{order.status.value}» нельзя перейти в «{payload.status.value}». Доступно: {allowed}",
        )

    order.status = payload.status
    await session.commit()
    return OrderOut.model_validate(order)
