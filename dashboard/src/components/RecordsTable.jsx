const VIOLENT_CRIMES = [
  'Murder', 'Attempt to Murder', 'Rape', 'Kidnapping / Abduction',
  'Robbery', 'Assault / Physical Attack', 'Human Trafficking',
];

const FINANCIAL_CRIMES = [
  'Cheating / Fraud', 'Online Financial Fraud', 'Forgery / Document Fraud',
  'Bribery / Corruption',
];

const CYBER_CRIMES = ['Cybercrime', 'Online Financial Fraud'];

function getTagClass(tag) {
  if (VIOLENT_CRIMES.includes(tag)) return 'crime-tag violent';
  if (FINANCIAL_CRIMES.includes(tag)) return 'crime-tag financial';
  if (CYBER_CRIMES.includes(tag)) return 'crime-tag cyber';
  return 'crime-tag';
}

export default function RecordsTable({ records, loading }) {
  if (loading) {
    return (
      <div className="records-table-container">
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <div className="loading-text">Loading FIR records...</div>
        </div>
      </div>
    );
  }

  if (!records || records.length === 0) {
    return (
      <div className="records-table-container">
        <div className="empty-state">
          <div className="empty-state-icon">📋</div>
          <div className="empty-state-title">No Records Found</div>
          <div className="empty-state-desc">
            Run the pipeline to scrape and process FIR data, or adjust your filters.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="section">
      <div className="section-header">
        <div className="section-title">
          📋 FIR Records
          <span className="section-badge">{records.length} records</span>
        </div>
      </div>

      <div className="records-table-container" style={{ maxHeight: '600px', overflowY: 'auto' }}>
        <table className="records-table">
          <thead>
            <tr>
              <th>FIR #</th>
              <th>Date</th>
              <th>Location</th>
              <th>Crime Tags</th>
              <th>Complainant</th>
              <th>Accused</th>
              <th>Coordinates</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r, idx) => (
              <tr key={r.id || idx}>
                <td style={{ fontWeight: 600, color: '#3b82f6' }}>{r.fir_number}</td>
                <td>{r.date || '—'}</td>
                <td style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {r.location}
                </td>
                <td>
                  {r.crime_tags.length > 0 ? (
                    r.crime_tags.map((tag, i) => (
                      <span key={i} className={getTagClass(tag)}>{tag}</span>
                    ))
                  ) : (
                    <span style={{ color: '#64748b', fontSize: '0.78rem' }}>Unclassified</span>
                  )}
                </td>
                <td>{r.complainant}</td>
                <td>{r.accused}</td>
                <td>
                  {r.coordinates ? (
                    <span className="coords-badge">
                      📍 {r.coordinates.lat.toFixed(3)}, {r.coordinates.lng.toFixed(3)}
                    </span>
                  ) : (
                    <span className="coords-badge missing">✕ Not geocoded</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
