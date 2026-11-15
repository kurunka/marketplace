"""Idempotent demo data: admin user, categories, products."""

import asyncio
from decimal import Decimal

from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import Category, Product, User, UserRole
from app.security import hash_password

CATEGORIES = [
    ("Электроника", "electronics"),
    ("Дом и сад", "home"),
    ("Одежда", "clothes"),
]

PRODUCTS = [
    ("Наушники Aurora X1", "aurora-x1", "electronics", "12990", 12, "Беспроводные, ANC, 40 ч работы."),
    ("Клавиатура Mech 68", "mech-68", "electronics", "7490", 8, "Механика, hot-swap, Bluetooth + USB-C."),
    ("Лампа Warm Desk", "warm-desk", "home", "3290", 20, "Тёплый свет 3000K, регулировка яркости."),
    ("Термокружка 500 мл", "thermo-500", "home", "1890", 35, "Держит тепло 12 часов."),
    ("Худи Oversize Graphite", "hoodie-graphite", "clothes", "5990", 15, "Плотный футер 340 г/м², унисекс."),
    ("Кепка Canvas", "cap-canvas", "clothes", "1590", 0, "Хлопок, регулируемый ремешок."),
]


async def seed() -> None:
    async with SessionLocal() as session:
        admin = await session.scalar(select(User).where(User.email == settings.admin_email.lower()))
        if admin is None:
            session.add(
                User(
                    email=settings.admin_email.lower(),
                    hashed_password=hash_password(settings.admin_password),
                    full_name="Администратор",
                    role=UserRole.admin,
                )
            )

        cats: dict[str, Category] = {}
        for title, slug in CATEGORIES:
            cat = await session.scalar(select(Category).where(Category.slug == slug))
            if cat is None:
                cat = Category(title=title, slug=slug)
                session.add(cat)
            cats[slug] = cat
        await session.flush()

        for title, slug, cat_slug, price, stock, descr in PRODUCTS:
            exists = await session.scalar(select(Product.id).where(Product.slug == slug))
            if exists:
                continue
            session.add(
                Product(
                    title=title,
                    slug=slug,
                    description=descr,
                    price=Decimal(price),
                    stock=stock,
                    category_id=cats[cat_slug].id,
                    image_url=f"/img/{slug}.jpg",
                )
            )

        await session.commit()
        print("seed: done")


if __name__ == "__main__":
    asyncio.run(seed())
