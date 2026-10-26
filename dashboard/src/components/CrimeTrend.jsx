import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div style={{
      background: '#1a2035',
      border: '1px solid rgba(99,115,171,0.2)',
      borderRadius: 8,
      padding: '10px 14px',
      fontFamily: 'Inter, sans-serif',
    }}>
      <p style={{ color: '#94a3b8', fontSize: '0.75rem', margin: 0 }}>{label}</p>
      <p style={{ color: '#3b82f6', fontSize: '1rem', fontWeight: 700, margin: '4px 0 0' }}>
        {payload[0].value} FIR{payload[0].value !== 1 ? 's' : ''}
      </p>
    </div>
  );
}

export default function CrimeTrend({ data }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-card-header">
          <h3 className="chart-card-title">📈 Crime Frequency Trend</h3>
        </div>
        <div className="loading-container" style={{ padding: 40 }}>
          <div className="empty-state-icon">📈</div>
          <div className="empty-state-desc">No trend data available yet</div>
        </div>
      </div>
    );
  }

  // Format dates for display
  const formatted = data.map(d => ({
    ...d,
    label: (() => {
      try {
        const dt = new Date(d.date);
        return dt.toLocaleDateString('en-IN', { day: '2-digit', month: 'short' });
      } catch {
        return d.date;
      }
    })(),
  }));

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3 className="chart-card-title">📈 Crime Frequency Trend</h3>
        <span className="section-badge">{data.length} days</span>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formatted} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <defs>
              <linearGradient id="colorFir" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(99,115,171,0.1)"
              vertical={false}
            />
            <XAxis
              dataKey="label"
              stroke="#64748b"
              fontSize={11}
              tick={{ fill: '#64748b' }}
              axisLine={{ stroke: 'rgba(99,115,171,0.15)' }}
            />
            <YAxis
              stroke="#64748b"
              fontSize={11}
              tick={{ fill: '#64748b' }}
              axisLine={{ stroke: 'rgba(99,115,171,0.15)' }}
              allowDecimals={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#3b82f6"
              strokeWidth={2}
              fill="url(#colorFir)"
              animationDuration={800}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
