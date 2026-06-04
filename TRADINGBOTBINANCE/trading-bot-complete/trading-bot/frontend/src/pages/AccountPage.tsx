import { useEffect, useState } from 'react'
import { Wallet, RefreshCw, TrendingUp, TrendingDown, LogOut, X, AlertTriangle } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchBalances, fetchPositions, exitPosition, fetchTodayPnl } from '../api/client'
import type { Balance, Position } from '../types'

function fmt(n: string | number, dec = 4) {
  return Number(n).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: dec })
}

interface ExitModal {
  symbol: string
  positionAmt: string
  side: 'BUY' | 'SELL'
  maxQty: number
}

export default function AccountPage() {
  const [balances, setBalances] = useState<Balance[]>([])
  const [positions, setPositions] = useState<Position[]>([])
  const [todayPnl, setTodayPnl] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [exitingSymbol, setExitingSymbol] = useState<string | null>(null)
  const [exitModal, setExitModal] = useState<ExitModal | null>(null)
  const [exitQty, setExitQty] = useState('')

  const load = async () => {
    setLoading(true)
    setError('')
    try {
      const [b, p, pnl] = await Promise.all([fetchBalances(), fetchPositions(), fetchTodayPnl()])
      setBalances(b)
      setPositions(p)
      setTodayPnl(pnl)
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Failed to fetch account data')
    } finally {
      setLoading(false)
    }
  }

  const openExitModal = (symbol: string, positionAmt: string) => {
    const maxQty = Math.abs(Number(positionAmt))
    const side   = Number(positionAmt) > 0 ? 'SELL' : 'BUY'
    setExitQty(String(maxQty))
    setExitModal({ symbol, positionAmt, side, maxQty })
  }

  const closeExitModal = () => {
    setExitModal(null)
    setExitQty('')
  }

  const confirmExit = async () => {
    if (!exitModal) return
    const qty = Number(exitQty)
    if (!exitQty || isNaN(qty) || qty <= 0) {
      toast.error('Enter a valid quantity')
      return
    }
    if (qty > exitModal.maxQty) {
      toast.error(`Quantity cannot exceed position size (${exitModal.maxQty})`)
      return
    }
    closeExitModal()
    setExitingSymbol(exitModal.symbol)
    try {
      const order = await exitPosition(exitModal.symbol, qty)
      toast.success(`${exitModal.symbol} exit placed — Order #${order.order_id}`)
      await load()
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? `Failed to exit ${exitModal.symbol}`)
    } finally {
      setExitingSymbol(null)
    }
  }

  useEffect(() => {
    load()
    const id = setInterval(load, 1000)
    return () => clearInterval(id)
  }, [])

  const totalBalance = balances.reduce((s, b) => s + Number(b.walletBalance), 0)
  const totalUPnl   = balances.reduce((s, b) => s + Number(b.unrealizedProfit), 0)

  return (
    <div className="p-8 animate-fade-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-display font-semibold text-slate-900 mb-1">Account</h1>
          <p className="text-slate-400 text-sm">Testnet wallet balances &amp; open positions</p>
        </div>
        <button
          onClick={load}
          disabled={loading}
          className="flex items-center gap-2 text-sm text-slate-500 hover:text-slate-900 transition-colors px-3 py-2 rounded-lg hover:bg-slate-100 border border-slate-200 shadow-sm"
        >
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="card border-rose-200 bg-rose-50 mb-6 text-rose-600 text-sm font-display">
          {error}
        </div>
      )}

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Wallet Balance', value: `$${fmt(totalBalance)}` },
          {
            label: 'Unrealised PnL',
            value: `${totalUPnl >= 0 ? '+' : ''}$${fmt(totalUPnl)}`,
            accent: totalUPnl >= 0 ? 'text-emerald-600' : 'text-rose-600',
          },
          { label: 'Open Positions', value: String(positions.length) },
          {
            label: 'Realised PnL (Today)',
            value: todayPnl === null ? '—' : `${todayPnl >= 0 ? '+' : ''}$${fmt(todayPnl)}`,
            accent: todayPnl === null ? 'text-slate-300' : todayPnl >= 0 ? 'text-emerald-600' : 'text-rose-600',
            sub: 'Since UTC midnight',
          },
        ].map(({ label, value, accent, sub }) => (
          <div key={label} className="card">
            <p className="label">{label}</p>
            <p className={`text-2xl font-display font-semibold mt-1 ${accent ?? 'text-slate-900'}`}>{value}</p>
            {sub && <p className="text-[10px] font-display text-slate-400 mt-1">{sub}</p>}
          </div>
        ))}
      </div>

      {/* Balances */}
      <div className="card mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Wallet size={14} className="text-accent-cyan" />
          <h2 className="text-sm font-display font-semibold text-slate-900">Balances</h2>
        </div>
        {balances.length === 0 ? (
          <p className="text-slate-400 text-sm font-display py-4 text-center">No balances available</p>
        ) : (
          <div className="space-y-1">
            {balances.map((b) => (
              <div key={b.asset} className="flex items-center justify-between py-2.5 border-b border-slate-100 last:border-0">
                <div>
                  <p className="text-sm font-display font-semibold text-slate-900">{b.asset}</p>
                  <p className="text-xs font-display text-slate-400">Available: {fmt(b.availableBalance)}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-display font-medium text-slate-700">{fmt(b.walletBalance)}</p>
                  <p className={`text-xs font-display ${Number(b.unrealizedProfit) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                    UPnL: {fmt(b.unrealizedProfit)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Positions */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp size={14} className="text-emerald-600" />
          <h2 className="text-sm font-display font-semibold text-slate-900">Open Positions</h2>
        </div>
        {positions.length === 0 ? (
          <p className="text-slate-400 text-sm font-display py-4 text-center">No open positions</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                {['Symbol', 'Size', 'Entry', 'Mark', 'UPnL', 'ROE%', ''].map((h) => (
                  <th key={h} className="text-left pb-3 pt-2 px-1 first:pl-0 text-[10px] font-display font-semibold text-slate-400 uppercase tracking-widest">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {positions.map((p) => {
                const pnl = Number(p.unRealizedProfit)
                const isLong = Number(p.positionAmt) > 0
                const isExiting = exitingSymbol === p.symbol
                return (
                  <tr key={p.symbol} className="hover:bg-slate-50 transition-colors">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        {isLong
                          ? <TrendingUp size={12} className="text-emerald-600" />
                          : <TrendingDown size={12} className="text-rose-600" />}
                        <span className="font-display font-semibold text-slate-900">{p.symbol}</span>
                      </div>
                    </td>
                    <td className={`py-3 pr-4 font-display text-xs font-semibold ${isLong ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {p.positionAmt}
                    </td>
                    <td className="py-3 pr-4 font-display text-xs text-slate-400">${fmt(p.entryPrice)}</td>
                    <td className="py-3 pr-4 font-display text-xs font-medium text-slate-700">${fmt(p.markPrice)}</td>
                    <td className={`py-3 pr-4 font-display text-xs font-semibold ${pnl >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {pnl >= 0 ? '+' : ''}{fmt(p.unRealizedProfit)}
                    </td>
                    <td className={`py-3 pr-4 font-display text-xs font-semibold ${Number(p.percentage) >= 0 ? 'text-emerald-600' : 'text-rose-600'}`}>
                      {Number(p.percentage).toFixed(2)}%
                    </td>
                    <td className="py-3">
                      <button
                        onClick={() => openExitModal(p.symbol, p.positionAmt)}
                        disabled={isExiting || exitingSymbol !== null}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-[11px] font-display font-semibold border border-rose-200 text-rose-600 hover:bg-rose-50 hover:border-rose-300 transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
                      >
                        <LogOut size={11} />
                        {isExiting ? 'Exiting…' : 'Exit'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
      {/* ── Exit Modal ── */}
      {exitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={closeExitModal}
          />

          {/* Dialog */}
          <div className="relative bg-white rounded-2xl shadow-card-md border border-slate-200 w-full max-w-sm animate-fade-up">
            {/* Header */}
            <div className="flex items-center justify-between px-5 pt-5 pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-lg bg-rose-50 border border-rose-200 flex items-center justify-center">
                  <AlertTriangle size={14} className="text-rose-500" />
                </div>
                <div>
                  <p className="text-sm font-display font-semibold text-slate-900">Exit Position</p>
                  <p className="text-[10px] font-display text-slate-400">{exitModal.symbol} · reduceOnly MARKET</p>
                </div>
              </div>
              <button onClick={closeExitModal} className="text-slate-400 hover:text-slate-700 transition-colors">
                <X size={16} />
              </button>
            </div>

            {/* Body */}
            <div className="px-5 py-4 space-y-4">
              {/* Info row */}
              <div className="flex gap-3">
                <div className="flex-1 bg-slate-50 rounded-lg px-3 py-2.5 border border-slate-200">
                  <p className="text-[10px] font-display text-slate-400 uppercase tracking-widest mb-0.5">Side</p>
                  <p className={`text-sm font-display font-semibold ${exitModal.side === 'SELL' ? 'text-rose-600' : 'text-emerald-600'}`}>
                    {exitModal.side}
                  </p>
                </div>
                <div className="flex-1 bg-slate-50 rounded-lg px-3 py-2.5 border border-slate-200">
                  <p className="text-[10px] font-display text-slate-400 uppercase tracking-widest mb-0.5">Max Qty</p>
                  <p className="text-sm font-display font-semibold text-slate-900">{exitModal.maxQty}</p>
                </div>
              </div>

              {/* Quantity input */}
              <div>
                <label className="label">Quantity to Exit</label>
                <input
                  type="number"
                  className="input"
                  value={exitQty}
                  min={0.001}
                  max={exitModal.maxQty}
                  step="any"
                  autoFocus
                  onChange={(e) => setExitQty(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && confirmExit()}
                />
                <div className="flex gap-2 mt-2">
                  {[25, 50, 75, 100].map((pct) => (
                    <button
                      key={pct}
                      onClick={() => setExitQty(String(Number((exitModal.maxQty * pct / 100).toFixed(8))))}
                      className="flex-1 py-1 rounded-lg text-[10px] font-display font-semibold bg-slate-100 text-slate-500 hover:bg-rose-50 hover:text-rose-600 border border-slate-200 hover:border-rose-200 transition-all"
                    >
                      {pct}%
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="px-5 pb-5 flex gap-3">
              <button
                onClick={closeExitModal}
                className="flex-1 py-2.5 rounded-lg text-sm font-display font-semibold text-slate-500 bg-slate-100 hover:bg-slate-200 transition-colors border border-slate-200"
              >
                Cancel
              </button>
              <button
                onClick={confirmExit}
                className="flex-1 py-2.5 rounded-lg text-sm font-display font-semibold text-white bg-rose-600 hover:bg-rose-700 transition-colors shadow-sm"
              >
                Confirm Exit
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
