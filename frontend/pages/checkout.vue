<script setup lang="ts">
import type { Order } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const api = useApi()
const cart = useCartStore()
const auth = useAuthStore()

await cart.refresh()

const form = reactive({
  customer_name: auth.user?.full_name ?? '',
  phone: '',
  address: '',
  comment: '',
})

const pending = ref(false)
const error = ref('')

const fmt = (value: string) =>
  new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
    .format(Number(value))

async function submit() {
  error.value = ''
  pending.value = true
  try {
    const order = await api<Order>('/orders', { method: 'POST', body: { ...form } })
    await cart.refresh()
    await navigateTo(`/orders?created=${order.id}`)
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Не удалось оформить заказ'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="container mt-24">
    <h1>Оформление заказа</h1>

    <div v-if="!cart.items.length" class="empty mt-24">
      Корзина пуста — оформлять нечего.
      <NuxtLink to="/" class="btn btn-sm" style="margin-left: 8px">В каталог</NuxtLink>
    </div>

    <div v-else style="display: grid; grid-template-columns: 1.2fr 1fr; gap: 24px" class="mt-24">
      <form class="card" style="padding: 20px" @submit.prevent="submit">
        <p v-if="error" class="error">{{ error }}</p>

        <div class="field">
          <label>Имя и фамилия</label>
          <input v-model="form.customer_name" required maxlength="255" />
        </div>
        <div class="field">
          <label>Телефон</label>
          <input v-model="form.phone" required placeholder="+7 999 000-00-00" maxlength="32" />
        </div>
        <div class="field">
          <label>Адрес доставки</label>
          <textarea v-model="form.address" required rows="3" maxlength="512" />
        </div>
        <div class="field">
          <label>Комментарий (необязательно)</label>
          <textarea v-model="form.comment" rows="2" />
        </div>

        <button class="btn btn-primary" type="submit" :disabled="pending">
          {{ pending ? 'Оформляем…' : 'Подтвердить заказ' }}
        </button>
      </form>

      <aside class="card" style="padding: 20px; height: fit-content">
        <h2>Ваш заказ</h2>
        <div class="stack" style="margin-top: 12px">
          <div v-for="item in cart.items" :key="item.id" class="row-between">
            <span class="muted">{{ item.product.title }} × {{ item.quantity }}</span>
            <span>{{ fmt(String(Number(item.product.price) * item.quantity)) }}</span>
          </div>
          <hr style="border: none; border-top: 1px solid var(--border); width: 100%" />
          <div class="row-between">
            <strong>Итого</strong>
            <strong class="price">{{ fmt(cart.total) }}</strong>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>
