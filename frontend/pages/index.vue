<script setup lang="ts">
import type { Category, ProductList } from '~/types/api'

const api = useApi()

const search = ref('')
const category = ref('')
const inStock = ref(false)
const page = ref(1)

// SSR: catalog is rendered on the server, so it is indexable and fast
const { data: categories } = await useAsyncData('categories', () =>
  api<Category[]>('/categories'),
)

const { data: catalog, pending } = await useAsyncData(
  'catalog',
  () =>
    api<ProductList>('/products', {
      query: {
        q: search.value || undefined,
        category: category.value || undefined,
        in_stock: inStock.value || undefined,
        page: page.value,
      },
    }),
  { watch: [search, category, inStock, page] },
)

const totalPages = computed(() =>
  catalog.value ? Math.max(1, Math.ceil(catalog.value.total / catalog.value.per_page)) : 1,
)

useSeoMeta({
  title: 'Каталог — Мини-маркетплейс',
  description: 'Витрина с фильтрами, корзиной и оформлением заказа.',
})
</script>

<template>
  <div>
    <section class="hero">
      <div class="container">
        <h1>Каталог</h1>
        <p>
          Витрина на Nuxt 3 с серверным рендерингом, серверной корзиной и оформлением заказа.
          Админка — по ссылке в шапке после входа под администратором.
        </p>
      </div>
    </section>

    <div class="container">
      <div class="filters">
        <input v-model="search" type="search" placeholder="Поиск по названию…" />
        <select v-model="category">
          <option value="">Все категории</option>
          <option v-for="c in categories ?? []" :key="c.id" :value="c.slug">{{ c.title }}</option>
        </select>
        <label class="row" style="margin: 0">
          <input v-model="inStock" type="checkbox" style="width: auto" />
          <span class="muted">Только в наличии</span>
        </label>
      </div>

      <div v-if="pending" class="empty">Загружаем товары…</div>

      <div v-else-if="!catalog?.items.length" class="empty">
        Ничего не нашлось. Попробуйте изменить фильтры.
      </div>

      <div v-else class="grid">
        <ProductCard v-for="product in catalog.items" :key="product.id" :product="product" />
      </div>

      <div v-if="totalPages > 1" class="row mt-24" style="justify-content: center">
        <button class="btn btn-sm" :disabled="page <= 1" @click="page--">Назад</button>
        <span class="muted">{{ page }} / {{ totalPages }}</span>
        <button class="btn btn-sm" :disabled="page >= totalPages" @click="page++">Вперёд</button>
      </div>
    </div>
  </div>
</template>
