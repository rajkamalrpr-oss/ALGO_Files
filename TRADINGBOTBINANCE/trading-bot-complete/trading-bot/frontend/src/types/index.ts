export type OrderSide = 'BUY' | 'SELL'
export type OrderType = 'MARKET' | 'LIMIT' | 'STOP_MARKET'
export type OrderStatus = 'NEW' | 'PARTIALLY_FILLED' | 'FILLED' | 'CANCELED' | 'REJECTED' | 'EXPIRED'

export interface Order {
  id: string
  order_id: number
  client_order_id: string
  symbol: string
  side: OrderSide
  order_type: string
  status: OrderStatus
  price: number
  orig_qty: number
  executed_qty: number
  avg_price: number
  time_in_force: string
  created_at: string
  fill_percent: number
}

export interface PlaceOrderPayload {
  symbol: string
  side: OrderSide
  type: OrderType
  quantity: number
  price?: number
  stop_price?: number
  time_in_force?: string
}

export interface Balance {
  asset: string
  walletBalance: string
  unrealizedProfit: string
  marginBalance: string
  availableBalance: string
}

export interface Position {
  symbol: string
  positionAmt: string
  entryPrice: string
  markPrice: string
  unRealizedProfit: string
  percentage: string
  leverage: string
}

export interface PnlStats {
  total_orders: number
  filled_orders: number
  fill_rate: number
  realized_pnl: number
  has_price_data: boolean
  by_symbol: SymbolStats[]
}

export interface SymbolStats {
  _id: string
  total_orders: number
  filled_orders: number
  total_buy_qty: number
  total_sell_qty: number
  total_buy_value: number
  total_sell_value: number
}

export interface OrdersResponse {
  orders: Order[]
  total: number
  limit: number
  skip: number
}
