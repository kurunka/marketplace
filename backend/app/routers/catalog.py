"""Public catalog: categories and products with filtering + pagination."""

from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from app.deps import SessionDep
from app.models import Category, Product
from app.schemas import CategoryOut, ProductListOut, ProductOut

router = APIRouter(tags=["catalog"])


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(session: SessionDep) -> list[CategoryOut]:
    rows = await session.scalars(select(Category).order_by(Category.title))
    return [CategoryOut.model_validate(row) for row in rows]


@router.get("/products", response_model=ProductListOut)
async def list_products(
    session: SessionDep,
    q: str | None = Query(default=None, description="поиск по названию"),
    category: str | None = Query(default=None, description="slug категории"),
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    in_stock: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=12, ge=1, le=60),
) -> ProductListOut:
    stmt = (
        select(Product)
        .where(Product.is_active.is_(True))
        .options(selectinload(Product.category))
    )

    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(or_(Product.title.ilike(pattern), Product.description.ilike(pattern)))
    if category:
        stmt = stmt.join(Product.category).where(Category.slug == category)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    if in_stock:
        stmt = stmt.where(Product.stock > 0)

    total = await session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    rows = await session.scalars(
        stmt.order_by(Product.id.desc()).offset((page - 1) * per_page).limit(per_page)
    )
    return ProductListOut(
        items=[ProductOut.model_validate(row) for row in rows],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/products/{slug}", response_model=ProductOut)
async def get_product(slug: str, session: SessionDep) -> ProductOut:
    product = await session.scalar(
        select(Product)
        .where(Product.slug == slug, Product.is_active.is_(True))
        .options(selectinload(Product.category))
    )
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Товар не найден")
    return ProductOut.model_validate(product)
