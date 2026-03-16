import React, { useState } from 'react';

// Constants for Drawing
const SVG_SIZE = 800;
const CX = SVG_SIZE / 2;
const CY = SVG_SIZE / 2;
const R_ZODIAC_OUTER = 380;
const R_ZODIAC_INNER = 340;
const R_HOUSES = 240;
const R_PLANETS = 290;

const ZODIAC_SIGNS = [
  { name: '牡羊', sym: '♈', color: '#ff4d4d' }, // Fire
  { name: '金牛', sym: '♉', color: '#4caf50' }, // Earth
  { name: '雙子', sym: '♊', color: '#ffc107' }, // Air
  { name: '巨蟹', sym: '♋', color: '#2196f3' }, // Water
  { name: '獅子', sym: '♌', color: '#ff9800' }, // Fire
  { name: '處女', sym: '♍', color: '#8bc34a' }, // Earth
  { name: '天秤', sym: '♎', color: '#03a9f4' }, // Air
  { name: '天蠍', sym: '♏', color: '#9c27b0' }, // Water
  { name: '射手', sym: '♐', color: '#f44336' }, // Fire
  { name: '魔羯', sym: '♑', color: '#795548' }, // Earth
  { name: '水瓶', sym: '♒', color: '#00bcd4' }, // Air
  { name: '雙魚', sym: '♓', color: '#3f51b5' }, // Water
];

const PLANET_COLORS = {
  '太陽': '#FFD700', '月亮': '#F8F8FF', '水星': '#00E5FF',
  '金星': '#FF69B4', '火星': '#FF4500', '木星': '#9370DB',
  '土星': '#8B4513', '天王星': '#00FFFF', '海王星': '#4169E1',
  '冥王星': '#800080', '北交點': '#A9A9A9', '南交點': '#A9A9A9'
};

// Utilities
const polarToCartesian = (cx, cy, r, angleDeg) => {
  const angleRad = angleDeg * Math.PI / 180.0;
  return {
    x: cx + (r * Math.cos(angleRad)),
    y: cy + (r * Math.sin(angleRad))
  };
};

const CustomAstroChart = ({ chartData }) => {
  const [tooltip, setTooltip] = useState(null);

  if (!chartData) return null;

  const { asc, cusps, planet_lons, aspects_rows, symbols, positions_rows } = chartData;

  const getVisualAngle = (lon) => {
    let diff = lon - cusps[0];
    let vAngle = 180 - diff;
    return (vAngle + 360) % 360; // Normalize
  };

  // 1. Draw Zodiac Wheel
  const renderZodiac = () => {
    return ZODIAC_SIGNS.map((sign, i) => {
      const startDeg = i * 30; // Aries = 0, Taurus = 30...
      const midDeg = startDeg + 15;
      
      const vStart = getVisualAngle(startDeg);
      const vMid = getVisualAngle(midDeg);
      
      // Calculate text position
      const textPos = polarToCartesian(CX, CY, (R_ZODIAC_OUTER + R_ZODIAC_INNER) / 2, vMid);
      const startPos = polarToCartesian(CX, CY, R_ZODIAC_INNER, vStart);
      const endPosOuter = polarToCartesian(CX, CY, R_ZODIAC_OUTER, vStart);

      return (
        <g key={`zodiac-${i}`}>
          {/* Divider Line */}
          <line
            x1={startPos.x} y1={startPos.y}
            x2={endPosOuter.x} y2={endPosOuter.y}
            stroke="var(--chart-line)"
            strokeWidth="1"
          />
          {/* Sign Text */}
          <text 
            x={textPos.x} y={textPos.y} 
            fill={sign.color}
            fontSize="32"
            fontFamily="sans-serif"
            textAnchor="middle"
            dominantBaseline="central"
            // fix rotation to not use scale(-1, -1) which shifts the origin
            // Since we draw anti-clockwise mathematically, vMid itself is inverted.
            // Using vMid - 90 aligns it tangentially and upright relative to the center.
            transform={`rotate(${vMid - 90}, ${textPos.x}, ${textPos.y})`}
            style={{ textShadow: `0 0 10px ${sign.color}90` }}
          >
            {sign.sym}
          </text>
        </g>
      );
    });
  };

  // 2. Draw Houses
  const renderHouses = () => {
    return cusps.map((cuspDeg, i) => {
      const vDeg = getVisualAngle(cuspDeg);
      const posInner = polarToCartesian(CX, CY, 0, vDeg);
      const posOuter = polarToCartesian(CX, CY, R_ZODIAC_INNER, vDeg);
      
      let vNext = getVisualAngle(cusps[(i + 1) % 12]);
      
      let diff = vNext - vDeg;
      if (diff > 0) diff -= 360; 
      const vMid = (vDeg + diff / 2) % 360;
      const textPos = polarToCartesian(CX, CY, R_HOUSES - 100, vMid);

      const isAngular = i === 0 || i === 3 || i === 6 || i === 9; // ASC, IC, DSC, MC

      return (
        <g key={`house-${i}`}>
          <line
            x1={posInner.x} y1={posInner.y}
            x2={posOuter.x} y2={posOuter.y}
            stroke={isAngular ? "var(--accent-cyan)" : "var(--chart-line)"}
            strokeWidth={isAngular ? "2" : "1"}
            opacity={isAngular ? "1" : "0.5"}
          />
          <text
            x={textPos.x} y={textPos.y}
            fill="var(--text-muted)"
            fontSize="18"
            fontWeight="bold"
            textAnchor="middle"
            dominantBaseline="central"
          >
            {i + 1}
          </text>
        </g>
      );
    });
  };

  // 3. Draw Planets and other points
  const renderPlanets = () => {
    let plList = Object.entries(planet_lons).map(([name, lon]) => {
      const posRow = positions_rows?.find(r => r["行星"] === name);
      const detail = posRow ? `${name} ${posRow["位置"]}` : name;
      return {
        name,
        lon,
        vDeg: getVisualAngle(lon),
        sym: symbols[name] || '',
        color: PLANET_COLORS[name] || 'var(--text-bright)',
        detail
      };
    });

    // Helper to get detail string
    const getPointDetail = (name, defaultDetail) => {
      const posRow = positions_rows?.find(r => r["行星"] === name);
      return posRow ? `${name} ${posRow["位置"]}` : defaultDetail;
    };

    // Add extra celestial points (ASC, MC, Nodes)
    if (chartData.asc !== undefined) plList.push({
      name: '上升', lon: chartData.asc, vDeg: getVisualAngle(chartData.asc),
      sym: 'ASC', color: 'var(--accent-cyan)', detail: getPointDetail('上升', `上升 ASC`)
    });
    if (chartData.mc !== undefined) plList.push({
      name: '天頂', lon: chartData.mc, vDeg: getVisualAngle(chartData.mc),
      sym: 'MC', color: 'var(--text-muted)', detail: getPointDetail('天頂', `天頂 MC`)
    });
    if (chartData.north_node !== undefined) plList.push({
      name: '北交點', lon: chartData.north_node, vDeg: getVisualAngle(chartData.north_node),
      sym: '☊', color: '#A9A9A9', detail: getPointDetail('北交點', `北交點 ☊`)
    });
    if (chartData.south_node !== undefined) plList.push({
      name: '南交點', lon: chartData.south_node, vDeg: getVisualAngle(chartData.south_node),
      sym: '☋', color: '#A9A9A9', detail: getPointDetail('南交點', `南交點 ☋`)
    });

    // Simple 1D repulsion algorithm mapping against angular overlaps
    // to separate clustered planets
    for (let iter = 0; iter < 15; iter++) {
      plList.sort((a, b) => a.vDeg - b.vDeg);
      for (let i = 0; i < plList.length; i++) {
        let curr = plList[i];
        let next = plList[(i + 1) % plList.length];
        
        let diff = next.vDeg - curr.vDeg;
        if (diff < 0) diff += 360;
        
        // If planets are closer than 6 visual degrees, nudge them apart
        if (diff < 6.0 && diff > 0) {
          curr.vDeg = (curr.vDeg - 0.5 + 360) % 360;
          next.vDeg = (next.vDeg + 0.5) % 360;
        }
      }
    }

    return plList.map((pl) => {
      const pos = polarToCartesian(CX, CY, R_PLANETS, pl.vDeg);
      const isTextNode = pl.sym.length > 1;

      return (
        <g 
          key={`planet-${pl.name}`} 
          className="planet-group"
          onMouseEnter={(e) => {
            const rect = e.target.getBoundingClientRect();
            setTooltip({
              text: pl.detail,
              color: pl.color,
              x: pos.x,
              y: pos.y
            });
          }}
          onMouseLeave={() => setTooltip(null)}
        >
          <circle cx={pos.x} cy={pos.y} r="16" fill="var(--bg-deep)" stroke={pl.color} strokeWidth="1" />
          <text
            x={pos.x} y={pos.y}
            fill={pl.color}
            fontSize={isTextNode ? "12" : "18"}
            fontWeight="bold"
            textAnchor="middle"
            dominantBaseline="central"
            style={{ textShadow: `0 0 8px ${pl.color}`, pointerEvents: 'none' }}
          >
            {pl.sym}
          </text>
        </g>
      );
    });
  };

  // 4. Draw Aspects
  const renderAspects = () => {
    if (!aspects_rows) return null;
    
    return aspects_rows.map((aspect, i) => {
      const parts = aspect['組合'].split('-');
      if (parts.length !== 2) return null;
      
      const p1 = parts[0];
      const p2 = parts[1];
      
      const lon1 = planet_lons[p1];
      const lon2 = planet_lons[p2];
      
      if (lon1 === undefined || lon2 === undefined) return null;

      const v1 = getVisualAngle(lon1);
      const v2 = getVisualAngle(lon2);
      
      const pos1 = polarToCartesian(CX, CY, R_PLANETS - 20, v1);
      const pos2 = polarToCartesian(CX, CY, R_PLANETS - 20, v2);

      let color = 'rgba(255,255,255,0.1)';
      let width = 1;
      
      switch (aspect['類型']) {
        case '三合': color = '#00e5ff'; width = 2; break; // Trine (Blue)
        case '六合': color = '#00e5ff'; width = 1; break; // Sextile (Blue)
        case '刑':   color = '#ff4d4d'; width = 2; break; // Square (Red)
        case '對沖': color = '#ff4d4d'; width = 2; break; // Opposition (Red)
        case '合相': return null; // Conjunction, don't draw line
      }

      return (
        <line
          key={`aspect-${i}`}
          x1={pos1.x} y1={pos1.y}
          x2={pos2.x} y2={pos2.y}
          stroke={color}
          strokeWidth={width}
          opacity="0.6"
        />
      );
    });
  };

  return (
    <div className="glass-panel chart-wrapper" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', padding: '1rem', height: '100%', position: 'relative' }}>
      <svg 
        viewBox={`0 0 ${SVG_SIZE} ${SVG_SIZE}`} 
        style={{ width: '100%', height: 'auto', maxWidth: '800px', filter: 'drop-shadow(0 0 20px rgba(0,229,255,0.1))' }}
      >
        <defs>
          <radialGradient id="bgGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(0, 229, 255, 0.05)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
        </defs>

        {/* Background Circles */}
        <circle cx={CX} cy={CY} r={R_ZODIAC_OUTER} fill="var(--chart-bg)" stroke="var(--chart-ring)" strokeWidth="2" />
        <circle cx={CX} cy={CY} r={R_ZODIAC_INNER} fill="url(#bgGlow)" stroke="var(--chart-ring)" strokeWidth="1" />
        
        {/* Render Layers */}
        {renderAspects()}
        {renderHouses()}
        {renderZodiac()}
        {renderPlanets()}
        
        {/* Inner Hub */}
        <circle cx={CX} cy={CY} r="30" fill="var(--bg-deep)" stroke="var(--chart-ring)" strokeWidth="1" />
        <circle cx={CX} cy={CY} r="5" fill="var(--accent-cyan)" />

        {/* Tooltip Overlay Layer */}
        {tooltip && (
          <g transform={`translate(${tooltip.x}, ${tooltip.y - 30})`}>
            <rect 
              x="-80" y="-15" 
              width="160" height="30" 
              rx="8" 
              fill="rgba(10, 15, 30, 0.9)" 
              stroke={tooltip.color}
              strokeWidth="1"
            />
            <text 
              fill="#ffffff" 
              fontSize="12" 
              fontWeight="bold" 
              textAnchor="middle" 
              dominantBaseline="central"
            >
              {tooltip.text}
            </text>
          </g>
        )}
      </svg>

      <style>{`
        .chart-wrapper {
          user-select: none;
        }
        .planet-group circle {
          pointer-events: bounding-box;
          transition: all 0.2s ease;
        }
        .planet-group:hover circle {
          stroke-width: 2;
          filter: drop-shadow(0 0 8px currentColor);
          r: 20;
        }
        .planet-group text {
          pointer-events: none;
        }
      `}</style>
    </div>
  );
};

export default CustomAstroChart;
