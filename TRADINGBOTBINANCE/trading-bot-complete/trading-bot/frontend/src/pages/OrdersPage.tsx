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
          <h1 className="text-2xl font-display font-semibold text-slate-900 mb-1">Order History</h1>
          <p className="text-slate-400 text-sm">{data?.total ?? 0} orders stored</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition-colors px-3 py-2 rounded-lg hover:bg-slate-100 border border-slate-200 shadow-sm disabled:opacity-40"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card mb-4 flex items-center gap-3 py-3">
        <Search size={14} className="text-slate-400 shrink-0" />
        <select
          className="bg-transparent text-sm font-display text-slate-600 outline-none cursor-pointer"
          value={symbol}
          onChange={(e) => { setSymbol(e.target.value); setPage(0) }}
        >
          {SYMBOLS.map((s) => (
            <option key={s} value={s} className="bg-white">{s || 'All Symbols'}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="card p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                {['Time', 'Symbol', 'Side', 'Order Type', 'Qty', 'Limit Price', 'Fill Price', 'Status'].map((h) => (
                  <th key={h} className="text-left px-4 py-3 text-[10px] font-display font-semibold text-slate-400 uppercase tracking-widest">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data?.orders.length === 0 && (
                <tr>
                  <td colSpan={8} className="px-4 py-12 text-center text-slate-400 font-display text-sm">
                    No orders yet. Place your first order to see it here.
                  </td>
                </tr>
              )}
              {data?.orders.map((o: Order) => (
                <tr key={o.id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3 font-display text-xs text-slate-400 whitespace-nowrap">{fmtDate(o.created_at)}</td>
                  <td className="px-4 py-3 font-display text-xs font-semibold text-slate-900">{o.symbol}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs font-display font-semibold ${o.side === 'BUY' ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {o.side}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-display text-xs text-slate-500">{o.order_type.replace('_', ' ')}</td>
                  <td className="px-4 py-3 font-display text-xs text-slate-700">{fmt(o.orig_qty)}</td>
                  <td className="px-4 py-3 font-display text-xs text-slate-400">{o.price > 0 ? `$${fmt(o.price)}` : '—'}</td>
                  <td className={`px-4 py-3 font-display text-xs font-semibold ${
                    o.avg_price > 0
                      ? o.side === 'BUY' ? 'text-emerald-600' : 'text-rose-600'
                      : 'text-slate-300'
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
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 bg-slate-50">
            <span className="text-xs font-display text-slate-400">
              Page {page + 1} of {totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(0, p - 1))}
                disabled={page === 0}
                className="px-3 py-1.5 rounded-lg text-xs font-display text-slate-500 hover:text-slate-900 disabled:opacity-30 hover:bg-white border border-slate-200 transition-colors shadow-sm"
              >
                Prev
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
                disabled={page >= totalPages - 1}
                className="px-3 py-1.5 rounded-lg text-xs font-display text-slate-500 hover:text-slate-900 disabled:opacity-30 hover:bg-white border border-slate-200 transition-colors shadow-sm"
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
