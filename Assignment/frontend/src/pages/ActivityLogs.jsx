import { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function ActivityLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [pagination, setPagination] = useState({});
  const [filters, setFilters] = useState({ action: '', entity_type: '', page: 1 });

  useEffect(() => {
    setLoading(true);
    const params = { limit: 20 };
    if (filters.action) params.action = filters.action;
    if (filters.entity_type) params.entity_type = filters.entity_type;
    params.page = filters.page;

    api.getActivityLogs(params)
      .then(data => {
        setLogs(data.logs);
        setPagination(data.pagination);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [filters]);

  const actionIcons = {
    task_created: '📝', task_assigned: '👤', task_updated: '✏️',
    status_changed: '🔄', visit_created: '📍', visit_started: '▶️',
    visit_completed: '✅', visit_notes_added: '📝',
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Activity Logs</h1>
          <p className="page-subtitle">Complete audit trail of all system actions</p>
        </div>
      </div>

      <div className="filters-bar">
        <select
          value={filters.action}
          onChange={(e) => setFilters(f => ({ ...f, action: e.target.value, page: 1 }))}
          className="filter-select"
        >
          <option value="">All Actions</option>
          <option value="task_created">Task Created</option>
          <option value="task_assigned">Task Assigned</option>
          <option value="status_changed">Status Changed</option>
          <option value="visit_started">Visit Started</option>
          <option value="visit_completed">Visit Completed</option>
          <option value="visit_notes_added">Notes Added</option>
        </select>
        <select
          value={filters.entity_type}
          onChange={(e) => setFilters(f => ({ ...f, entity_type: e.target.value, page: 1 }))}
          className="filter-select"
        >
          <option value="">All Entities</option>
          <option value="task">Tasks</option>
          <option value="visit">Visits</option>
        </select>
      </div>

      <div className="card">
        <div className="card-body">
          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : logs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📜</div>
              <h3>No logs found</h3>
            </div>
          ) : (
            <>
              <div className="table-wrapper">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Time</th>
                      <th>User</th>
                      <th>Role</th>
                      <th>Action</th>
                      <th>Entity</th>
                      <th>Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {logs.map(log => {
                      let details = {};
                      try { details = JSON.parse(log.details || '{}'); } catch(e) {}
                      return (
                        <tr key={log.id}>
                          <td>{new Date(log.created_at + 'Z').toLocaleString()}</td>
                          <td>
                            <strong>{log.full_name || log.username}</strong>
                          </td>
                          <td><span className="role-badge">{log.user_role}</span></td>
                          <td>
                            <span className="action-badge">
                              {actionIcons[log.action] || '📌'} {log.action.replace(/_/g, ' ')}
                            </span>
                          </td>
                          <td>{log.entity_type} #{log.entity_id}</td>
                          <td className="details-cell">
                            {details.title && <span>{details.title}</span>}
                            {details.assigned_to && <span>→ {details.assigned_to}</span>}
                            {details.from && <span>{details.from} → {details.to}</span>}
                            {details.outcome && <span>Outcome: {details.outcome}</span>}
                            {details.location && <span>📍 {details.location}</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>

              {pagination.totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="btn btn-sm btn-secondary"
                    disabled={pagination.page <= 1}
                    onClick={() => setFilters(f => ({ ...f, page: f.page - 1 }))}
                  >
                    ← Prev
                  </button>
                  <span className="page-info">
                    Page {pagination.page} of {pagination.totalPages} ({pagination.total} total)
                  </span>
                  <button
                    className="btn btn-sm btn-secondary"
                    disabled={pagination.page >= pagination.totalPages}
                    onClick={() => setFilters(f => ({ ...f, page: f.page + 1 }))}
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
