export default function Sidebar({ activePage, onNavigate, totalRecords, connected }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'map', label: 'Crime Map', icon: '🗺️' },
    { id: 'records', label: 'FIR Records', icon: '📋' },
    { id: 'analytics', label: 'Analytics', icon: '📈' },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">🛡️</div>
        <div className="sidebar-brand-text">
          <h1>Crime Watch</h1>
          <span>Maharashtra FIR Monitor</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Navigation</div>
        {navItems.map(item => (
          <div
            key={item.id}
            className={`sidebar-link ${activePage === item.id ? 'active' : ''}`}
            onClick={() => onNavigate(item.id)}
          >
            <span className="sidebar-link-icon">{item.icon}</span>
            <span>{item.label}</span>
          </div>
        ))}

        <div className="sidebar-section-label" style={{ marginTop: 24 }}>System</div>
        <div className="sidebar-link" style={{ cursor: 'default' }}>
          <span className="sidebar-link-icon">💾</span>
          <span>Records: {totalRecords}</span>
        </div>
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot ${connected ? '' : 'disconnected'}`}></span>
          <span>{connected ? 'Supabase Connected' : 'Disconnected'}</span>
        </div>
      </div>
    </aside>
  );
}
