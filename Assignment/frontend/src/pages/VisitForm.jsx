import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import AIInsights from '../components/AIInsights';

export default function VisitForm() {
  const { user } = useAuth();
  const [visits, setVisits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [notes, setNotes] = useState('');
  const [aiInsights, setAiInsights] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [filters, setFilters] = useState({ status: '' });

  const loadVisits = () => {
    setLoading(true);
    const params = {};
    if (filters.status) params.status = filters.status;
    api.getVisits(params)
      .then(data => setVisits(data.visits))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadVisits(); }, [filters]);

  const handleStartVisit = async (visitId) => {
    try {
      await api.startVisit(visitId);
      loadVisits();
    } catch (err) { alert(err.message); }
  };

  const handleCompleteVisit = async (visitId) => {
    const outcome = prompt('Enter outcome (successful, partial, unsuccessful, follow_up_needed):', 'successful');
    if (!outcome) return;
    try {
      await api.completeVisit(visitId, { outcome, notes: notes || undefined });
      setSelectedVisit(null);
      setNotes('');
      setAiInsights(null);
      loadVisits();
    } catch (err) { alert(err.message); }
  };

  const handleSubmitNotes = async (visitId) => {
    if (!notes.trim()) return alert('Please enter visit notes');
    setSubmitting(true);
    try {
      const result = await api.addVisitNotes(visitId, notes);
      setAiInsights(result.aiInsights);
      loadVisits();
    } catch (err) { alert(err.message); }
    finally { setSubmitting(false); }
  };

  const openVisitDetail = (visit) => {
    setSelectedVisit(visit);
    setNotes(visit.notes || '');
    setAiInsights(null);
    // Load existing AI insights
    api.getAIInsights(visit.id).then(setAiInsights).catch(() => {});
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Visits</h1>
          <p className="page-subtitle">
            {user.role === 'Field Agent' ? 'Manage your field visits' : 'Track all field visits'}
          </p>
        </div>
      </div>

      <div className="filters-bar">
        <select
          value={filters.status}
          onChange={(e) => setFilters(f => ({ ...f, status: e.target.value }))}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      <div className="visits-page-layout">
        <div className="visits-list-panel">
          {loading ? (
            <div className="loading-spinner"><div className="spinner"></div></div>
          ) : visits.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📍</div>
              <h3>No visits found</h3>
            </div>
          ) : (
            <div className="visits-list">
              {visits.map(visit => (
                <div
                  key={visit.id}
                  className={`visit-list-item ${selectedVisit?.id === visit.id ? 'selected' : ''}`}
                  onClick={() => openVisitDetail(visit)}
                >
                  <div className="visit-list-header">
                    <span className={`status-badge status-${visit.status}`}>{visit.status.replace('_', ' ')}</span>
                    {visit.outcome && <span className={`outcome-badge outcome-${visit.outcome}`}>{visit.outcome.replace('_', ' ')}</span>}
                  </div>
                  <h4 className="visit-list-title">{visit.task_title}</h4>
                  <div className="visit-list-meta">
                    <span>👤 {visit.agent_name}</span>
                    {visit.location && <span>📍 {visit.location}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="visit-detail-panel">
          {selectedVisit ? (
            <div className="card">
              <div className="card-header">
                <h3>Visit #{selectedVisit.id}</h3>
                <span className={`status-badge status-${selectedVisit.status}`}>{selectedVisit.status.replace('_', ' ')}</span>
              </div>
              <div className="card-body">
                <div className="detail-meta-grid">
                  <div className="detail-meta-item">
                    <span className="meta-label">Task</span>
                    <span className="meta-value">{selectedVisit.task_title}</span>
                  </div>
                  <div className="detail-meta-item">
                    <span className="meta-label">Agent</span>
                    <span className="meta-value">{selectedVisit.agent_name}</span>
                  </div>
                  <div className="detail-meta-item">
                    <span className="meta-label">Location</span>
                    <span className="meta-value">{selectedVisit.location || '—'}</span>
                  </div>
                  <div className="detail-meta-item">
                    <span className="meta-label">Team</span>
                    <span className="meta-value">{selectedVisit.team_name || '—'}</span>
                  </div>
                  {selectedVisit.started_at && (
                    <div className="detail-meta-item">
                      <span className="meta-label">Started</span>
                      <span className="meta-value">{new Date(selectedVisit.started_at).toLocaleString()}</span>
                    </div>
                  )}
                  {selectedVisit.completed_at && (
                    <div className="detail-meta-item">
                      <span className="meta-label">Completed</span>
                      <span className="meta-value">{new Date(selectedVisit.completed_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>

                {/* Visit Actions */}
                {(user.role === 'Admin' || (user.role === 'Field Agent' && selectedVisit.agent_id === user.profileId)) && (
                  <div className="visit-action-buttons">
                    {selectedVisit.status === 'scheduled' && (
                      <button className="btn btn-success" onClick={() => { handleStartVisit(selectedVisit.id); }}>
                        ▶ Start Visit
                      </button>
                    )}
                    {selectedVisit.status === 'in_progress' && (
                      <button className="btn btn-primary" onClick={() => handleCompleteVisit(selectedVisit.id)}>
                        ✅ Complete Visit
                      </button>
                    )}
                  </div>
                )}

                {/* Notes Section */}
                <div className="visit-notes-section">
                  <h4>📝 Visit Notes</h4>
                  {(user.role === 'Admin' || (user.role === 'Field Agent' && selectedVisit.agent_id === user.profileId)) ? (
                    <>
                      <textarea
                        value={notes}
                        onChange={(e) => setNotes(e.target.value)}
                        placeholder="Enter visit observations, findings, and notes..."
                        rows={5}
                        className="notes-textarea"
                      />
                      <button
                        className="btn btn-primary"
                        onClick={() => handleSubmitNotes(selectedVisit.id)}
                        disabled={submitting || !notes.trim()}
                        style={{ marginTop: '8px' }}
                      >
                        {submitting ? 'Analyzing...' : '💡 Submit Notes & Get AI Analysis'}
                      </button>
                    </>
                  ) : (
                    <div className="visit-notes-readonly">
                      {selectedVisit.notes || 'No notes available'}
                    </div>
                  )}
                </div>

                {/* AI Insights */}
                {aiInsights && <AIInsights insights={aiInsights} />}
              </div>
            </div>
          ) : (
            <div className="empty-state">
              <div className="empty-icon">👈</div>
              <h3>Select a visit</h3>
              <p>Click on a visit from the list to view details and manage it.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
