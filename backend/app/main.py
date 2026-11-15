"""FastAPI entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import admin, auth, cart, catalog, orders

app = FastAPI(
    title="Mini Marketplace API",
    version="1.0.0",
    description="Каталог, корзина, заказы и админка. FastAPI + PostgreSQL.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(catalog.router, prefix="/api")
app.include_router(cart.router, prefix="/api")
app.include_router(orders.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/api/health", tags=["service"])
async def health() -> dict:
    return {"status": "ok"}
