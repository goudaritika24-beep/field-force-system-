import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import AIInsights from '../components/AIInsights';

export default function TaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user, hasPermission } = useAuth();
  const [task, setTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [agents, setAgents] = useState([]);
  const [assignTo, setAssignTo] = useState('');
  const [aiInsights, setAiInsights] = useState({});
  const [showVisitModal, setShowVisitModal] = useState(false);
  const [visitLocation, setVisitLocation] = useState('');

  const loadTask = () => {
    setLoading(true);
    api.getTask(id)
      .then(data => {
        setTask(data);
        // Load AI insights for completed visits
        if (data.visits) {
          data.visits.forEach(v => {
            if (v.notes) {
              api.getAIInsights(v.id).then(ai => {
                setAiInsights(prev => ({ ...prev, [v.id]: ai }));
              }).catch(() => {});
            }
          });
        }
      })
      .catch(err => { console.error(err); navigate('/tasks'); })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadTask(); }, [id]);

  useEffect(() => {
    if (hasPermission('tasks', 'assign')) {
      api.getAgents().then(setAgents).catch(() => {});
    }
  }, []);

  const handleAssign = async () => {
    if (!assignTo) return;
    try {
      await api.assignTask(id, parseInt(assignTo));
      loadTask();
      setAssignTo('');
    } catch (err) { alert(err.message); }
  };

  const handleStatusChange = async (newStatus) => {
    try {
      await api.updateTask(id, { status: newStatus });
      loadTask();
    } catch (err) { alert(err.message); }
  };

  const handleCreateVisit = async (e) => {
    e.preventDefault();
    try {
      await api.createVisit({ task_id: parseInt(id), location: visitLocation });
      setShowVisitModal(false);
      setVisitLocation('');
      loadTask();
    } catch (err) { alert(err.message); }
  };

  const handleStartVisit = async (visitId) => {
    try {
      await api.startVisit(visitId);
      loadTask();
    } catch (err) { alert(err.message); }
  };

  const handleCompleteVisit = async (visitId) => {
    const outcome = prompt('Enter outcome (successful, partial, unsuccessful, follow_up_needed):', 'successful');
    if (!outcome) return;
    const notes = prompt('Enter visit notes (optional):');
    try {
      await api.completeVisit(visitId, { outcome, notes: notes || undefined });
      loadTask();
    } catch (err) { alert(err.message); }
  };

  if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;
  if (!task) return null;

  const priorityClass = `priority-badge priority-${task.priority}`;
  const statusClass = `status-badge status-${task.status}`;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <button className="btn btn-ghost" onClick={() => navigate('/tasks')}>← Back to Tasks</button>
          <h1 style={{ marginTop: '8px' }}>{task.title}</h1>
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-main">
          <div className="card">
            <div className="card-header">
              <h3>Task Details</h3>
              <div className="badge-group">
                <span className={priorityClass}>{task.priority}</span>
                <span className={statusClass}>{task.status.replace('_', ' ')}</span>
              </div>
            </div>
            <div className="card-body">
              <p className="detail-description">{task.description || 'No description provided'}</p>
              <div className="detail-meta-grid">
                <div className="detail-meta-item">
                  <span className="meta-label">Created By</span>
                  <span className="meta-value">{task.created_by_username}</span>
                </div>
                <div className="detail-meta-item">
                  <span className="meta-label">Assigned To</span>
                  <span className="meta-value">{task.assigned_to_name || 'Unassigned'}</span>
                </div>
                <div className="detail-meta-item">
                  <span className="meta-label">Team</span>
                  <span className="meta-value">{task.team_name || '—'}</span>
                </div>
                <div className="detail-meta-item">
                  <span className="meta-label">Region</span>
                  <span className="meta-value">{task.region_name || '—'}</span>
                </div>
                <div className="detail-meta-item">
                  <span className="meta-label">Due Date</span>
                  <span className={`meta-value ${task.due_date && new Date(task.due_date) < new Date() && task.status !== 'completed' ? 'overdue' : ''}`}>
                    {task.due_date ? new Date(task.due_date).toLocaleDateString() : '—'}
                  </span>
                </div>
                <div className="detail-meta-item">
                  <span className="meta-label">Created</span>
                  <span className="meta-value">{new Date(task.created_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Visits Section */}
          <div className="card">
            <div className="card-header">
              <h3>📍 Visits ({task.visits?.length || 0})</h3>
              {hasPermission('visits', 'create') && task.assigned_to && (
                <button className="btn btn-sm btn-primary" onClick={() => setShowVisitModal(true)}>+ New Visit</button>
              )}
            </div>
            <div className="card-body">
              {!task.visits || task.visits.length === 0 ? (
                <div className="empty-state">No visits yet</div>
              ) : (
                <div className="visits-list">
                  {task.visits.map(visit => (
                    <div key={visit.id} className="visit-item">
                      <div className="visit-item-header">
                        <div>
                          <span className={`status-badge status-${visit.status}`}>{visit.status.replace('_', ' ')}</span>
                          {visit.outcome && <span className={`outcome-badge outcome-${visit.outcome}`}>{visit.outcome.replace('_', ' ')}</span>}
                        </div>
                        <span className="visit-agent">👤 {visit.agent_name}</span>
                      </div>
                      {visit.location && <div className="visit-location">📍 {visit.location}</div>}
                      {visit.notes && <div className="visit-notes">{visit.notes}</div>}
                      <div className="visit-times">
                        {visit.started_at && <span>Started: {new Date(visit.started_at).toLocaleString()}</span>}
                        {visit.completed_at && <span>Completed: {new Date(visit.completed_at).toLocaleString()}</span>}
                      </div>

                      {/* Visit Actions */}
                      {(user.role === 'Admin' || (user.role === 'Field Agent' && visit.agent_id === user.profileId)) && (
                        <div className="visit-actions">
                          {visit.status === 'scheduled' && (
                            <button className="btn btn-sm btn-success" onClick={() => handleStartVisit(visit.id)}>▶ Start Visit</button>
                          )}
                          {visit.status === 'in_progress' && (
                            <button className="btn btn-sm btn-primary" onClick={() => handleCompleteVisit(visit.id)}>✅ Complete Visit</button>
                          )}
                        </div>
                      )}

                      {/* AI Insights */}
                      {aiInsights[visit.id] && <AIInsights insights={aiInsights[visit.id]} />}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar Actions */}
        <div className="detail-sidebar">
          {hasPermission('tasks', 'assign') && agents.length > 0 && (
            <div className="card">
              <div className="card-header"><h3>Assign Agent</h3></div>
              <div className="card-body">
                <select className="filter-select" value={assignTo} onChange={e => setAssignTo(e.target.value)} style={{ width: '100%', marginBottom: '8px' }}>
                  <option value="">Select Agent</option>
                  {agents.map(a => (
                    <option key={a.id} value={a.id}>{a.full_name} ({a.team_name})</option>
                  ))}
                </select>
                <button className="btn btn-primary btn-full" onClick={handleAssign} disabled={!assignTo}>Assign</button>
              </div>
            </div>
          )}

          {hasPermission('tasks', 'update') && (
            <div className="card">
              <div className="card-header"><h3>Update Status</h3></div>
              <div className="card-body">
                <div className="status-actions">
                  {['pending', 'in_progress', 'completed', 'cancelled'].filter(s => s !== task.status).map(s => (
                    <button key={s} className={`btn btn-sm btn-full status-btn-${s}`} onClick={() => handleStatusChange(s)}>
                      Mark as {s.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {showVisitModal && (
        <div className="modal-overlay" onClick={() => setShowVisitModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create Visit</h2>
              <button className="modal-close" onClick={() => setShowVisitModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreateVisit} className="modal-body">
              <div className="form-group">
                <label>Location</label>
                <input type="text" value={visitLocation} onChange={e => setVisitLocation(e.target.value)} placeholder="Visit location / site name" />
              </div>
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowVisitModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Visit</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
