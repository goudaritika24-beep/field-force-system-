import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export default function TaskList() {
  const { user, hasPermission } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '', priority: '', search: '' });
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [agents, setAgents] = useState([]);
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 'medium', due_date: '', assigned_to: '' });
  const [creating, setCreating] = useState(false);

  const loadTasks = () => {
    setLoading(true);
    const params = {};
    if (filters.status) params.status = filters.status;
    if (filters.priority) params.priority = filters.priority;
    if (filters.search) params.search = filters.search;

    api.getTasks(params)
      .then(data => setTasks(data.tasks))
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadTasks(); }, [filters]);

  useEffect(() => {
    if (hasPermission('tasks', 'assign')) {
      api.getAgents().then(setAgents).catch(() => {});
    }
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      await api.createTask({
        ...newTask,
        assigned_to: newTask.assigned_to ? parseInt(newTask.assigned_to) : null
      });
      setShowCreateModal(false);
      setNewTask({ title: '', description: '', priority: 'medium', due_date: '', assigned_to: '' });
      loadTasks();
    } catch (err) {
      alert(err.message);
    } finally {
      setCreating(false);
    }
  };

  const priorityClass = (p) => `priority-badge priority-${p}`;
  const statusClass = (s) => `status-badge status-${s}`;

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>Tasks</h1>
          <p className="page-subtitle">Manage and track all field operations tasks</p>
        </div>
        {hasPermission('tasks', 'create') && (
          <button className="btn btn-primary" onClick={() => setShowCreateModal(true)}>
            + New Task
          </button>
        )}
      </div>

      <div className="filters-bar">
        <input
          type="text"
          placeholder="🔍 Search tasks..."
          value={filters.search}
          onChange={(e) => setFilters(f => ({ ...f, search: e.target.value }))}
          className="filter-input"
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters(f => ({ ...f, status: e.target.value }))}
          className="filter-select"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="assigned">Assigned</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
        <select
          value={filters.priority}
          onChange={(e) => setFilters(f => ({ ...f, priority: e.target.value }))}
          className="filter-select"
        >
          <option value="">All Priorities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-spinner"><div className="spinner"></div></div>
      ) : tasks.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">📋</div>
          <h3>No tasks found</h3>
          <p>Try adjusting your filters or create a new task.</p>
        </div>
      ) : (
        <div className="task-grid">
          {tasks.map(task => (
            <Link key={task.id} to={`/tasks/${task.id}`} className="task-card">
              <div className="task-card-header">
                <span className={priorityClass(task.priority)}>{task.priority}</span>
                <span className={statusClass(task.status)}>{task.status.replace('_', ' ')}</span>
              </div>
              <h3 className="task-card-title">{task.title}</h3>
              <p className="task-card-desc">{task.description?.slice(0, 100)}{task.description?.length > 100 ? '...' : ''}</p>
              <div className="task-card-meta">
                {task.assigned_to_name && (
                  <span className="meta-item">👤 {task.assigned_to_name}</span>
                )}
                {task.team_name && (
                  <span className="meta-item">👥 {task.team_name}</span>
                )}
                {task.due_date && (
                  <span className={`meta-item ${new Date(task.due_date) < new Date() && task.status !== 'completed' ? 'overdue' : ''}`}>
                    📅 {new Date(task.due_date).toLocaleDateString()}
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      )}

      {showCreateModal && (
        <div className="modal-overlay" onClick={() => setShowCreateModal(false)}>
          <div className="modal" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Create New Task</h2>
              <button className="modal-close" onClick={() => setShowCreateModal(false)}>✕</button>
            </div>
            <form onSubmit={handleCreate} className="modal-body">
              <div className="form-group">
                <label>Title *</label>
                <input type="text" required value={newTask.title} onChange={e => setNewTask(t => ({ ...t, title: e.target.value }))} placeholder="Task title" />
              </div>
              <div className="form-group">
                <label>Description</label>
                <textarea value={newTask.description} onChange={e => setNewTask(t => ({ ...t, description: e.target.value }))} placeholder="Task description" rows={3} />
              </div>
              <div className="form-row">
                <div className="form-group">
                  <label>Priority</label>
                  <select value={newTask.priority} onChange={e => setNewTask(t => ({ ...t, priority: e.target.value }))}>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Due Date</label>
                  <input type="date" value={newTask.due_date} onChange={e => setNewTask(t => ({ ...t, due_date: e.target.value }))} />
                </div>
              </div>
              {agents.length > 0 && (
                <div className="form-group">
                  <label>Assign To</label>
                  <select value={newTask.assigned_to} onChange={e => setNewTask(t => ({ ...t, assigned_to: e.target.value }))}>
                    <option value="">-- Unassigned --</option>
                    {agents.map(a => (
                      <option key={a.id} value={a.id}>{a.full_name} ({a.team_name})</option>
                    ))}
                  </select>
                </div>
              )}
              <div className="modal-actions">
                <button type="button" className="btn btn-secondary" onClick={() => setShowCreateModal(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={creating}>
                  {creating ? 'Creating...' : 'Create Task'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
