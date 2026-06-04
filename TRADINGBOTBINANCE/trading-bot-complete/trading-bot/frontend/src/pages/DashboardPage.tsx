import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { TrendingUp, ClipboardList, Wallet, Activity, ArrowRight, CheckCircle2, Circle } from 'lucide-react'
import { fetchOrders, fetchPnlStats, pingBinance } from '../api/client'
import type { Order, PnlStats } from '../types'
import StatusBadge from '../components/StatusBadge'

function fmt(n: number, dec = 4) {
  return Number(n).toLocaleString(undefined, { maximumFractionDigits: dec })
}
function fmtDate(s: string) {
  return new Date(s).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

export default function DashboardPage() {
  const [recentOrders, setRecentOrders] = useState<Order[]>([])
  const [stats, setStats] = useState<PnlStats | null>(null)
  const [connected, setConnected] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      fetchOrders({ limit: 5 }),
      fetchPnlStats(),
      pingBinance(),
    ]).then(([ordersRes, pnlRes, ping]) => {
      setRecentOrders(ordersRes.orders)
      setStats(pnlRes)
      setConnected(ping)
    }).finally(() => setLoading(false))
  }, [])

  const pnlPositive = (stats?.realized_pnl ?? 0) >= 0

  const cards = [
    { label: 'Total Orders',   value: String(stats?.total_orders ?? 0),    icon: ClipboardList, to: '/orders',    color: 'text-accent-cyan'  },
    { label: 'Filled',         value: String(stats?.filled_orders ?? 0),    icon: CheckCircle2,  to: '/orders',    color: 'text-accent-green' },
    { label: 'Symbols Traded', value: String(stats?.by_symbol.length ?? 0), icon: Activity,      to: '/analytics', color: 'text-accent-yellow'},
    {
      label: 'Realised PnL',
      value: `${pnlPositive ? '+' : ''}$${fmt(stats?.realized_pnl ?? 0)}`,
      icon: TrendingUp,
      to: '/analytics',
      color: pnlPositive ? 'text-accent-green' : 'text-accent-red',
    },
  ]

  return (
    <div className="p-8 animate-fade-up">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-display font-semibold text-slate-900 mb-1">Dashboard</h1>
          <p className="text-slate-400 text-sm">Binance USDT-M Futures Testnet</p>
        </div>
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white border border-slate-200 shadow-sm">
          {connected === null ? (
            <Circle size={8} className="text-slate-300 animate-pulse" />
          ) : connected ? (
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          ) : (
            <span className="w-2 h-2 rounded-full bg-rose-500" />
          )}
          <span className="text-xs font-display text-slate-500">
            {connected === null ? 'Checking…' : connected ? 'API Connected' : 'API Offline'}
          </span>
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {cards.map(({ label, value, icon: Icon, to, color }) => (
          <Link key={label} to={to} className="card hover:shadow-card-md hover:border-slate-300 transition-all group">
            <div className="flex items-center justify-between mb-3">
              <Icon size={16} className={color} />
              <ArrowRight size={12} className="text-slate-300 group-hover:text-slate-500 transition-colors" />
            </div>
            <p className={`text-2xl font-display font-semibold ${color}`}>{loading ? '—' : value}</p>
            <p className="text-xs font-display text-slate-400 mt-1">{label}</p>
          </Link>
        ))}
      </div>

      <div className="grid grid-cols-5 gap-6">
        {/* Recent orders */}
        <div className="col-span-3 card">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-display font-semibold text-slate-900">Recent Orders</h2>
            <Link to="/orders" className="text-xs font-display text-slate-400 hover:text-slate-700 transition-colors flex items-center gap-1">
              View all <ArrowRight size={10} />
            </Link>
          </div>
          {recentOrders.length === 0 ? (
            <div className="py-8 text-center">
              <p className="text-slate-400 text-sm font-display">No orders yet</p>
              <Link to="/trade" className="mt-3 inline-flex items-center gap-1 text-xs font-display text-accent-green hover:brightness-90">
                Place your first order <ArrowRight size={10} />
              </Link>
            </div>
          ) : (
            <div className="space-y-1">
              {recentOrders.map((o) => (
                <div key={o.id} className="flex items-center justify-between py-2.5 border-b border-slate-100 last:border-0">
                  <div className="flex items-center gap-3">
                    <div className={`w-1 h-8 rounded-full ${o.side === 'BUY' ? 'bg-emerald-500' : 'bg-rose-500'}`} />
                    <div>
                      <p className="text-xs font-display font-semibold text-slate-900">{o.symbol}</p>
                      <p className="text-[10px] font-display text-slate-400">{fmtDate(o.created_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-xs font-display text-slate-500">{o.orig_qty}</span>
                    {o.avg_price > 0 && (
                      <span className="text-xs font-display font-medium text-slate-700">${fmt(o.avg_price)}</span>
                    )}
                    <StatusBadge status={o.status} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Quick actions */}
        <div className="col-span-2 space-y-4">
          <div className="card">
            <h2 className="text-sm font-display font-semibold text-slate-900 mb-4">Quick Actions</h2>
            <div className="space-y-2">
              <Link to="/trade" className="flex items-center justify-between w-full p-3 rounded-lg bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 transition-colors group">
                <div className="flex items-center gap-2">
                  <TrendingUp size={14} className="text-emerald-700" />
                  <span className="text-xs font-display font-semibold text-emerald-700">Place New Order</span>
                </div>
                <ArrowRight size={12} className="text-emerald-400 group-hover:text-emerald-600 transition-colors" />
              </Link>
              <Link to="/account" className="flex items-center justify-between w-full p-3 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors group">
                <div className="flex items-center gap-2">
                  <Wallet size={14} className="text-slate-400" />
                  <span className="text-xs font-display text-slate-600">View Balances</span>
                </div>
                <ArrowRight size={12} className="text-slate-300 group-hover:text-slate-500 transition-colors" />
              </Link>
              <Link to="/analytics" className="flex items-center justify-between w-full p-3 rounded-lg bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors group">
                <div className="flex items-center gap-2">
                  <Activity size={14} className="text-slate-400" />
                  <span className="text-xs font-display text-slate-600">Analytics &amp; P&amp;L</span>
                </div>
                <ArrowRight size={12} className="text-slate-300 group-hover:text-slate-500 transition-colors" />
              </Link>
            </div>
          </div>

          {stats && stats.by_symbol.length > 0 && (
            <div className="card">
              <h2 className="text-sm font-display font-semibold text-slate-900 mb-4">Top Symbols</h2>
              <div className="space-y-2">
                {stats.by_symbol.slice(0, 4).map((s) => (
                  <div key={s._id} className="flex items-center justify-between py-1">
                    <span className="text-xs font-display font-medium text-slate-700">{s._id}</span>
                    <span className="text-xs font-display text-slate-400">{s.total_orders} orders</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
