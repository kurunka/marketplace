<script setup lang="ts">
const auth = useAuthStore()
const cart = useCartStore()

// one place where session + cart are restored (works on SSR too)
if (!auth.user) await auth.fetchMe()
await cart.refresh()
</script>

<template>
  <div>
    <header class="site-header">
      <div class="container inner">
        <NuxtLink to="/" class="logo">Мини-маркетплейс</NuxtLink>

        <nav class="nav">
          <NuxtLink to="/">Каталог</NuxtLink>

          <NuxtLink to="/cart">
            Корзина
            <span v-if="cart.count" class="badge">{{ cart.count }}</span>
          </NuxtLink>

          <template v-if="auth.isAuthenticated">
            <NuxtLink to="/orders">Заказы</NuxtLink>
            <NuxtLink v-if="auth.isAdmin" to="/admin">Админка</NuxtLink>
            <button class="btn btn-sm btn-ghost" @click="auth.logout()">Выйти</button>
          </template>
          <NuxtLink v-else to="/login" class="btn btn-sm">Войти</NuxtLink>
        </nav>
      </div>
    </header>

    <main>
      <slot />
    </main>

    <footer class="container mt-32" style="padding-bottom: 32px">
      <p class="muted">
        Nuxt 3 + FastAPI + PostgreSQL. Демо-проект: каталог, корзина, заказы, админка.
      </p>
    </footer>
  </div>
</template>
