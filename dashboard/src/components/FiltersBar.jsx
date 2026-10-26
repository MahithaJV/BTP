export default function FiltersBar({
  filterCity,
  setFilterCity,
  filterCrime,
  setFilterCrime,
  crimeTypes,
}) {
  const cities = ['all', 'Pune', 'Mumbai', 'Thane', 'Nashik', 'Nagpur', 'Other'];

  return (
    <div className="filters-bar">
      <span className="filter-label">Filters:</span>

      <select
        className="filter-select"
        value={filterCity}
        onChange={e => setFilterCity(e.target.value)}
      >
        <option value="all">All Cities</option>
        {cities.slice(1).map(c => (
          <option key={c} value={c}>{c}</option>
        ))}
      </select>

      <select
        className="filter-select"
        value={filterCrime}
        onChange={e => setFilterCrime(e.target.value)}
      >
        <option value="all">All Crime Types</option>
        {crimeTypes.map(t => (
          <option key={t} value={t}>{t}</option>
        ))}
      </select>

      {(filterCity !== 'all' || filterCrime !== 'all') && (
        <button
          className="header-refresh-btn"
          onClick={() => { setFilterCity('all'); setFilterCrime('all'); }}
          style={{ fontSize: '0.78rem', padding: '6px 12px' }}
        >
          ✕ Clear
        </button>
      )}
    </div>
  );
}
