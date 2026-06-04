import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Sidebar from './components/Sidebar'
import BackgroundDecor from './components/BackgroundDecor'
import DashboardPage from './pages/DashboardPage'
import TradePage from './pages/TradePage'
import OrdersPage from './pages/OrdersPage'
import AccountPage from './pages/AccountPage'
import AnalyticsPage from './pages/AnalyticsPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#ffffff',
            color: '#0f172a',
            border: '1px solid #e2e8f0',
            fontFamily: 'DM Sans, sans-serif',
            fontSize: '13px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
            borderRadius: '10px',
          },
          success: { iconTheme: { primary: '#059669', secondary: '#fff' } },
          error:   { iconTheme: { primary: '#e11d48', secondary: '#fff' } },
        }}
      />
      <BackgroundDecor />
      <div className="relative flex min-h-screen" style={{ zIndex: 1 }}>
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/"          element={<DashboardPage />} />
            <Route path="/trade"     element={<TradePage />} />
            <Route path="/orders"    element={<OrdersPage />} />
            <Route path="/account"   element={<AccountPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/settings"  element={<SettingsPage />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
