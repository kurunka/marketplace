/**
 * Typed API client.
 * - on the server it talks to the backend container directly
 * - in the browser it goes through nginx (/api)
 * - the JWT lives in a cookie, so SSR requests are authenticated too
 */
export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('token', {
    sameSite: 'lax',
    maxAge: 60 * 60 * 24 * 7,
  })

  const baseURL = import.meta.server
    ? `${config.apiInternal}/api`
    : String(config.public.apiBase)

  return async function api<T>(path: string, options: Record<string, unknown> = {}): Promise<T> {
    const headers: Record<string, string> = {
      ...((options.headers as Record<string, string>) ?? {}),
    }
    if (token.value) headers.Authorization = `Bearer ${token.value}`

    return await $fetch<T>(path, { baseURL, ...options, headers }) as T
  }
}
