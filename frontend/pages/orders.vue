<script setup lang="ts">
import type { Order, OrderStatus } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const api = useApi()
const route = useRoute()

const { data: orders } = await useAsyncData('my-orders', () => api<Order[]>('/orders'))

const created = computed(() => route.query.created)

const STATUS_LABELS: Record<OrderStatus, string> = {
  pending: 'Ожидает оплаты',
  paid: 'Оплачен',
  shipped: 'Отправлен',
  done: 'Завершён',
  cancelled: 'Отменён',
}

const fmt = (value: string) =>
  new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 })
    .format(Number(value))

const formatDate = (iso: string) =>
  new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
</script>

<template>
  <div class="container mt-24">
    <h1>Мои заказы</h1>

    <p v-if="created" class="error" style="background: rgba(61,220,151,.1); border-color: rgba(61,220,151,.4); color: #9ff0c8">
      Заказ №{{ created }} оформлен. Мы свяжемся с вами для подтверждения.
    </p>

    <div v-if="!orders?.length" class="empty mt-24">Заказов пока нет.</div>

    <div v-else class="stack mt-24">
      <div v-for="order in orders" :key="order.id" class="card" style="padding: 16px">
        <div class="row-between">
          <div>
            <strong>Заказ №{{ order.id }}</strong>
            <span class="muted" style="margin-left: 10px">{{ formatDate(order.created_at) }}</span>
          </div>
          <span class="tag" :class="`tag-${order.status}`">{{ STATUS_LABELS[order.status] }}</span>
        </div>

        <table class="table" style="margin-top: 12px">
          <tbody>
            <tr v-for="item in order.items" :key="item.id">
              <td>{{ item.title }}</td>
              <td class="muted" style="width: 90px">× {{ item.quantity }}</td>
              <td style="width: 120px; text-align: right">{{ fmt(item.price) }}</td>
            </tr>
          </tbody>
        </table>

        <div class="row-between" style="margin-top: 12px">
          <span class="muted">{{ order.address }}</span>
          <strong class="price">{{ fmt(order.total) }}</strong>
        </div>
      </div>
    </div>
  </div>
</template>
