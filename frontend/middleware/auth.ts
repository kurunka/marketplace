export default defineNuxtRouteMiddleware((to) => {
  const token = useCookie<string | null>('token')
  if (!token.value) {
    return navigateTo(`/login?next=${encodeURIComponent(to.fullPath)}`)
  }
})
