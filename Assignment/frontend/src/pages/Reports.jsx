import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Reports() {
  const [activeReport, setActiveReport] = useState('tasks-by-region');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const reports = [
    { id: 'tasks-by-region', label: '📊 Tasks by Region', icon: '🌍' },
    { id: 'agent-performance', label: '⚡ Agent Performance', icon: '👤' },
    { id: 'recent-visits', label: '📅 Recent Visits (7 Days)', icon: '📍' },
    { id: 'task-status-distribution', label: '📈 Status Distribution', icon: '📋' },
  ];

  useEffect(() => {
    setLoading(true);
    setData(null);
    const fetchers = {
      'tasks-by-region': api.getTasksByRegion,
      'agent-performance': api.getAgentPerformance,
      'recent-visits': api.getRecentVisits,
      'task-status-distribution': api.getTaskStatusDist,
    };
    fetchers[activeReport]()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [activeReport]);

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Reports</h1>
          <p className="page-subtitle">Analytics and insights from field operations</p>
        </div>
      </div>

      <div className="report-tabs">
        {reports.map(r => (
          <button
            key={r.id}
            className={`report-tab ${activeReport === r.id ? 'active' : ''}`}
            onClick={() => setActiveReport(r.id)}
          >
            {r.label}
          </button>
        ))}
      </div>

      <div className="card">
        <div className="card-header">
          <h3>{data?.report || 'Loading...'}</h3>
        </div>
        <div className="card-body">
          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : !data || !data.data || data.data.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📊</div>
              <h3>No data available</h3>
              <p>The report has no matching records.</p>
            </div>
          ) : (
            <>
              {/* Summary section for recent-visits */}
              {data.summary && (
                <div className="report-summary">
                  <div className="summary-stat">
                    <span className="summary-value">{data.summary.total_completed}</span>
                    <span className="summary-label">Total Completed</span>
                  </div>
                  <div className="summary-stat">
                    <span className="summary-value">{data.summary.agents_active}</span>
                    <span className="summary-label">Agents Active</span>
                  </div>
                  <div className="summary-stat">
                    <span className="summary-value">{data.summary.avg_visit_duration_days || '—'}</span>
                    <span className="summary-label">Avg Duration (days)</span>
                  </div>
                </div>
              )}

              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      {Object.keys(data.data[0]).map(key => (
                        <th key={key}>{key.replace(/_/g, ' ')}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {data.data.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((val, j) => (
                          <td key={j}>
                            {typeof val === 'number' ? (
                              <span className="number-cell">{val}</span>
                            ) : val || '—'}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
