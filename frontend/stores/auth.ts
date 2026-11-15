import type { AuthResponse, User } from '~/types/api'

export const useAuthStore = defineStore('auth', () => {
  const api = useApi()
  const token = useCookie<string | null>('token', {
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7,
  })
  const user = useState<User | null>('auth-user', () => null)

  const isAuthenticated = computed(() => Boolean(token.value))
  const isAdmin = computed(() => user.value?.role === 'admin')

  function apply(payload: AuthResponse) {
    token.value = payload.access_token
    user.value = payload.user
  }

  async function login(email: string, password: string) {
    apply(await api<AuthResponse>('/auth/login', { method: 'POST', body: { email, password } }))
  }

  async function register(email: string, password: string, fullName: string) {
    apply(
      await api<AuthResponse>('/auth/register', {
        method: 'POST',
        body: { email, password, full_name: fullName },
      }),
    )
  }

  async function fetchMe() {
    if (!token.value) return null
    try {
      user.value = await api<User>('/auth/me')
    } catch {
      token.value = null
      user.value = null
    }
    return user.value
  }

  function logout() {
    token.value = null
    user.value = null
    navigateTo('/')
  }

  return { user, token, isAuthenticated, isAdmin, login, register, fetchMe, logout }
})
