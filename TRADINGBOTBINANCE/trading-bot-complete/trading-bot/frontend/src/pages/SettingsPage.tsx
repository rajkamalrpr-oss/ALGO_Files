import { useState, useEffect } from 'react'
import { Eye, EyeOff, Key, Save, CheckCircle2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'
import { fetchCredentials, saveCredentials } from '../api/client'
import type { CredentialStatus } from '../api/client'

export default function SettingsPage() {
  const [apiKey, setApiKey]       = useState('')
  const [apiSecret, setApiSecret] = useState('')
  const [showSecret, setShowSecret] = useState(false)
  const [saving, setSaving]       = useState(false)
  const [status, setStatus]       = useState<CredentialStatus | null>(null)

  useEffect(() => {
    fetchCredentials().then(setStatus).catch(() => {})
  }, [])

  const handleSave = async () => {
    if (!apiKey.trim() || !apiSecret.trim()) {
      toast.error('Both API Key and Secret are required')
      return
    }
    setSaving(true)
    try {
      const result = await saveCredentials({ api_key: apiKey.trim(), api_secret: apiSecret.trim() })
      setStatus(result)
      setApiKey('')
      setApiSecret('')
      toast.success('Credentials saved successfully')
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? 'Failed to save credentials')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8 max-w-xl animate-fade-up">
      <h1 className="text-2xl font-display font-semibold text-slate-900 mb-1">Settings</h1>
      <p className="text-slate-400 text-sm mb-8">Configure your Binance Futures Testnet API credentials</p>

      {/* Current status */}
      {status && (
        <div className="card mb-6">
          <div className="flex items-center gap-2 mb-3">
            <Key size={14} className="text-accent-cyan" />
            <span className="text-sm font-display font-semibold text-slate-900">API Key Status</span>
          </div>
          <div className="flex items-center gap-2">
            {status.api_key_set ? (
              <>
                <CheckCircle2 size={14} className="text-emerald-600" />
                <span className="text-xs font-display text-emerald-700 font-medium">Configured</span>
                <code className="ml-2 text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md border border-slate-200">
                  {status.api_key_preview}
                </code>
              </>
            ) : (
              <>
                <AlertCircle size={14} className="text-rose-500" />
                <span className="text-xs font-display text-rose-600">Not configured — orders will fail until keys are set</span>
              </>
            )}
          </div>
        </div>
      )}

      {/* Credentials form */}
      <div className="card space-y-5">
        <div>
          <label className="label">API Key</label>
          <input
            type="text"
            className="input font-mono text-xs"
            placeholder="Paste your Binance testnet API key"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <div>
          <label className="label">API Secret</label>
          <div className="relative">
            <input
              type={showSecret ? 'text' : 'password'}
              className="input font-mono text-xs pr-10"
              placeholder="Paste your API secret"
              value={apiSecret}
              onChange={(e) => setApiSecret(e.target.value)}
              autoComplete="new-password"
              spellCheck={false}
            />
            <button
              type="button"
              onClick={() => setShowSecret((v) => !v)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700 transition-colors"
            >
              {showSecret ? <EyeOff size={14} /> : <Eye size={14} />}
            </button>
          </div>
        </div>

        <div className="pt-1 flex items-start gap-4">
          <button
            onClick={handleSave}
            disabled={saving}
            className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-emerald-600 text-white text-sm font-display font-semibold hover:bg-emerald-700 transition-all shadow-sm shadow-glow disabled:opacity-40 shrink-0"
          >
            <Save size={13} />
            {saving ? 'Saving…' : 'Save Credentials'}
          </button>
          <p className="text-[11px] font-display text-slate-400 mt-1 leading-relaxed">
            Saved to backend <code className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-slate-600 border border-slate-200">.env</code> and applied immediately. The full secret is never returned.
          </p>
        </div>
      </div>

      {/* How-to guide */}
      <div className="card mt-6 bg-slate-50 border-slate-200">
        <p className="text-xs font-display font-semibold text-slate-600 mb-3">How to get Binance Testnet keys</p>
        <ol className="text-xs font-display text-slate-400 space-y-2 list-decimal list-inside">
          <li>Go to <span className="text-slate-600 font-medium">testnet.binancefuture.com</span></li>
          <li>Log in (GitHub account works)</li>
          <li>Click <span className="text-slate-600 font-medium">API Key</span> → Generate a new key pair</li>
          <li>Copy both values and paste them above</li>
        </ol>
      </div>
    </div>
  )
}
