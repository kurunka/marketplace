<script setup lang="ts">
import type { AdminStats, Order, OrderStatus, Product } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const api = useApi()
const auth = useAuthStore()

// role check on the client; the API enforces it anyway (403)
if (auth.user && !auth.isAdmin) {
  await navigateTo('/')
}

const { data: stats, refresh: refreshStats } = await useAsyncData('admin-stats', () =>
  api<AdminStats>('/admin/stats'),
)
const { data: orders, refresh: refreshOrders } = await useAsyncData('admin-orders', () =>
  api<Order[]>('/admin/orders'),
)
const { data: products, refresh: refreshProducts } = await useAsyncData('admin-products', () =>
  api<Product[]>('/admin/products'),
)

const error = ref('')
const STATUS_LABELS: Record<OrderStatus, string> = {
  pending: 'Ожидает',
  paid: 'Оплачен',
  shipped: 'Отправлен',
  done: 'Завершён',
  cancelled: 'Отменён',
}
const NEXT_STATUSES: Record<OrderStatus, OrderStatus[]> = {
  pending: ['paid', 'cancelled'],
  paid: ['shipped', 'cancelled'],
  shipped: ['done'],
  done: [],
  cancelled: [],
}

const fmt = (value: string) =>
  new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
    .format(Number(value))

async function setStatus(order: Order, status: OrderStatus) {
  error.value = ''
  try {
    await api(`/admin/orders/${order.id}`, { method: 'PATCH', body: { status } })
    await Promise.all([refreshOrders(), refreshStats()])
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Не удалось изменить статус'
  }
}

async function updateStock(product: Product, stock: number) {
  error.value = ''
  try {
    await api(`/admin/products/${product.id}`, { method: 'PATCH', body: { stock } })
    await Promise.all([refreshProducts(), refreshStats()])
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Не удалось обновить остаток'
  }
}

async function toggleActive(product: Product) {
  error.value = ''
  try {
    await api(`/admin/products/${product.id}`, {
      method: 'PATCH',
      body: { is_active: !product.is_active },
    })
    await refreshProducts()
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Не удалось изменить товар'
  }
}
</script>

<template>
  <div class="container mt-24">
    <h1>Админка</h1>
    <p class="muted">Заказы, статусы и остатки. Данные приходят из FastAPI, права проверяются на сервере.</p>

    <p v-if="error" class="error mt-24">{{ error }}</p>

    <div class="stats mt-24">
      <div class="stat">
        <div class="value">{{ stats?.orders_count ?? 0 }}</div>
        <div class="label">Всего заказов</div>
      </div>
      <div class="stat">
        <div class="value">{{ stats?.pending_orders ?? 0 }}</div>
        <div class="label">Ждут обработки</div>
      </div>
      <div class="stat">
        <div class="value">{{ fmt(stats?.revenue ?? '0') }}</div>
        <div class="label">Выручка (оплаченные)</div>
      </div>
      <div class="stat">
        <div class="value">{{ stats?.products_count ?? 0 }}</div>
        <div class="label">Товаров</div>
      </div>
      <div class="stat">
        <div class="value">{{ stats?.out_of_stock ?? 0 }}</div>
        <div class="label">Нет в наличии</div>
      </div>
    </div>

    <h2 class="mt-32">Заказы</h2>

    <div v-if="!orders?.length" class="empty mt-24">Заказов нет.</div>

    <div v-else class="card mt-24" style="padding: 8px 16px">
      <table class="table">
        <thead>
          <tr>
            <th style="width: 70px">№</th>
            <th>Клиент</th>
            <th>Состав</th>
            <th style="width: 110px">Сумма</th>
            <th style="width: 130px">Статус</th>
            <th style="width: 170px">Действие</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="order in orders" :key="order.id">
            <td>{{ order.id }}</td>
            <td>
              <div>{{ order.customer_name }}</div>
              <div class="muted">{{ order.phone }}</div>
            </td>
            <td class="muted">
              <div v-for="item in order.items" :key="item.id">{{ item.title }} × {{ item.quantity }}</div>
            </td>
            <td class="price">{{ fmt(order.total) }}</td>
            <td><span class="tag" :class="`tag-${order.status}`">{{ STATUS_LABELS[order.status] }}</span></td>
            <td>
              <select
                v-if="NEXT_STATUSES[order.status].length"
                :value="''"
                @change="setStatus(order, ($event.target as HTMLSelectElement).value as OrderStatus)"
              >
                <option value="" disabled>Перевести в…</option>
                <option v-for="next in NEXT_STATUSES[order.status]" :key="next" :value="next">
                  {{ STATUS_LABELS[next] }}
                </option>
              </select>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <h2 class="mt-32">Товары</h2>

    <div class="card mt-24" style="padding: 8px 16px">
      <table class="table">
        <thead>
          <tr>
            <th>Название</th>
            <th style="width: 120px">Цена</th>
            <th style="width: 150px">Остаток</th>
            <th style="width: 120px">Витрина</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products ?? []" :key="product.id">
            <td>
              <div>{{ product.title }}</div>
              <div class="muted">{{ product.slug }}</div>
            </td>
            <td>{{ fmt(product.price) }}</td>
            <td>
              <input
                type="number"
                min="0"
                :value="product.stock"
                style="width: 90px"
                @change="updateStock(product, Number(($event.target as HTMLInputElement).value))"
              />
            </td>
            <td>
              <button class="btn btn-sm" @click="toggleActive(product)">
                {{ product.is_active ? 'Скрыть' : 'Показать' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
