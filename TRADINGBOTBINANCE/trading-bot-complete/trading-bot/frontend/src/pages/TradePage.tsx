import { useState } from 'react'
import toast from 'react-hot-toast'
import { TrendingUp, TrendingDown, CheckCircle2 } from 'lucide-react'
import clsx from 'clsx'
import { placeOrder } from '../api/client'
import type { Order, OrderSide, OrderType } from '../types'

const SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT']

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="label">{label}</label>
      {children}
    </div>
  )
}

export default function TradePage() {
  const [side, setSide] = useState<OrderSide>('BUY')
  const [orderType, setOrderType] = useState<OrderType>('MARKET')
  const [symbol, setSymbol] = useState('BTCUSDT')
  const [quantity, setQuantity] = useState('')
  const [price, setPrice] = useState('')
  const [stopPrice, setStopPrice] = useState('')
  const [tif, setTif] = useState('GTC')
  const [loading, setLoading] = useState(false)
  const [lastOrder, setLastOrder] = useState<Order | null>(null)

  const handleSubmit = async () => {
    if (!quantity || isNaN(Number(quantity)) || Number(quantity) <= 0) {
      toast.error('Enter a valid quantity')
      return
    }
    if (orderType === 'LIMIT' && (!price || isNaN(Number(price)))) {
      toast.error('Enter a valid price for LIMIT orders')
      return
    }
    if (orderType === 'STOP_MARKET' && (!stopPrice || isNaN(Number(stopPrice)))) {
      toast.error('Enter a valid stop price for STOP_MARKET orders')
      return
    }

    setLoading(true)
    try {
      const result = await placeOrder({
        symbol,
        side,
        type: orderType,
        quantity: Number(quantity),
        ...(orderType === 'LIMIT' && { price: Number(price), time_in_force: tif }),
        ...(orderType === 'STOP_MARKET' && { stop_price: Number(stopPrice) }),
      })
      setLastOrder(result)
      toast.success(`Order placed! ID: ${result.order_id}`)
    } catch (err: any) {
      const msg = err?.response?.data?.detail ?? err.message ?? 'Failed to place order'
      toast.error(msg)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-8 max-w-xl animate-fade-up">
      <h1 className="text-2xl font-display font-semibold text-slate-900 mb-1">Place Order</h1>
      <p className="text-slate-400 text-sm mb-8">Binance USDT-M Futures Testnet</p>

      <div className="card space-y-5">
        {/* BUY / SELL toggle */}
        <div className="grid grid-cols-2 gap-2 p-1 bg-slate-100 rounded-xl">
          {(['BUY', 'SELL'] as OrderSide[]).map((s) => (
            <button
              key={s}
              onClick={() => setSide(s)}
              className={clsx(
                'py-2.5 rounded-lg text-sm font-display font-semibold flex items-center justify-center gap-2 transition-all duration-150',
                side === s
                  ? s === 'BUY'
                    ? 'bg-emerald-600 text-white shadow-glow shadow-sm'
                    : 'bg-rose-600 text-white shadow-glow-red shadow-sm'
                  : 'text-slate-400 hover:text-slate-700'
              )}
            >
              {s === 'BUY' ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
              {s}
            </button>
          ))}
        </div>

        {/* Symbol */}
        <Field label="Symbol">
          <select className="input" value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {SYMBOLS.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </Field>

        {/* Order type */}
        <Field label="Order Type">
          <div className="grid grid-cols-3 gap-1.5">
            {(['MARKET', 'LIMIT', 'STOP_MARKET'] as OrderType[]).map((t) => (
              <button
                key={t}
                onClick={() => setOrderType(t)}
                className={clsx(
                  'py-2 rounded-lg text-xs font-display font-medium transition-all border',
                  orderType === t
                    ? 'border-indigo-400 text-indigo-700 bg-indigo-50 shadow-sm'
                    : 'border-slate-200 text-slate-400 hover:text-slate-700 hover:border-slate-300 hover:bg-slate-50'
                )}
              >
                {t.replace('_', ' ')}
              </button>
            ))}
          </div>
        </Field>

        {/* Quantity */}
        <Field label="Quantity">
          <input
            type="number"
            className="input"
            placeholder="0.001"
            value={quantity}
            min={0}
            step="any"
            onChange={(e) => setQuantity(e.target.value)}
          />
        </Field>

        {/* Limit fields */}
        {orderType === 'LIMIT' && (
          <>
            <Field label="Limit Price (USDT)">
              <input
                type="number"
                className="input"
                placeholder="e.g. 67000"
                value={price}
                min={0}
                step="any"
                onChange={(e) => setPrice(e.target.value)}
              />
            </Field>
            <Field label="Time in Force">
              <select className="input" value={tif} onChange={(e) => setTif(e.target.value)}>
                <option value="GTC">GTC — Good Till Cancelled</option>
                <option value="IOC">IOC — Immediate Or Cancel</option>
                <option value="FOK">FOK — Fill Or Kill</option>
              </select>
            </Field>
          </>
        )}

        {/* Stop price */}
        {orderType === 'STOP_MARKET' && (
          <Field label="Stop Trigger Price (USDT)">
            <input
              type="number"
              className="input"
              placeholder="e.g. 65000"
              value={stopPrice}
              min={0}
              step="any"
              onChange={(e) => setStopPrice(e.target.value)}
            />
          </Field>
        )}

        {/* Submit */}
        <button
          onClick={handleSubmit}
          disabled={loading}
          className={clsx(
            'w-full py-3 rounded-xl text-sm font-display font-semibold transition-all shadow-sm',
            side === 'BUY'
              ? 'bg-emerald-600 text-white hover:bg-emerald-700 shadow-glow disabled:opacity-40'
              : 'bg-rose-600 text-white hover:bg-rose-700 shadow-glow-red disabled:opacity-40'
          )}
        >
          {loading ? 'Placing…' : `${side} ${symbol}`}
        </button>
      </div>

      {/* Result card */}
      {lastOrder && (
        <div className="mt-6 card animate-fade-up border-emerald-200 bg-emerald-50/30">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle2 size={16} className="text-emerald-600" />
            <span className="text-emerald-700 font-display text-sm font-semibold">Order Placed</span>
          </div>
          <div className="space-y-2 font-display text-xs">
            {[
              ['Order ID',  lastOrder.order_id],
              ['Status',    lastOrder.status],
              ['Symbol',    lastOrder.symbol],
              ['Side',      lastOrder.side],
              ['Executed',  `${lastOrder.executed_qty} / ${lastOrder.orig_qty}`],
              ['Avg Price', lastOrder.avg_price > 0 ? `$${lastOrder.avg_price}` : '—'],
            ].map(([k, v]) => (
              <div key={String(k)} className="flex justify-between py-0.5">
                <span className="text-slate-400">{k}</span>
                <span className="text-slate-800 font-medium">{String(v)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
