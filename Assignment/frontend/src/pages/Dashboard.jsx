import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import ActivityFeed from '../components/ActivityFeed';

export default function Dashboard() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;
  if (!data) return <div className="error-message">Failed to load dashboard</div>;

  const statCards = [
    { label: 'Total Tasks', value: data.tasks.total, icon: '📝', color: 'var(--color-primary)' },
    { label: 'In Progress', value: data.tasks.in_progress, icon: '🔄', color: 'var(--color-warning)' },
    { label: 'Completed', value: data.tasks.completed, icon: '✅', color: 'var(--color-success)' },
    { label: 'Critical Active', value: data.tasks.critical_active, icon: '🚨', color: 'var(--color-danger)' },
    { label: 'Total Visits', value: data.visits.total, icon: '📍', color: 'var(--color-info)' },
    { label: 'Overdue Tasks', value: data.overdueTasks, icon: '⏰', color: data.overdueTasks > 0 ? 'var(--color-danger)' : 'var(--color-success)' },
  ];

  const priorityColors = {
    critical: 'var(--color-danger)',
    high: 'var(--color-warning)',
    medium: 'var(--color-info)',
    low: 'var(--color-success)'
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Welcome back, {user?.fullName || user?.username}</p>
        </div>
        <div className="header-badge">
          {user?.role} {user?.regionName ? `• ${user.regionName}` : ''} {user?.teamName ? `• ${user.teamName}` : ''}
        </div>
      </div>

      <div className="stats-grid">
        {statCards.map((card, i) => (
          <div key={i} className="stat-card" style={{ '--accent': card.color }}>
            <div className="stat-icon">{card.icon}</div>
            <div className="stat-body">
              <div className="stat-value">{card.value}</div>
              <div className="stat-label">{card.label}</div>
            </div>
          </div>
        ))}
      </div>

      <div className="dashboard-grid">
        <div className="card">
          <div className="card-header">
            <h3>📊 Task Status Overview</h3>
          </div>
          <div className="card-body">
            <div className="status-bars">
              {['pending', 'assigned', 'in_progress', 'completed', 'cancelled'].map(status => {
                const count = data.tasks[status] || 0;
                const pct = data.tasks.total > 0 ? (count / data.tasks.total) * 100 : 0;
                return (
                  <div key={status} className="status-bar-row">
                    <span className="status-bar-label">{status.replace('_', ' ')}</span>
                    <div className="status-bar-track">
                      <div 
                        className="status-bar-fill" 
                        style={{ 
                          width: `${pct}%`,
                          backgroundColor: status === 'completed' ? 'var(--color-success)' : 
                            status === 'in_progress' ? 'var(--color-warning)' :
                            status === 'cancelled' ? 'var(--color-muted)' :
                            'var(--color-primary)'
                        }}
                      ></div>
                    </div>
                    <span className="status-bar-count">{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>🎯 Active Priority Distribution</h3>
          </div>
          <div className="card-body">
            {data.priorityDistribution.length > 0 ? (
              <div className="priority-chips">
                {data.priorityDistribution.map(p => (
                  <div key={p.priority} className="priority-chip" style={{ '--chip-color': priorityColors[p.priority] }}>
                    <span className="chip-label">{p.priority}</span>
                    <span className="chip-count">{p.count}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">No active tasks</div>
            )}

            <div className="visit-stats-mini">
              <h4>📍 Visit Status</h4>
              <div className="visit-stats-row">
                <div className="visit-stat"><span className="dot scheduled"></span> Scheduled: {data.visits.scheduled}</div>
                <div className="visit-stat"><span className="dot in-progress"></span> In Progress: {data.visits.in_progress}</div>
                <div className="visit-stat"><span className="dot completed"></span> Completed: {data.visits.completed}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="card card-full">
          <div className="card-header">
            <h3>🕐 Recent Activity</h3>
          </div>
          <div className="card-body">
            <ActivityFeed activities={data.recentActivity} />
          </div>
        </div>
      </div>
    </div>
  );
}
