<script setup lang="ts">
const auth = useAuthStore()
const route = useRoute()
const cart = useCartStore()

const mode = ref<'login' | 'register'>('login')
const email = ref('')
const password = ref('')
const fullName = ref('')
const pending = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  pending.value = true
  try {
    if (mode.value === 'login') {
      await auth.login(email.value, password.value)
    } else {
      await auth.register(email.value, password.value, fullName.value)
    }
    await cart.refresh()
    const next = typeof route.query.next === 'string' ? route.query.next : '/'
    await navigateTo(next)
  } catch (e: any) {
    const detail = e?.data?.detail
    error.value = Array.isArray(detail)
      ? detail.map((d: any) => d.msg).join('; ')
      : (detail ?? 'Не удалось войти')
  } finally {
    pending.value = false
  }
}
</script>

<template>
  <div class="container mt-24" style="max-width: 420px">
    <h1>{{ mode === 'login' ? 'Вход' : 'Регистрация' }}</h1>
    <p class="muted">Корзина и заказы привязаны к аккаунту.</p>

    <form class="card mt-24" style="padding: 20px" @submit.prevent="submit">
      <p v-if="error" class="error">{{ error }}</p>

      <div v-if="mode === 'register'" class="field">
        <label>Имя</label>
        <input v-model="fullName" maxlength="255" />
      </div>

      <div class="field">
        <label>Email</label>
        <input v-model="email" type="email" required autocomplete="email" />
      </div>

      <div class="field">
        <label>Пароль</label>
        <input
          v-model="password"
          type="password"
          required
          :minlength="mode === 'register' ? 8 : 1"
          autocomplete="current-password"
        />
        <p v-if="mode === 'register'" class="muted" style="margin: 6px 0 0">Минимум 8 символов</p>
      </div>

      <button class="btn btn-primary" type="submit" :disabled="pending" style="width: 100%">
        {{ pending ? 'Подождите…' : mode === 'login' ? 'Войти' : 'Создать аккаунт' }}
      </button>

      <p class="muted" style="margin: 14px 0 0; text-align: center">
        <template v-if="mode === 'login'">
          Нет аккаунта?
          <a href="#" @click.prevent="mode = 'register'">Зарегистрироваться</a>
        </template>
        <template v-else>
          Уже есть аккаунт?
          <a href="#" @click.prevent="mode = 'login'">Войти</a>
        </template>
      </p>
    </form>

    <p class="muted mt-24">
      Демо-админ: <code>admin@example.com</code> / <code>admin12345</code>
    </p>
  </div>
</template>
