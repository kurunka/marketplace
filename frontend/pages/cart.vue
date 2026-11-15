<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

const cart = useCartStore()
const error = ref('')

await cart.refresh()

const fmt = (value: string) =>
  new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
    .format(Number(value))

async function change(itemId: number, quantity: number) {
  error.value = ''
  if (quantity < 1) return
  try {
    await cart.setQuantity(itemId, quantity)
  } catch (e: any) {
    error.value = e?.data?.detail ?? 'Не удалось изменить количество'
    await cart.refresh()
  }
}

async function remove(itemId: number) {
  error.value = ''
  try {
    await cart.remove(itemId)
  } catch {
    error.value = 'Не удалось удалить позицию'
  }
}
</script>

<template>
  <div class="container mt-24">
    <h1>Корзина</h1>

    <p v-if="error" class="error mt-24">{{ error }}</p>

    <div v-if="!cart.items.length" class="empty mt-24">
      Корзина пуста.
      <NuxtLink to="/" class="btn btn-sm mt-24" style="margin-left: 8px">В каталог</NuxtLink>
    </div>

    <template v-else>
      <div class="card mt-24" style="padding: 8px 16px">
        <table class="table">
          <thead>
            <tr>
              <th>Товар</th>
              <th style="width: 140px">Кол-во</th>
              <th style="width: 130px">Сумма</th>
              <th style="width: 60px"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in cart.items" :key="item.id">
              <td>
                <NuxtLink :to="`/product/${item.product.slug}`">
                  <strong>{{ item.product.title }}</strong>
                </NuxtLink>
                <div class="muted">{{ fmt(item.product.price) }} / шт.</div>
              </td>
              <td>
                <div class="row">
                  <button class="btn btn-sm" @click="change(item.id, item.quantity - 1)">−</button>
                  <span>{{ item.quantity }}</span>
                  <button
                    class="btn btn-sm"
                    :disabled="item.quantity >= item.product.stock"
                    @click="change(item.id, item.quantity + 1)"
                  >
                    +
                  </button>
                </div>
              </td>
              <td class="price">{{ fmt(String(Number(item.product.price) * item.quantity)) }}</td>
              <td>
                <button class="btn btn-sm btn-ghost" @click="remove(item.id)">✕</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="row-between mt-24">
        <button class="btn btn-ghost btn-sm" @click="cart.clear()">Очистить корзину</button>
        <div class="row">
          <span class="muted">Итого:</span>
          <span class="price" style="font-size: 22px">{{ fmt(cart.total) }}</span>
          <NuxtLink to="/checkout" class="btn btn-primary">Оформить заказ</NuxtLink>
        </div>
      </div>
    </template>
  </div>
</template>
