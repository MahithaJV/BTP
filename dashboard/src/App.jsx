import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from './supabaseClient';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import StatsCards from './components/StatsCards';
import CrimeMap from './components/CrimeMap';
import CrimeTrend from './components/CrimeTrend';
import CrimeDistribution from './components/CrimeDistribution';
import RecordsTable from './components/RecordsTable';
import FiltersBar from './components/FiltersBar';
import './index.css';

// ── Helpers ───────────────────────────────────────────────────
function parseCrimeTags(raw) {
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    try {
      const p = JSON.parse(raw);
      if (Array.isArray(p)) return p;
    } catch { /* ignore */ }
    return raw.split(',').map(s => s.trim()).filter(Boolean);
  }
  return [];
}

const CITY_CENTROIDS = {
  pune: { lat: 18.5204, lng: 73.8567 },
  mumbai: { lat: 19.0760, lng: 72.8777 },
  thane: { lat: 19.2183, lng: 72.9781 },
  nashik: { lat: 19.9975, lng: 73.7898 },
  nagpur: { lat: 21.1458, lng: 79.0882 },
  dadar: { lat: 19.0178, lng: 72.8478 },
  sitabuldi: { lat: 21.1466, lng: 79.0806 },
  shivajinagar: { lat: 18.5314, lng: 73.8446 },
};

function parseCoords(raw, location = '') {
  if (raw) {
    if (typeof raw === 'string') {
      try { raw = JSON.parse(raw); } catch { raw = null; }
    }
    if (raw && raw.lat && raw.lng) {
      return { lat: parseFloat(raw.lat), lng: parseFloat(raw.lng) };
    }
  }

  // Fallback to city centroid if coordinates are null
  const loc = (location || '').toLowerCase();
  for (const [place, coords] of Object.entries(CITY_CENTROIDS)) {
    if (loc.includes(place)) {
      const hash = loc.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      const jitterLat = ((hash % 100) / 100 - 0.5) * 0.02;
      const jitterLng = (((hash * 7) % 100) / 100 - 0.5) * 0.02;
      return {
        lat: Number((coords.lat + jitterLat).toFixed(6)),
        lng: Number((coords.lng + jitterLng).toFixed(6)),
      };
    }
  }
  return null;
}

function normalizeRecord(r) {
  return {
    id: r.id,
    fir_number: r.fir_number || 'Unknown',
    date: r.date || '',
    location: r.location || 'Unknown',
    description: r.description || '',
    complainant: r.complainant || 'Anonymous',
    accused: r.accused || 'Unknown',
    crime_tags: parseCrimeTags(r.crime_tags),
    coordinates: parseCoords(r.coordinates, r.location),
    created_at: r.created_at || '',
  };
}

function detectCity(location) {
  const loc = (location || '').toLowerCase();
  for (const city of ['Pune', 'Mumbai', 'Thane', 'Nashik', 'Nagpur']) {
    if (loc.includes(city.toLowerCase())) return city;
  }
  return 'Other';
}

// ── Main App ──────────────────────────────────────────────────
export default function App() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dbConnected, setDbConnected] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [activePage, setActivePage] = useState('dashboard');

  // Filters
  const [filterCity, setFilterCity] = useState('all');
  const [filterCrime, setFilterCrime] = useState('all');

  const recordsRef = useRef(records);
  recordsRef.current = records;

  // ── Fetch all records from Supabase ──────────────────────
  const fetchRecords = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const { data, error: fetchError } = await supabase
        .from('fir_records')
        .select('*')
        .order('created_at', { ascending: false });

      if (fetchError) throw fetchError;

      const normalized = (data || []).map(normalizeRecord);
      setRecords(normalized);
      setDbConnected(true);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err.message || 'Failed to fetch records');
      setDbConnected(false);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Initial load + real-time subscription ────────────────
  useEffect(() => {
    fetchRecords();

    // Subscribe to real-time INSERT events
    const channel = supabase
      .channel('fir-realtime')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'fir_records' },
        (payload) => {
          const newRecord = normalizeRecord(payload.new);
          setRecords(prev => [newRecord, ...prev]);
          setLastUpdated(new Date());
        }
      )
      .subscribe();

    // Auto-refresh every 60 seconds to catch any missed updates
    const interval = setInterval(fetchRecords, 60000);

    return () => {
      supabase.removeChannel(channel);
      clearInterval(interval);
    };
  }, [fetchRecords]);

  // ── Compute filtered records ─────────────────────────────
  const filteredRecords = records.filter(r => {
    if (filterCity !== 'all') {
      if (detectCity(r.location) !== filterCity) return false;
    }
    if (filterCrime !== 'all') {
      if (!r.crime_tags.includes(filterCrime)) return false;
    }
    return true;
  });

  // ── Compute statistics ───────────────────────────────────
  const stats = {
    totalFirs: filteredRecords.length,
    geocoded: filteredRecords.filter(r => r.coordinates).length,
    cities: {},
    crimeDistribution: {},
    trend: {},
  };

  filteredRecords.forEach(r => {
    const city = detectCity(r.location);
    stats.cities[city] = (stats.cities[city] || 0) + 1;

    r.crime_tags.forEach(tag => {
      stats.crimeDistribution[tag] = (stats.crimeDistribution[tag] || 0) + 1;
    });

    const dateKey = r.date || (r.created_at ? r.created_at.split('T')[0] : '');
    if (dateKey) {
      stats.trend[dateKey] = (stats.trend[dateKey] || 0) + 1;
    }
  });

  // Get unique crime types for filter
  const allCrimeTypes = [...new Set(records.flatMap(r => r.crime_tags))].sort();

  // Heatmap points
  const heatmapPoints = filteredRecords
    .filter(r => r.coordinates)
    .map(r => ({
      lat: r.coordinates.lat,
      lng: r.coordinates.lng,
      intensity: r.crime_tags.some(t =>
        ['Murder', 'Attempt to Murder', 'Rape', 'Kidnapping / Abduction', 'Robbery'].includes(t)
      ) ? 0.9 : 0.5,
      fir_number: r.fir_number,
      location: r.location,
      crime_tags: r.crime_tags,
      date: r.date,
    }));

  // Trend data sorted by date
  const trendData = Object.entries(stats.trend)
    .map(([date, count]) => ({ date, count }))
    .sort((a, b) => a.date.localeCompare(b.date));

  // Crime distribution data sorted by count
  const crimeDistData = Object.entries(stats.crimeDistribution)
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count);

  // City distribution data
  const cityDistData = Object.entries(stats.cities)
    .map(([city, count]) => ({ city, count }))
    .sort((a, b) => b.count - a.count);

  return (
    <div className="app-layout">
      <Sidebar
        activePage={activePage}
        onNavigate={setActivePage}
        totalRecords={records.length}
        connected={dbConnected}
      />

      <div className="main-content">
        <Header
          activePage={activePage}
          lastUpdated={lastUpdated}
          onRefresh={fetchRecords}
          loading={loading}
        />

        <div className="page-content">
          {error && (
            <div className="error-banner">
              <span>⚠️</span>
              <span className="error-banner-text">{error}</span>
            </div>
          )}

          {activePage === 'dashboard' && (
            <>
              <div className="auto-refresh-bar">
                <span className="pulse"></span>
                <span>Live data — auto-refreshes every 60s. New FIR entries appear automatically via Supabase Realtime.</span>
              </div>

              <StatsCards
                totalFirs={stats.totalFirs}
                geocoded={stats.geocoded}
                cities={stats.cities}
                topCrime={crimeDistData[0]}
              />

              <FiltersBar
                filterCity={filterCity}
                setFilterCity={setFilterCity}
                filterCrime={filterCrime}
                setFilterCrime={setFilterCrime}
                crimeTypes={allCrimeTypes}
              />

              <div className="section">
                <div className="section-header">
                  <div className="section-title">
                    🗺️ Incident Map
                    <span className="section-badge">{heatmapPoints.length} geocoded</span>
                  </div>
                </div>
                <CrimeMap points={heatmapPoints} />
              </div>

              <div className="charts-grid">
                <CrimeTrend data={trendData} />
                <CrimeDistribution data={crimeDistData} />
              </div>

              {cityDistData.length > 0 && (
                <div className="section">
                  <div className="section-header">
                    <div className="section-title">🏙️ City-wise Distribution</div>
                  </div>
                  <div className="stats-grid">
                    {cityDistData.map(({ city, count }) => (
                      <div className="stat-card" key={city} style={{ cursor: 'pointer' }}
                        onClick={() => setFilterCity(city === filterCity ? 'all' : city)}>
                        <div className="stat-card-label">{city}</div>
                        <div className="stat-card-value">{count}</div>
                        <div className="stat-card-change">
                          {((count / stats.totalFirs) * 100).toFixed(1)}% of total FIRs
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

          {activePage === 'records' && (
            <>
              <FiltersBar
                filterCity={filterCity}
                setFilterCity={setFilterCity}
                filterCrime={filterCrime}
                setFilterCrime={setFilterCrime}
                crimeTypes={allCrimeTypes}
              />
              <RecordsTable records={filteredRecords} loading={loading} />
            </>
          )}

          {activePage === 'map' && (
            <div className="section">
              <div className="section-header">
                <div className="section-title">
                  🗺️ Full Crime Map
                  <span className="section-badge">{heatmapPoints.length} points</span>
                </div>
              </div>
              <FiltersBar
                filterCity={filterCity}
                setFilterCity={setFilterCity}
                filterCrime={filterCrime}
                setFilterCrime={setFilterCrime}
                crimeTypes={allCrimeTypes}
              />
              <div style={{ height: 'calc(100vh - 220px)' }}>
                <CrimeMap points={heatmapPoints} fullHeight />
              </div>
            </div>
          )}

          {activePage === 'analytics' && (
            <>
              <div className="charts-grid">
                <CrimeTrend data={trendData} />
                <CrimeDistribution data={crimeDistData} />
              </div>
              <div className="charts-grid" style={{ marginTop: 20 }}>
                <div className="chart-card">
                  <div className="chart-card-header">
                    <h3 className="chart-card-title">🏙️ FIRs by City</h3>
                  </div>
                  <CrimeDistribution
                    data={cityDistData.map(d => ({ category: d.city, count: d.count }))}
                    colorScheme="cities"
                  />
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
