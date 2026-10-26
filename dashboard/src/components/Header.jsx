import { useState, useEffect } from 'react';

const PAGE_TITLES = {
  dashboard: { title: 'Dashboard', subtitle: 'Real-time crime analytics overview' },
  map: { title: 'Crime Map', subtitle: 'Interactive geographic incident visualization' },
  records: { title: 'FIR Records', subtitle: 'Browse all First Information Reports' },
  analytics: { title: 'Analytics', subtitle: 'Crime trends and distribution analysis' },
};

export default function Header({ activePage, lastUpdated, onRefresh, loading }) {
  const [currentTime, setCurrentTime] = useState(new Date());
  const page = PAGE_TITLES[activePage] || PAGE_TITLES.dashboard;

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="header">
      <div className="header-left">
        <div>
          <div className="header-title">{page.title}</div>
          <div className="header-subtitle">{page.subtitle}</div>
        </div>
      </div>

      <div className="header-right">
        {lastUpdated && (
          <span className="header-time">
            Updated: {lastUpdated.toLocaleTimeString('en-IN')}
          </span>
        )}
        <button
          className={`header-refresh-btn ${loading ? 'loading' : ''}`}
          onClick={onRefresh}
          disabled={loading}
        >
          <span className="refresh-icon">🔄</span>
          {loading ? 'Refreshing...' : 'Refresh'}
        </button>
        <span className="header-time">
          {currentTime.toLocaleTimeString('en-IN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
          })}
        </span>
      </div>
    </header>
  );
}
