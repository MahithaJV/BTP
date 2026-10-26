export default function StatsCards({ totalFirs, geocoded, cities, topCrime }) {
  const cityCount = Object.keys(cities).length;
  const topCrimeName = topCrime ? topCrime.category : '—';
  const topCrimeCount = topCrime ? topCrime.count : 0;

  const cards = [
    {
      label: 'Total FIRs',
      value: totalFirs,
      icon: '📄',
      change: `Across ${cityCount} ${cityCount === 1 ? 'city' : 'cities'}`,
    },
    {
      label: 'Geocoded',
      value: geocoded,
      icon: '📍',
      change: totalFirs > 0
        ? `${((geocoded / totalFirs) * 100).toFixed(0)}% success rate`
        : 'No records yet',
    },
    {
      label: 'Cities Covered',
      value: cityCount,
      icon: '🏙️',
      change: 'Maharashtra state',
    },
    {
      label: 'Top Crime',
      value: topCrimeCount,
      icon: '⚡',
      change: topCrimeName,
    },
  ];

  return (
    <div className="stats-grid">
      {cards.map((card, i) => (
        <div className="stat-card" key={i}>
          <div className="stat-card-header">
            <span className="stat-card-label">{card.label}</span>
            <div className="stat-card-icon">{card.icon}</div>
          </div>
          <div className="stat-card-value">{card.value}</div>
          <div className="stat-card-change">{card.change}</div>
        </div>
      ))}
    </div>
  );
}
