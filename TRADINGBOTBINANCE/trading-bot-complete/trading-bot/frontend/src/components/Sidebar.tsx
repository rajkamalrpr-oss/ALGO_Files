import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  TrendingUp,
  ClipboardList,
  Wallet,
  Activity,
  Settings,
  Zap,
} from 'lucide-react'
import clsx from 'clsx'

const nav = [
  { to: '/',          icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/trade',     icon: TrendingUp,      label: 'Place Order' },
  { to: '/orders',    icon: ClipboardList,   label: 'Order History' },
  { to: '/account',   icon: Wallet,          label: 'Account' },
  { to: '/analytics', icon: Activity,        label: 'Analytics' },
]

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 flex flex-col bg-white border-r border-slate-200 h-screen sticky top-0 shadow-[1px_0_0_#e2e8f0]">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-indigo-700 flex items-center justify-center shadow-sm">
            <Zap size={15} className="text-white" />
          </div>
          <div>
            <p className="text-slate-900 text-sm font-semibold font-body leading-none">FuturesBot</p>
            <p className="text-slate-400 text-[10px] font-display mt-0.5 uppercase tracking-widest">Testnet</p>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 p-3 space-y-0.5">
        {nav.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-body transition-all duration-150',
                isActive
                  ? 'bg-indigo-50 text-indigo-700 font-semibold'
                  : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
              )
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={16} className={isActive ? 'text-indigo-600' : 'text-slate-400'} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <div className="px-3 pb-3 border-t border-slate-100 pt-3">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            clsx(
              'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-body transition-all duration-150',
              isActive
                ? 'bg-indigo-50 text-indigo-700 font-semibold'
                : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
            )
          }
        >
          {({ isActive }) => (
            <>
              <Settings size={16} className={isActive ? 'text-indigo-600' : 'text-slate-400'} />
              Settings
            </>
          )}
        </NavLink>
      </div>

      {/* Footer */}
      <div className="px-5 pb-4">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <p className="text-slate-400 text-[10px] font-display">Binance USDT-M Futures · v1.0.0</p>
        </div>
      </div>
    </aside>
  )
}
