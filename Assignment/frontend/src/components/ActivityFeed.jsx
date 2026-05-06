export default function ActivityFeed({ activities }) {
  if (!activities || activities.length === 0) {
    return <div className="empty-state">No recent activity</div>;
  }

  const actionIcons = {
    task_created: '📝',
    task_assigned: '👤',
    task_updated: '✏️',
    status_changed: '🔄',
    visit_created: '📍',
    visit_started: '▶️',
    visit_completed: '✅',
    visit_notes_added: '📝',
  };

  const actionLabels = {
    task_created: 'created a task',
    task_assigned: 'assigned a task',
    task_updated: 'updated a task',
    status_changed: 'changed status',
    visit_created: 'created a visit',
    visit_started: 'started a visit',
    visit_completed: 'completed a visit',
    visit_notes_added: 'added visit notes',
  };

  const formatTime = (dateStr) => {
    const date = new Date(dateStr + 'Z');
    const now = new Date();
    const diff = now - date;
    const mins = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="activity-feed">
      {activities.map((activity, i) => {
        let details = {};
        try { details = JSON.parse(activity.details || '{}'); } catch(e) {}

        return (
          <div key={activity.id || i} className="activity-item">
            <div className="activity-icon">
              {actionIcons[activity.action] || '📌'}
            </div>
            <div className="activity-body">
              <div className="activity-text">
                <strong>{activity.full_name || activity.username}</strong>{' '}
                {actionLabels[activity.action] || activity.action}
                {details.title && <span className="activity-detail"> — {details.title}</span>}
                {details.assigned_to && <span className="activity-detail"> to {details.assigned_to}</span>}
                {details.from && details.to && (
                  <span className="activity-detail"> from <em>{details.from}</em> to <em>{details.to}</em></span>
                )}
                {details.outcome && <span className="activity-detail"> ({details.outcome})</span>}
              </div>
              <div className="activity-time">{formatTime(activity.created_at)}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
