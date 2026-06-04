import axios from 'axios'
import type { Order, PlaceOrderPayload, OrdersResponse, PnlStats } from '../types'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
})

// ── Orders ────────────────────────────────────────────────────────────────────

export async function placeOrder(payload: PlaceOrderPayload): Promise<Order> {
  const { data } = await api.post<Order>('/orders/', payload)
  return data
}

export async function fetchOrders(params?: {
  symbol?: string
  limit?: number
  skip?: number
}): Promise<OrdersResponse> {
  const { data } = await api.get<OrdersResponse>('/orders/', { params })
  return data
}

export async function fetchPnlStats(): Promise<PnlStats> {
  const { data } = await api.get<PnlStats>('/orders/stats/pnl')
  return data
}

export async function fetchTodayPnl(): Promise<number> {
  const { data } = await api.get<PnlStats>('/orders/stats/pnl?today=true')
  return data.realized_pnl
}

export async function syncOrders(): Promise<{ checked: number; updated: number; failed: number }> {
  const { data } = await api.post('/orders/sync')
  return data
}

// ── Account ───────────────────────────────────────────────────────────────────

export async function fetchBalances() {
  const { data } = await api.get('/account/balance')
  return data.balances
}

export async function fetchPositions() {
  const { data } = await api.get('/account/positions')
  return data.positions
}

export async function exitPosition(symbol: string, qty?: number): Promise<Order> {
  const { data } = await api.post<Order>(
    `/account/positions/${symbol}/exit`,
    null,
    qty !== undefined ? { params: { qty } } : undefined,
  )
  return data
}

export async function fetchTicker(symbol: string) {
  const { data } = await api.get(`/account/ticker/${symbol}`)
  return data
}

export async function pingBinance(): Promise<boolean> {
  try {
    const { data } = await api.get('/account/ping')
    return data.binance_reachable
  } catch {
    return false
  }
}

// ── Credentials ───────────────────────────────────────────────────────────────

export interface CredentialStatus {
  api_key_set: boolean
  api_key_preview: string
}

export async function fetchCredentials(): Promise<CredentialStatus> {
  const { data } = await api.get<CredentialStatus>('/account/credentials')
  return data
}

export async function saveCredentials(payload: { api_key: string; api_secret: string }): Promise<CredentialStatus> {
  const { data } = await api.post<CredentialStatus>('/account/credentials', payload)
  return data
}
