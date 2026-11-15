"""End-to-end API tests on SQLite (no Postgres needed to run the suite)."""

import os
from decimal import Decimal

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.sqlite3"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["ADMIN_EMAIL"] = "admin@example.com"
os.environ["ADMIN_PASSWORD"] = "admin12345"

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402

from app.db import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Product, User, UserRole  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    await engine.dispose()


async def _make_admin() -> None:
    from app.db import SessionLocal

    async with SessionLocal() as session:
        session.add(
            User(
                email="admin@example.com",
                hashed_password=hash_password("admin12345"),
                role=UserRole.admin,
            )
        )
        await session.commit()


async def _make_product(stock: int = 5, price: str = "1000") -> int:
    from app.db import SessionLocal

    async with SessionLocal() as session:
        product = Product(
            title="Тестовый товар",
            slug="test-product",
            description="",
            price=Decimal(price),
            stock=stock,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product.id


async def _register(client: AsyncClient) -> str:
    r = await client.post(
        "/api/auth/register",
        json={"email": "buyer@example.com", "password": "password123", "full_name": "Тест"},
    )
    assert r.status_code == 201, r.text
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.anyio
async def test_health(client: AsyncClient) -> None:
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_register_login_me(client: AsyncClient) -> None:
    token = await _register(client)
    r = await client.get("/api/auth/me", headers=_auth(token))
    assert r.status_code == 200
    assert r.json()["email"] == "buyer@example.com"

    r = await client.post(
        "/api/auth/login", json={"email": "buyer@example.com", "password": "password123"}
    )
    assert r.status_code == 200

    r = await client.post(
        "/api/auth/login", json={"email": "buyer@example.com", "password": "wrong-pass"}
    )
    assert r.status_code == 401


@pytest.mark.anyio
async def test_catalog_filtering(client: AsyncClient) -> None:
    await _make_product(stock=3)
    r = await client.get("/api/products", params={"q": "Тестовый"})
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = await client.get("/api/products", params={"in_stock": True})
    assert r.json()["total"] == 1

    r = await client.get("/api/products/test-product")
    assert r.status_code == 200
    assert r.json()["slug"] == "test-product"


@pytest.mark.anyio
async def test_cart_respects_stock(client: AsyncClient) -> None:
    token = await _register(client)
    product_id = await _make_product(stock=2)

    r = await client.post(
        "/api/cart", json={"product_id": product_id, "quantity": 2}, headers=_auth(token)
    )
    assert r.status_code == 201
    assert r.json()["count"] == 2
    assert Decimal(str(r.json()["total"])) == Decimal("2000")

    # adding one more must fail — only 2 in stock
    r = await client.post(
        "/api/cart", json={"product_id": product_id, "quantity": 1}, headers=_auth(token)
    )
    assert r.status_code == 409


@pytest.mark.anyio
async def test_checkout_decrements_stock_and_clears_cart(client: AsyncClient) -> None:
    token = await _register(client)
    product_id = await _make_product(stock=5)

    await client.post(
        "/api/cart", json={"product_id": product_id, "quantity": 2}, headers=_auth(token)
    )
    r = await client.post(
        "/api/orders",
        json={
            "customer_name": "Иван",
            "phone": "+79990000000",
            "address": "Москва, ул. Тестовая 1",
        },
        headers=_auth(token),
    )
    assert r.status_code == 201, r.text
    order = r.json()
    assert Decimal(str(order["total"])) == Decimal("2000")
    assert order["status"] == "pending"
    assert len(order["items"]) == 1

    r = await client.get("/api/cart", headers=_auth(token))
    assert r.json()["count"] == 0

    r = await client.get("/api/products/test-product")
    assert r.json()["stock"] == 3


@pytest.mark.anyio
async def test_checkout_empty_cart_rejected(client: AsyncClient) -> None:
    token = await _register(client)
    r = await client.post(
        "/api/orders",
        json={"customer_name": "Иван", "phone": "+79990000000", "address": "Москва"},
        headers=_auth(token),
    )
    assert r.status_code == 400


@pytest.mark.anyio
async def test_admin_guard_and_status_transitions(client: AsyncClient) -> None:
    await _make_admin()
    buyer_token = await _register(client)
    product_id = await _make_product(stock=5)

    # customer must not reach admin endpoints
    r = await client.get("/api/admin/orders", headers=_auth(buyer_token))
    assert r.status_code == 403

    r = await client.post(
        "/api/auth/login", json={"email": "admin@example.com", "password": "admin12345"}
    )
    admin_token = r.json()["access_token"]

    await client.post(
        "/api/cart", json={"product_id": product_id, "quantity": 1}, headers=_auth(buyer_token)
    )
    order = (
        await client.post(
            "/api/orders",
            json={"customer_name": "Иван", "phone": "+79990000000", "address": "Москва"},
            headers=_auth(buyer_token),
        )
    ).json()

    # pending -> shipped is not allowed
    r = await client.patch(
        f"/api/admin/orders/{order['id']}", json={"status": "shipped"}, headers=_auth(admin_token)
    )
    assert r.status_code == 409

    r = await client.patch(
        f"/api/admin/orders/{order['id']}", json={"status": "paid"}, headers=_auth(admin_token)
    )
    assert r.status_code == 200
    assert r.json()["status"] == "paid"

    r = await client.get("/api/admin/stats", headers=_auth(admin_token))
    assert r.status_code == 200
    assert Decimal(str(r.json()["revenue"])) == Decimal("1000")
