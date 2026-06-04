export default function BackgroundDecor() {
  const nodes = [
    { cx: 700, cy: 110, color: '#F7931A' },
    { cx: 810, cy: 185, color: '#627EEA' },
    { cx: 930, cy: 125, color: '#F3BA2F' },
    { cx: 670, cy: 210, color: '#8B5CF6' },
    { cx: 760, cy: 275, color: '#F7931A' },
    { cx: 870, cy: 260, color: '#627EEA' },
    { cx: 990, cy: 200, color: '#F3BA2F' },
    { cx:1050, cy: 300, color: '#8B5CF6' },
  ]
  const edges = [
    [0,1],[1,2],[3,4],[4,5],[5,6],[1,4],[2,6],[6,7],[5,7],
  ]

  return (
    <div
      className="fixed inset-0 overflow-hidden pointer-events-none select-none"
      style={{ zIndex: 0 }}
      aria-hidden="true"
    >
      <svg
        width="100%" height="100%"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMid slice"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* ── Glow blobs ── */}
          <radialGradient id="glowOrange" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#F7931A" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#F7931A" stopOpacity="0"    />
          </radialGradient>
          <radialGradient id="glowBlue" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#627EEA" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#627EEA" stopOpacity="0"    />
          </radialGradient>
          <radialGradient id="glowGold" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#F3BA2F" stopOpacity="0.18" />
            <stop offset="100%" stopColor="#F3BA2F" stopOpacity="0"    />
          </radialGradient>
          <radialGradient id="glowPurple" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#8B5CF6" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#8B5CF6" stopOpacity="0"    />
          </radialGradient>
          <radialGradient id="glowTeal" cx="50%" cy="50%" r="50%">
            <stop offset="0%"   stopColor="#06B6D4" stopOpacity="0.14" />
            <stop offset="100%" stopColor="#06B6D4" stopOpacity="0"    />
          </radialGradient>

          {/* ── ETH gradient fill ── */}
          <linearGradient id="ethGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stopColor="#8B5CF6" />
            <stop offset="100%" stopColor="#627EEA" />
          </linearGradient>

          {/* ── BTC gradient fill ── */}
          <linearGradient id="btcGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%"   stopColor="#F7931A" />
            <stop offset="100%" stopColor="#FBBF24" />
          </linearGradient>

          {/* ── Hex grid ── */}
          <pattern id="hexGrid" width="60" height="52" patternUnits="userSpaceOnUse">
            <polygon
              points="30,1 59,15 59,37 30,51 1,37 1,15"
              fill="none" stroke="#6366f1" strokeWidth="0.7"
            />
          </pattern>
          <radialGradient id="hexFade" cx="50%" cy="50%" r="60%">
            <stop offset="10%"  stopColor="white" stopOpacity="1"   />
            <stop offset="75%"  stopColor="white" stopOpacity="0.2" />
            <stop offset="100%" stopColor="white" stopOpacity="0"   />
          </radialGradient>
          <mask id="hexMask">
            <rect width="1440" height="900" fill="url(#hexFade)" />
          </mask>
        </defs>

        {/* ══════════════════════════════════
            AURORA GLOW BLOBS
        ══════════════════════════════════ */}
        {/* BTC glow — bottom-left */}
        <ellipse cx="60"  cy="820" rx="420" ry="360" fill="url(#glowOrange)" />
        {/* ETH glow — top-right */}
        <ellipse cx="1380" cy="120" rx="380" ry="320" fill="url(#glowBlue)"   />
        {/* BNB glow — top-center */}
        <ellipse cx="720"  cy="-60" rx="340" ry="280" fill="url(#glowGold)"   />
        {/* Purple accent — bottom-right */}
        <ellipse cx="1400" cy="860" rx="320" ry="260" fill="url(#glowPurple)" />
        {/* Teal accent — left-center */}
        <ellipse cx="-20"  cy="420" rx="280" ry="240" fill="url(#glowTeal)"   />

        {/* ══════════════════════════════════
            HEX GRID (indigo-tinted)
        ══════════════════════════════════ */}
        <rect
          width="1440" height="900"
          fill="url(#hexGrid)"
          opacity="0.2"
          mask="url(#hexMask)"
        />

        {/* ══════════════════════════════════
            BITCOIN  ₿
        ══════════════════════════════════ */}
        {/* Large — bottom-left */}
        <text
          x="-80" y="920"
          fontSize="600"
          fontFamily="Georgia, 'Times New Roman', serif"
          fontWeight="700"
          fill="url(#btcGrad)"
          opacity="0.11"
          transform="rotate(-10, 220, 680)"
        >₿</text>

        {/* Medium — top-right */}
        <text
          x="1060" y="290"
          fontSize="310"
          fontFamily="Georgia, 'Times New Roman', serif"
          fontWeight="700"
          fill="url(#btcGrad)"
          opacity="0.1"
          transform="rotate(12, 1210, 200)"
        >₿</text>

        {/* ══════════════════════════════════
            ETHEREUM  ◆
        ══════════════════════════════════ */}
        {/* Large — left-center */}
        <g transform="translate(10, 260) scale(3.8)" opacity="0.14">
          <polygon points="32,0  0,54 32,74"  fill="url(#ethGrad)" />
          <polygon points="32,0  64,54 32,74" fill="#627EEA" opacity="0.8"  />
          <polygon points="0,54  32,74 32,108" fill="#8B5CF6" opacity="0.55" />
          <polygon points="64,54 32,74 32,108" fill="#627EEA" opacity="0.7"  />
        </g>

        {/* Medium — upper-right */}
        <g transform="translate(1300, 60) scale(2.2)" opacity="0.12">
          <polygon points="32,0  0,54 32,74"  fill="url(#ethGrad)" />
          <polygon points="32,0  64,54 32,74" fill="#627EEA" opacity="0.8"  />
          <polygon points="0,54  32,74 32,108" fill="#8B5CF6" opacity="0.55" />
          <polygon points="64,54 32,74 32,108" fill="#627EEA" opacity="0.7"  />
        </g>

        {/* Small — bottom-right */}
        <g transform="translate(1360, 720) scale(1.6)" opacity="0.1">
          <polygon points="32,0  0,54 32,74"  fill="url(#ethGrad)" />
          <polygon points="32,0  64,54 32,74" fill="#627EEA" opacity="0.8"  />
          <polygon points="0,54  32,74 32,108" fill="#8B5CF6" opacity="0.55" />
          <polygon points="64,54 32,74 32,108" fill="#627EEA" opacity="0.7"  />
        </g>

        {/* ══════════════════════════════════
            BINANCE  ◈  (gold rotated square)
        ══════════════════════════════════ */}
        <g opacity="0.13">
          <rect x="650" y="-55" width="120" height="120" rx="10"
            fill="#F3BA2F" transform="rotate(45, 710, 5)" />
          <rect x="675" y="-30" width="70"  height="70"  rx="6"
            fill="white" opacity="0.4" transform="rotate(45, 710, 5)" />
        </g>
        <g opacity="0.1">
          <rect x="650" y="830" width="100" height="100" rx="8"
            fill="#F3BA2F" transform="rotate(45, 700, 880)" />
          <rect x="672" y="853" width="56"  height="56"  rx="5"
            fill="white" opacity="0.4" transform="rotate(45, 700, 880)" />
        </g>

        {/* ══════════════════════════════════
            COIN RINGS
        ══════════════════════════════════ */}
        <circle cx="195" cy="710" r="155" fill="none" stroke="#F7931A" strokeWidth="2"   opacity="0.18" />
        <circle cx="195" cy="710" r="128" fill="none" stroke="#FBBF24" strokeWidth="1"   opacity="0.12" />
        <circle cx="195" cy="710" r="102" fill="none" stroke="#F7931A" strokeWidth="0.6" opacity="0.08" />

        <circle cx="1265" cy="480" r="115" fill="none" stroke="#627EEA" strokeWidth="2"   opacity="0.16" />
        <circle cx="1265" cy="480" r="90"  fill="none" stroke="#8B5CF6" strokeWidth="1"   opacity="0.12" />
        <circle cx="1265" cy="480" r="66"  fill="none" stroke="#06B6D4" strokeWidth="0.6" opacity="0.08" />

        {/* ══════════════════════════════════
            BLOCKCHAIN NETWORK
        ══════════════════════════════════ */}
        {edges.map(([a, b], i) => (
          <line
            key={`e${i}`}
            x1={nodes[a].cx} y1={nodes[a].cy}
            x2={nodes[b].cx} y2={nodes[b].cy}
            stroke={nodes[a].color} strokeWidth="1.2" opacity="0.25"
          />
        ))}
        {nodes.map((n, i) => (
          <g key={`n${i}`}>
            <circle cx={n.cx} cy={n.cy} r="8"   fill={n.color} opacity="0.08" />
            <circle cx={n.cx} cy={n.cy} r="4"   fill={n.color} opacity="0.35" />
            <circle cx={n.cx} cy={n.cy} r="1.8" fill={n.color} opacity="0.9"  />
          </g>
        ))}
      </svg>
    </div>
  )
}
