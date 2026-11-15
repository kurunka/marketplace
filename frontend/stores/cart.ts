import type { Cart, CartItem } from '~/types/api'

export const useCartStore = defineStore('cart', () => {
  const api = useApi()
  const auth = useAuthStore()

  const items = ref<CartItem[]>([])
  const total = ref('0')
  const count = ref(0)
  const loading = ref(false)

  function apply(data: Cart) {
    items.value = data.items
    total.value = data.total
    count.value = data.count
  }

  async function refresh() {
    if (!auth.isAuthenticated) {
      apply({ items: [], total: '0', count: 0 })
      return
    }
    loading.value = true
    try {
      apply(await api<Cart>('/cart'))
    } finally {
      loading.value = false
    }
  }

  async function add(productId: number, quantity = 1) {
    apply(await api<Cart>('/cart', { method: 'POST', body: { product_id: productId, quantity } }))
  }

  async function setQuantity(itemId: number, quantity: number) {
    apply(await api<Cart>(`/cart/${itemId}`, { method: 'PATCH', body: { quantity } }))
  }

  async function remove(itemId: number) {
    apply(await api<Cart>(`/cart/${itemId}`, { method: 'DELETE' }))
  }

  async function clear() {
    apply(await api<Cart>('/cart', { method: 'DELETE' }))
  }

  return { items, total, count, loading, refresh, add, setQuantity, remove, clear }
})
