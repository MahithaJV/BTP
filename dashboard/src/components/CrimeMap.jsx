import { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Critical for ES modules: expose L on window so plugins like leaflet.heat can attach to it
if (typeof window !== 'undefined') {
  window.L = L;
}

// Fix Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom colored pulsing marker icon
function createColoredIcon(color) {
  return L.divIcon({
    className: 'custom-crime-marker',
    html: `
      <div style="
        position: relative;
        width: 26px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <div style="
          position: absolute;
          width: 26px;
          height: 26px;
          border-radius: 50%;
          background: ${color}45;
          animation: marker-pulse 2s infinite ease-out;
        "></div>
        <div style="
          width: 14px;
          height: 14px;
          background: ${color};
          border: 2px solid #ffffff;
          border-radius: 50%;
          box-shadow: 0 0 10px ${color}, 0 2px 5px rgba(0,0,0,0.6);
        "></div>
      </div>
    `,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  });
}

const SEVERITY_COLORS = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#3b82f6',
};

function getSeverity(tags) {
  const high = ['Murder', 'Attempt to Murder', 'Rape', 'Kidnapping / Abduction', 'Human Trafficking'];
  const medium = ['Robbery', 'Assault / Physical Attack', 'Drug-related Offences', 'Snatching'];
  for (const t of tags) {
    if (high.includes(t)) return 'high';
  }
  for (const t of tags) {
    if (medium.includes(t)) return 'medium';
  }
  return 'low';
}

// ── Heatmap Layer Component ──────────────────────────────────
function HeatmapLayer({ points }) {
  const map = useMap();
  const heatLayerRef = useRef(null);

  useEffect(() => {
    if (!map || !window.L || !window.L.heatLayer) return;

    if (heatLayerRef.current) {
      try {
        map.removeLayer(heatLayerRef.current);
      } catch {
        /* ignore */
      }
      heatLayerRef.current = null;
    }

    if (!points || points.length === 0) return;

    const heatPoints = points.map(p => [p.lat, p.lng, p.intensity || 0.6]);

    try {
      heatLayerRef.current = window.L.heatLayer(heatPoints, {
        radius: 28,
        blur: 20,
        maxZoom: 14,
        max: 1.0,
        gradient: {
          0.2: '#3b82f6',
          0.4: '#10b981',
          0.6: '#f59e0b',
          0.8: '#ef4444',
          1.0: '#ff0055',
        },
      }).addTo(map);
    } catch (e) {
      console.warn('Heatmap layer error:', e);
    }

    return () => {
      if (heatLayerRef.current && map) {
        try {
          map.removeLayer(heatLayerRef.current);
        } catch {
          /* ignore */
        }
        heatLayerRef.current = null;
      }
    };
  }, [map, points]);

  return null;
}

// ── Load Heatmap Plugin ──────────────────────────────────────
function useHeatmapPlugin() {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    window.L = L;

    if (window.L && window.L.heatLayer) {
      setLoaded(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/leaflet.heat@0.2.0/dist/leaflet-heat.js';
    script.onload = () => {
      if (window.L && window.L.heatLayer) {
        setLoaded(true);
      }
    };
    script.onerror = () => console.warn('Could not load leaflet-heat from CDN');
    document.head.appendChild(script);
  }, []);

  return loaded;
}

// ── Auto-fit Map to Incident Bounds ─────────────────────────
function AutoFitBounds({ points }) {
  const map = useMap();
  const fittedRef = useRef(false);

  useEffect(() => {
    if (points && points.length > 0 && !fittedRef.current) {
      const valid = points.filter(p => p.lat && p.lng);
      if (valid.length > 0) {
        const bounds = L.latLngBounds(valid.map(p => [p.lat, p.lng]));
        map.fitBounds(bounds, { padding: [50, 50], maxZoom: 12 });
        fittedRef.current = true;
      }
    }
  }, [map, points]);

  return null;
}

// ── Tile Providers Configuration (100% Free Defaults) ────────
const TILE_PROVIDERS = {
  dark: {
    id: 'dark',
    name: '🌙 Dark Mode',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    className: 'dark-tiles',
    requiresKey: false,
    badge: 'Free (No Key Needed)',
  },
  streets: {
    id: 'streets',
    name: '🗺️ Streets',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    className: '',
    requiresKey: false,
    badge: 'Free OSM',
  },
  satellite: {
    id: 'satellite',
    name: '🛰️ Satellite',
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS',
    className: '',
    requiresKey: false,
    badge: 'Free Esri HD',
  },
  carto: {
    id: 'carto',
    name: '⚡ CARTO Dark',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>',
    className: '',
    requiresKey: true,
    badge: 'Requires Carto Key',
  },
};

// ── Main Crime Map Component ─────────────────────────────────
export default function CrimeMap({ points = [], fullHeight }) {
  const [viewMode, setViewMode] = useState('both'); // Default to 'both' so markers are immediately visible!
  const [tileStyle, setTileStyle] = useState('dark');
  const [cartoKey, setCartoKey] = useState(() => localStorage.getItem('btp_carto_api_key') || '');
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [tempKeyInput, setTempKeyInput] = useState(cartoKey);
  const heatReady = useHeatmapPlugin();

  // Maharashtra center
  const center = [19.0760, 73.8];
  const zoom = 8;

  const currentProvider = TILE_PROVIDERS[tileStyle] || TILE_PROVIDERS.dark;

  // Compute tile URL (attaching API key if CARTO is selected)
  let tileUrl = currentProvider.url;
  if (tileStyle === 'carto' && cartoKey) {
    tileUrl = `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png?api_key=${encodeURIComponent(cartoKey)}`;
  }

  const handleSaveKey = () => {
    const trimmed = tempKeyInput.trim();
    setCartoKey(trimmed);
    if (trimmed) {
      localStorage.setItem('btp_carto_api_key', trimmed);
      setTileStyle('carto');
    } else {
      localStorage.removeItem('btp_carto_api_key');
      setTileStyle('dark');
    }
    setShowKeyModal(false);
  };

  return (
    <div className="map-container" style={fullHeight ? { height: '100%' } : {}}>
      {/* Top Map Controls */}
      <div className="map-controls">
        {/* Style Selector */}
        <div className="map-control-group">
          {Object.values(TILE_PROVIDERS).map(provider => {
            const isKeyRequired = provider.requiresKey && !cartoKey;
            return (
              <button
                key={provider.id}
                className={`map-toggle-btn ${tileStyle === provider.id ? 'active' : ''}`}
                onClick={() => {
                  if (isKeyRequired) {
                    setShowKeyModal(true);
                  } else {
                    setTileStyle(provider.id);
                  }
                }}
                title={provider.badge}
              >
                {provider.name}
              </button>
            );
          })}
        </div>

        {/* View Mode Selector */}
        <div className="map-control-group">
          {[
            { id: 'both', label: '🔥📍 Both' },
            { id: 'markers', label: '📍 Markers' },
            { id: 'heatmap', label: '🔥 Heatmap' },
          ].map(m => (
            <button
              key={m.id}
              className={`map-toggle-btn ${viewMode === m.id ? 'active' : ''}`}
              onClick={() => setViewMode(m.id)}
            >
              {m.label}
            </button>
          ))}
        </div>

        {/* API Key Config Button */}
        <button
          className={`map-toggle-btn map-key-btn ${cartoKey ? 'key-active' : ''}`}
          onClick={() => {
            setTempKeyInput(cartoKey);
            setShowKeyModal(true);
          }}
          title="Configure Map Tile API Key"
        >
          {cartoKey ? '🔑 Key Active' : '🔑 API Key'}
        </button>
      </div>

      {/* Floating Status Indicator */}
      <div className="map-status-pill">
        <span className="map-status-dot"></span>
        <span>
          {currentProvider.requiresKey && !cartoKey
            ? '⚠️ CARTO requires an API key — switch to Dark Mode or Streets for free maps'
            : `${currentProvider.name} • ${points.length} incident points loaded`}
        </span>
      </div>

      {/* Zero Points Notification overlay if filtered out */}
      {points.length === 0 && (
        <div className="map-empty-overlay">
          <span>📍 No incident coordinates match the current filter. Showing Maharashtra base map.</span>
        </div>
      )}

      {/* The Map */}
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          key={`${tileStyle}-${cartoKey}`}
          attribution={currentProvider.attribution}
          url={tileUrl}
          className={currentProvider.className}
        />

        <AutoFitBounds points={points} />

        {heatReady && (viewMode === 'heatmap' || viewMode === 'both') && (
          <HeatmapLayer points={points} />
        )}

        {(viewMode === 'markers' || viewMode === 'both') &&
          points.map((point, idx) => {
            const severity = getSeverity(point.crime_tags || []);
            const color = SEVERITY_COLORS[severity];
            const icon = createColoredIcon(color);

            return (
              <Marker key={`${point.fir_number}-${idx}`} position={[point.lat, point.lng]} icon={icon}>
                <Popup className="crime-popup">
                  <div className="popup-title">
                    <span className="popup-severity-indicator" style={{ background: color }}></span>
                    FIR #{point.fir_number}
                  </div>
                  <div className="popup-row">
                    <span className="popup-label">📍 Location:</span>
                    <span className="popup-value">{point.location}</span>
                  </div>
                  <div className="popup-row">
                    <span className="popup-label">📅 Date:</span>
                    <span className="popup-value">{point.date || 'N/A'}</span>
                  </div>
                  <div className="popup-row">
                    <span className="popup-label">⚖️ Crime:</span>
                    <span className="popup-value">
                      {(point.crime_tags || []).join(', ') || 'Unclassified'}
                    </span>
                  </div>
                  <div className="popup-row">
                    <span className="popup-label">🌐 Coords:</span>
                    <span className="popup-value">
                      {point.lat.toFixed(4)}, {point.lng.toFixed(4)}
                    </span>
                  </div>
                </Popup>
              </Marker>
            );
          })}
      </MapContainer>

      {/* API Key Modal */}
      {showKeyModal && (
        <div className="map-key-modal-overlay" onClick={() => setShowKeyModal(false)}>
          <div className="map-key-modal" onClick={e => e.stopPropagation()}>
            <div className="map-key-modal-header">
              <h3>🔑 Map Tile Provider & API Key</h3>
              <button className="map-key-modal-close" onClick={() => setShowKeyModal(false)}>✕</button>
            </div>

            <div className="map-key-modal-body">
              <div className="key-info-box">
                <div className="key-info-title">✨ Good news: No API key is required!</div>
                <div className="key-info-desc">
                  The dashboard provides <strong>Free Dark Mode</strong>, <strong>OpenStreetMap</strong>, and <strong>Esri Satellite</strong> completely free without any watermark or API key.
                </div>
              </div>

              <div className="key-input-section">
                <label className="key-input-label">
                  Optional: CARTO Basemaps API Key
                  <span className="key-input-subtext">(Enter only if you want to use official CARTO tiles)</span>
                </label>
                <input
                  type="text"
                  className="key-text-input"
                  placeholder="e.g. your_carto_api_key_here..."
                  value={tempKeyInput}
                  onChange={e => setTempKeyInput(e.target.value)}
                />
              </div>

              <div className="key-modal-actions">
                {cartoKey && (
                  <button
                    className="key-clear-btn"
                    onClick={() => {
                      setTempKeyInput('');
                      setCartoKey('');
                      localStorage.removeItem('btp_carto_api_key');
                      setTileStyle('dark');
                      setShowKeyModal(false);
                    }}
                  >
                    Remove Key (Use Free Mode)
                  </button>
                )}
                <button className="key-save-btn" onClick={handleSaveKey}>
                  {tempKeyInput.trim() ? 'Save & Use CARTO Key' : 'Close (Use Free Provider)'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
