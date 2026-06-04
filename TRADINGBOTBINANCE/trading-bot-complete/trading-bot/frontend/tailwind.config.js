/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"DM Mono"', 'monospace'],
        body:    ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        surface: {
          DEFAULT: '#f8fafc',
          1: '#ffffff',
          2: '#f1f5f9',
          3: '#e8edf3',
        },
        accent: {
          green:  '#059669',
          red:    '#e11d48',
          yellow: '#d97706',
          blue:   '#4f46e5',
          cyan:   '#0284c7',
        },
        border: '#e2e8f0',
      },
      boxShadow: {
        card:      '0 1px 3px rgba(0,0,0,0.07), 0 1px 2px rgba(0,0,0,0.04)',
        'card-md': '0 4px 12px rgba(0,0,0,0.08), 0 1px 3px rgba(0,0,0,0.04)',
        glow:      '0 0 16px rgba(5,150,105,0.18)',
        'glow-red':'0 0 16px rgba(225,29,72,0.18)',
      },
    },
  },
  plugins: [],
}
