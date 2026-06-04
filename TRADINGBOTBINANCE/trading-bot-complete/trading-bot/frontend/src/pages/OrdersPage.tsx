import { useEffect, useState, useCallback } from 'react'
import { RefreshCw, Search } from 'lucide-react'
import { fetchOrders, syncOrders } from '../api/client'
import type { Order, OrdersResponse } from '../types'
import StatusBadge from '../components/StatusBadge'

const SYMBOLS = ['', 'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT']

function fmt(n: number) { return n > 0 ? n.toLocaleString(undefined, { maximumFractionDigits: 4 }) : '—' }
function fmtDate(s: string) {
  const d = new Date(s)
  return d.toLocaleString('en-GB', { dateStyle: 'short', timeStyle: 'medium' })
}

export default function OrdersPage() {
  const [data, setData] = useState<OrdersResponse | null>(null)
  const [symbol, setSymbol] = useState('')
  const [loading, setLoading] = useState(false)
  const [page, setPage] = useState(0)
  const limit = 20

  const load = useCallback(async () => {
    setLoading(true)
    try {
      await syncOrders()
      const res = await fetchOrders({ symbol: symbol || undefined, limit, skip: page * limit })
      setData(res)
    } finally {
      setLoading(false)
    }
  }, [symbol, page])

  useEffect(() => { load() }, [load])

  const totalPages = data ? Math.ceil(data.total / limit) : 0

  return (
    <div className="p-8 animate-fade-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-display font-medium text-white mb-1">Order History</h1>
          <p className="text-white/40 text-sm">{data?.total ?? 0} orders stored in MongoDB</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-white/50 hover:text-white transition-colors px-3 py-2 rounded-lg hover:bg-white/5"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-4 flex items-center gap-4">
        <Search size={14} className="text-white/30 shrink-0" />
        <select
          className="bg-transparent text-sm font-display text-white/70 outline-none"
          value={symbol}
          onChange={(e) => { setSymbol(e.target.value); setPage(0) }}
        >
          {SYMBOLS.map((s) => (
            <option key={s} value={s} className="bg-surface-1">{s || 'All Symbols'}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                {['Time', 'Symbol', 'Side', 'Order Type', 'Qty', 'Limit Price', 'Fill Price', 'Status'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[10px] font-display text-white/30 uppercase tracking-widest">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {data?.orders.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-white/30 font-display text-sm">
                    No orders yet. Place your first order to see it here.
                  </td>
                </tr>
              )}
              {data?.orders.map((o: Order) => (
                <tr key={o.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3 font-display text-xs text-white/40 whitespace-nowrap">{fmtDate(o.created_at)}</td>
                  <td className="px-4 py-3 font-display text-xs font-medium text-white">{o.symbol}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-display font-medium ${o.side === 'BUY' ? 'text-accent-green' : 'text-accent-red'}`}>
                      {o.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-display text-xs text-white/60">{o.order_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3 font-display text-xs text-white">{fmt(o.orig_qty)}</td>
                  <td className="px-4 py-3 font-display text-xs text-white/40">{o.price > 0 ? `$${fmt(o.price)}` : '—'}</td>
                  <td className={`px-4 py-3 font-display text-xs font-medium ${
                    o.avg_price > 0
                      ? o.side === 'BUY' ? 'text-accent-green' : 'text-accent-red'
                      : 'text-white/20'
                  }`}>
                    {o.avg_price > 0 ? `$${fmt(o.avg_price)}` : '—'}
                  </td>
                  <td className="px-4 py-3"><StatusBadge status={o.status} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-border">
            <span className="text-xs font-display text-white/30">
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1.5 rounded-lg text-xs font-display text-white/50 hover:text-white disabled:opacity-30 hover:bg-white/5 transition-colors"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1.5 rounded-lg text-xs font-display text-white/50 hover:text-white disabled:opacity-30 hover:bg-white/5 transition-colors"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
