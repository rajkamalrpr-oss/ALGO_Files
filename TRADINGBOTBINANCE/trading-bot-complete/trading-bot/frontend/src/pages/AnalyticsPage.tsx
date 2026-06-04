import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend,
} from 'recharts'
import { Activity, CheckCircle2, RefreshCw } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchPnlStats, syncOrders } from '../api/client'
import type { PnlStats } from '../types'

const COLORS = ['#059669', '#0284c7', '#d97706', '#e11d48', '#4f46e5', '#7c3aed']

function StatCard({ label, value, sub, accent }: {
  label: string; value: string; sub?: string; accent?: string
}) {
  return (
    <div className="card">
      <p className="label">{label}</p>
      <p className={`text-2xl font-display font-semibold mt-1 ${accent ?? 'text-slate-900'}`}>{value}</p>
      {sub && <p className="text-xs font-display text-slate-400 mt-1">{sub}</p>}
    </div>
  )
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-lg px-3 py-2 shadow-card-md">
      <p className="text-xs font-display text-slate-500 mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.name} className="text-xs font-display font-medium" style={{ color: p.color }}>
          {p.name}: {Number(p.value).toFixed(4)}
        </p>
      ))}
    </div>
  )
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<PnlStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)

  const load = () => {
    setLoading(true)
    fetchPnlStats()
      .then(setStats)
      .catch(() => toast.error('Failed to load analytics'))
      .finally(() => setLoading(false))
  }

  const handleSync = async () => {
    setSyncing(true)
    try {
      const result = await syncOrders()
      toast.success(`Sync complete — ${result.updated} order(s) updated`)
      load()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Sync failed')
    } finally {
      setSyncing(false)
    }
  }

  useEffect(() => { load() }, [])

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center h-64">
        <div className="text-slate-400 font-display text-sm animate-pulse">Loading analytics…</div>
      </div>
    )
  }

  if (!stats) return null

  const hasPriceData = stats.has_price_data
  const pnlPositive  = stats.realized_pnl >= 0

  const pieData = stats.by_symbol.map((s) => ({ name: s._id, value: s.total_orders }))
  const barData = stats.by_symbol.map((s) => ({
    symbol: s._id,
    'Buy Qty':  s.total_buy_qty,
    'Sell Qty': s.total_sell_qty,
  }))

  return (
    <div className="p-8 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-display font-semibold text-slate-900 mb-1">Analytics</h1>
          <p className="text-slate-400 text-sm">Order stats from MongoDB</p>
        </div>
        <div className="flex items-center gap-3">
          {!hasPriceData && (
            <span className="text-[10px] font-display text-slate-400 border border-slate-200 rounded-lg px-2.5 py-1 bg-white shadow-sm">
              No fill prices — sync to refresh
            </span>
          )}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition-colors px-3 py-2 rounded-lg hover:bg-slate-100 border border-slate-200 shadow-sm disabled:opacity-40"
          >
            <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
            {syncing ? 'Syncing…' : 'Sync Orders'}
          </button>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Orders"   value={String(stats.total_orders)} />
        <StatCard
          label="Filled Orders"
          value={String(stats.filled_orders)}
          sub={`${stats.fill_rate}% fill rate`}
        />
        <StatCard
          label="Realised PnL"
          value={hasPriceData ? `${pnlPositive ? '+' : ''}$${stats.realized_pnl.toFixed(4)}` : '—'}
          sub={hasPriceData ? undefined : 'No fill prices available'}
          accent={hasPriceData ? (pnlPositive ? 'text-emerald-600' : 'text-rose-600') : 'text-slate-300'}
        />
        <StatCard label="Active Symbols" value={String(stats.by_symbol.length)} />
      </div>

      <div className="grid grid-cols-2 gap-6 mb-6">
        {/* Bar chart */}
        <div className="card">
          <div className="flex items-center gap-2 mb-5">
            <Activity size={14} className="text-accent-cyan" />
            <h2 className="text-sm font-display font-semibold text-slate-900">Trade Quantity by Symbol</h2>
          </div>
          {barData.length === 0 || barData.every(d => d['Buy Qty'] === 0 && d['Sell Qty'] === 0) ? (
            <p className="text-slate-400 text-sm font-display py-8 text-center">No orders yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={barData} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                <XAxis
                  dataKey="symbol"
                  tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'DM Mono' }}
                  axisLine={false} tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 10, fontFamily: 'DM Mono' }}
                  axisLine={false} tickLine={false} width={40}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="Buy Qty"  fill="#059669" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Sell Qty" fill="#e11d48" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Pie chart */}
        <div className="card">
          <div className="flex items-center gap-2 mb-5">
            <CheckCircle2 size={14} className="text-emerald-600" />
            <h2 className="text-sm font-display font-semibold text-slate-900">Orders by Symbol</h2>
          </div>
          {pieData.length === 0 ? (
            <p className="text-slate-400 text-sm font-display py-8 text-center">No orders yet</p>
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%" cy="50%"
                  innerRadius={55} outerRadius={85}
                  paddingAngle={3} dataKey="value"
                >
                  {pieData.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(v) => [`${v} orders`]}
                  contentStyle={{
                    background: '#ffffff',
                    border: '1px solid #e2e8f0',
                    borderRadius: 10,
                    fontFamily: 'DM Mono',
                    fontSize: 12,
                    boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                  }}
                />
                <Legend
                  iconType="circle" iconSize={8}
                  formatter={(v) => <span style={{ fontSize: 11, fontFamily: 'DM Mono', color: '#64748b' }}>{v}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Symbol breakdown table */}
      <div className="card overflow-x-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-display font-semibold text-slate-900">Symbol Breakdown</h2>
          {!hasPriceData && (
            <span className="text-[10px] font-display text-slate-400">Prices unavailable — click Sync Orders</span>
          )}
        </div>
        <table className="w-full text-sm min-w-[720px]">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              {['Symbol', 'Orders', 'Filled', 'Buy Qty', 'Avg Buy Price', 'Sell Qty', 'Avg Sell Price', 'Net Qty', 'PnL'].map((h) => (
                <th key={h} className="text-left pb-3 pt-2 pr-4 text-[10px] font-display font-semibold text-slate-400 uppercase tracking-widest whitespace-nowrap">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {stats.by_symbol.map((s) => {
              const netQty       = s.total_buy_qty - s.total_sell_qty
              const avgBuyPrice  = s.total_buy_qty > 0  && s.total_buy_value > 0  ? s.total_buy_value  / s.total_buy_qty  : null
              const avgSellPrice = s.total_sell_qty > 0 && s.total_sell_value > 0 ? s.total_sell_value / s.total_sell_qty : null
              const matchedQty   = Math.min(s.total_buy_qty, s.total_sell_qty)
              const pnl          = matchedQty > 0 && avgBuyPrice != null && avgSellPrice != null
                ? (avgSellPrice - avgBuyPrice) * matchedQty : 0
              return (
                <tr key={s._id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 pr-4 font-display font-semibold text-slate-900 text-xs">{s._id}</td>
                  <td className="py-3 pr-4 font-display text-xs text-slate-500">{s.total_orders}</td>
                  <td className="py-3 pr-4 font-display text-xs text-slate-500">{s.filled_orders}</td>
                  <td className="py-3 pr-4 font-display text-xs text-emerald-600 font-medium">{s.total_buy_qty.toFixed(4)}</td>
                  <td className="py-3 pr-4 font-display text-xs text-emerald-600 font-medium">
                    {avgBuyPrice != null ? `$${avgBuyPrice.toLocaleString(undefined, { maximumFractionDigits: 4 })}` : '—'}
                  </td>
                  <td className="py-3 pr-4 font-display text-xs text-rose-600 font-medium">{s.total_sell_qty.toFixed(4)}</td>
                  <td className="py-3 pr-4 font-display text-xs text-rose-600 font-medium">
                    {avgSellPrice != null ? `$${avgSellPrice.toLocaleString(undefined, { maximumFractionDigits: 4 })}` : '—'}
                  </td>
                  <td className={`py-3 pr-4 font-display text-xs font-medium ${netQty >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    {netQty >= 0 ? '+' : ''}{netQty.toFixed(4)}
                  </td>
                  <td className={`py-3 font-display text-xs font-semibold ${
                    matchedQty === 0 || !hasPriceData ? 'text-slate-300'
                      : pnl >= 0 ? 'text-emerald-600' : 'text-rose-600'
                  }`}>
                    {matchedQty > 0 && hasPriceData ? `${pnl >= 0 ? '+' : ''}$${pnl.toFixed(4)}` : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
