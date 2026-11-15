export interface Category {
  id: number
  title: string
  slug: string
}

export interface Product {
  id: number
  title: string
  slug: string
  description: string
  price: string
  stock: number
  image_url: string
  is_active: boolean
  category: Category | null
}

export interface ProductList {
  items: Product[]
  total: number
  page: number
  per_page: number
}

export interface CartItem {
  id: number
  product_id: number
  quantity: number
  product: Product
}

export interface Cart {
  items: CartItem[]
  total: string
  count: number
}

export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'done' | 'cancelled'

export interface OrderItem {
  id: number
  product_id: number | null
  title: string
  price: string
  quantity: number
}

export interface Order {
  id: number
  status: OrderStatus
  total: string
  customer_name: string
  phone: string
  address: string
  comment: string
  created_at: string
  items: OrderItem[]
}

export interface User {
  id: number
  email: string
  full_name: string
  role: 'customer' | 'admin'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

export interface AdminStats {
  orders_count: number
  revenue: string
  pending_orders: number
  products_count: number
  out_of_stock: number
}
