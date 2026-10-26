import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts';

const CHART_COLORS = [
  '#3b82f6', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
  '#ef4444', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
  '#a855f7', '#0ea5e9', '#22c55e', '#eab308', '#e11d48',
];

const CITY_COLORS = {
  Pune: '#3b82f6',
  Mumbai: '#ef4444',
  Thane: '#10b981',
  Nashik: '#f59e0b',
  Nagpur: '#8b5cf6',
  Other: '#64748b',
};

function CustomTooltip({ active, payload }) {
  if (!active || !payload || !payload.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: '#1a2035',
      border: '1px solid rgba(99,115,171,0.2)',
      borderRadius: 8,
      padding: '10px 14px',
      fontFamily: 'Inter, sans-serif',
    }}>
      <p style={{ color: '#e2e8f0', fontSize: '0.82rem', fontWeight: 600, margin: 0 }}>
        {d.category}
      </p>
      <p style={{ color: '#3b82f6', fontSize: '1rem', fontWeight: 700, margin: '4px 0 0' }}>
        {d.count} incident{d.count !== 1 ? 's' : ''}
      </p>
    </div>
  );
}

export default function CrimeDistribution({ data, colorScheme }) {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-card-header">
          <h3 className="chart-card-title">🥧 Crime Distribution</h3>
        </div>
        <div className="loading-container" style={{ padding: 40 }}>
          <div className="empty-state-icon">🥧</div>
          <div className="empty-state-desc">No distribution data yet</div>
        </div>
      </div>
    );
  }

  // Shorten long category names for the chart axis
  const chartData = data.slice(0, 12).map(d => ({
    ...d,
    shortName: d.category.length > 20
      ? d.category.split(' / ')[0].substring(0, 18) + '…'
      : d.category,
  }));

  return (
    <div className="chart-card">
      <div className="chart-card-header">
        <h3 className="chart-card-title">
          {colorScheme === 'cities' ? '🏙️ FIRs by City' : '🥧 Crime Distribution'}
        </h3>
        <span className="section-badge">{data.length} categories</span>
      </div>
      <div className="chart-wrapper">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="rgba(99,115,171,0.1)"
              horizontal={false}
            />
            <XAxis
              type="number"
              stroke="#64748b"
              fontSize={11}
              tick={{ fill: '#64748b' }}
              axisLine={{ stroke: 'rgba(99,115,171,0.15)' }}
              allowDecimals={false}
            />
            <YAxis
              type="category"
              dataKey="shortName"
              stroke="#64748b"
              fontSize={11}
              tick={{ fill: '#94a3b8' }}
              axisLine={{ stroke: 'rgba(99,115,171,0.15)' }}
              width={130}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(59,130,246,0.06)' }} />
            <Bar dataKey="count" radius={[0, 4, 4, 0]} animationDuration={600}>
              {chartData.map((entry, idx) => {
                const color = colorScheme === 'cities'
                  ? (CITY_COLORS[entry.category] || CHART_COLORS[idx % CHART_COLORS.length])
                  : CHART_COLORS[idx % CHART_COLORS.length];
                return <Cell key={idx} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
