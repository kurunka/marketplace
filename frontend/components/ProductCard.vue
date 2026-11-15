<script setup lang="ts">
import type { Product } from '~/types/api'

const props = defineProps<{ product: Product }>()

const cart = useCartStore()
const auth = useAuthStore()
const pending = ref(false)
const message = ref('')

const price = computed(() =>
  new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
    .format(Number(props.product.price)),
)

async function addToCart() {
  if (!auth.isAuthenticated) {
    await navigateTo('/login')
    return
  }
  pending.value = true
  message.value = ''
  try {
    await cart.add(props.product.id)
    message.value = 'Добавлено в корзину'
  } catch (e: any) {
    message.value = e?.data?.detail ?? 'Не удалось добавить'
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <article class="card">
    <NuxtLink :to="`/product/${product.slug}`" class="thumb">
      {{ product.category?.title ?? 'Товар' }}
    </NuxtLink>

    <div class="card-body">
      <NuxtLink :to="`/product/${product.slug}`">
        <strong>{{ product.title }}</strong>
      </NuxtLink>

      <p class="muted" style="margin: 0">{{ product.description }}</p>

      <div class="row-between" style="margin-top: auto">
        <span class="price">{{ price }}</span>
        <span v-if="product.stock > 0" class="tag">в наличии: {{ product.stock }}</span>
        <span v-else class="tag tag-cancelled">нет в наличии</span>
      </div>

      <button
        class="btn btn-primary btn-sm"
        :disabled="pending || product.stock === 0"
        @click="addToCart"
      >
        {{ product.stock === 0 ? 'Нет в наличии' : 'В корзину' }}
      </button>

      <p v-if="message" class="muted" style="margin: 0">{{ message }}</p>
    </div>
  </article>
</template>
