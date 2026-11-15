"""Pydantic schemas (request / response contracts)."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import OrderStatus, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# ── auth ──────────────────────────────────────────────────────────────
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class UserOut(ORMModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ── catalog ───────────────────────────────────────────────────────────
class CategoryOut(ORMModel):
    id: int
    title: str
    slug: str


class ProductOut(ORMModel):
    id: int
    title: str
    slug: str
    description: str
    price: Decimal
    stock: int
    image_url: str
    is_active: bool
    category: CategoryOut | None = None


class ProductListOut(BaseModel):
    items: list[ProductOut]
    total: int
    page: int
    per_page: int


class ProductIn(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    description: str = ""
    price: Decimal = Field(gt=0)
    stock: int = Field(ge=0, default=0)
    image_url: str = ""
    is_active: bool = True
    category_id: int | None = None


class ProductPatch(BaseModel):
    title: str | None = None
    description: str | None = None
    price: Decimal | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = None
    is_active: bool | None = None
    category_id: int | None = None


# ── cart ──────────────────────────────────────────────────────────────
class CartItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, le=99, default=1)


class CartItemPatch(BaseModel):
    quantity: int = Field(ge=1, le=99)


class CartItemOut(ORMModel):
    id: int
    product_id: int
    quantity: int
    product: ProductOut


class CartOut(BaseModel):
    items: list[CartItemOut]
    total: Decimal
    count: int


# ── orders ────────────────────────────────────────────────────────────
class OrderIn(BaseModel):
    customer_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=5, max_length=32)
    address: str = Field(min_length=3, max_length=512)
    comment: str = ""


class OrderItemOut(ORMModel):
    id: int
    product_id: int | None
    title: str
    price: Decimal
    quantity: int


class OrderOut(ORMModel):
    id: int
    status: OrderStatus
    total: Decimal
    customer_name: str
    phone: str
    address: str
    comment: str
    created_at: datetime
    items: list[OrderItemOut]


class OrderStatusPatch(BaseModel):
    status: OrderStatus
