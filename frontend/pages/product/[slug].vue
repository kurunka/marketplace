<script setup lang="ts">
import type { Product } from '~/types/api'

const api = useApi()
const route = useRoute()
const cart = useCartStore()
const auth = useAuthStore()

const slug = computed(() => String(route.params.slug))
const quantity = ref(1)
const pending = ref(false)
const message = ref('')

const { data: product, error } = await useAsyncData(`product-${slug.value}`, () =>
  api<Product>(`/products/${slug.value}`),
)

if (!product.value) {
  throw createError({ statusCode: 404, statusMessage: 'Товар не найден' })
}

const price = computed(() =>
  new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
    .format(Number(product.value!.price)),
)

useSeoMeta({
  title: () => `${product.value?.title} — Мини-маркетплейс`,
  description: () => product.value?.description ?? '',
  ogTitle: () => product.value?.title,
  ogDescription: () => product.value?.description,
})

async function addToCart() {
  if (!auth.isAuthenticated) {
    await navigateTo('/login')
    return
  }
  pending.value = true
  message.value = ''
  try {
    await cart.add(product.value!.id, quantity.value)
    message.value = 'Товар в корзине'
  } catch (e: any) {
    message.value = e?.data?.detail ?? 'Ошибка'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="container mt-24">
    <p v-if="error" class="error">Не удалось загрузить товар</p>

    <div v-if="product" class="card" style="padding: 24px; gap: 24px; display: grid; grid-template-columns: 1fr 1fr">
      <div class="thumb" style="border-radius: 10px; aspect-ratio: 1">
        {{ product.category?.title ?? 'Товар' }}
      </div>

      <div class="stack">
        <NuxtLink to="/" class="muted">← в каталог</NuxtLink>

        <h1 style="margin: 0">{{ product.title }}</h1>
        <p class="muted" style="margin: 0">{{ product.description }}</p>

        <div class="price" style="font-size: 28px">{{ price }}</div>

        <p v-if="product.stock > 0" class="muted" style="margin: 0">
          В наличии: {{ product.stock }} шт.
        </p>
        <p v-else class="muted" style="margin: 0; color: var(--danger)">Нет в наличии</p>

        <div class="row">
          <input
            v-model.number="quantity"
            type="number"
            min="1"
            :max="product.stock"
            style="width: 90px"
          />
          <button class="btn btn-primary" :disabled="pending || product.stock === 0" @click="addToCart">
            Добавить в корзину
          </button>
        </div>

        <p v-if="message" class="muted" style="margin: 0">{{ message }}</p>
      </div>
    </div>
  </div>
</template>
