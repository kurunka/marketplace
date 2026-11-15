export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  devtools: { enabled: false },

  modules: ['@pinia/nuxt'],
  css: ['~/assets/css/main.css'],

  runtimeConfig: {
    // used by SSR (server -> server, inside the docker network)
    apiInternal: 'http://backend:8000',
    public: {
      // used by the browser (goes through nginx)
      apiBase: 'http://localhost/api',
    },
  },

  app: {
    head: {
      htmlAttrs: { lang: 'ru' },
      title: 'Мини-маркетплейс',
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'Каталог, корзина, заказы и админка — Nuxt 3 + FastAPI.' },
      ],
    },
  },

  typescript: {
    strict: true,
  },
})
