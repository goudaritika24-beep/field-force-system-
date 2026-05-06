const API_BASE = '/api';

/**
 * Fetch wrapper that automatically attaches JWT token and handles errors.
 */
async function request(endpoint, options = {}) {
  const token = localStorage.getItem('fieldops_token');
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers
    },
    ...options
  };

  let url = `${API_BASE}${endpoint}`;
  if (!options.method || options.method === 'GET') {
    url += (url.includes('?') ? '&' : '?') + '_nc=' + Date.now();
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch (err) {
    throw new Error('Network error — is the backend server running?');
  }
  
  if (response.status === 401 && !endpoint.startsWith('/auth/login')) {
    localStorage.removeItem('fieldops_token');
    localStorage.removeItem('fieldops_user');
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`Server returned invalid JSON (HTTP ${response.status})`);
  }
  
  if (!response.ok) {
    throw new Error(data.error || `Request failed (HTTP ${response.status})`);
  }
  
  return data;
}

export const api = {
  // Auth
  login: (username, password) => 
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  getMe: () => request('/auth/me'),

  // Tasks
  getTasks: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/tasks${query ? `?${query}` : ''}`);
  },
  getTask: (id) => request(`/tasks/${id}`),
  createTask: (data) => request('/tasks', { method: 'POST', body: JSON.stringify(data) }),
  updateTask: (id, data) => request(`/tasks/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  assignTask: (id, assigned_to) => request(`/tasks/${id}/assign`, { method: 'PUT', body: JSON.stringify({ assigned_to }) }),
  getAgents: () => request('/tasks/agents/list'),

  // Visits
  getVisits: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/visits${query ? `?${query}` : ''}`);
  },
  createVisit: (data) => request('/visits', { method: 'POST', body: JSON.stringify(data) }),
  startVisit: (id) => request(`/visits/${id}/start`, { method: 'PUT' }),
  completeVisit: (id, data) => request(`/visits/${id}/complete`, { method: 'PUT', body: JSON.stringify(data) }),
  addVisitNotes: (id, notes) => request(`/visits/${id}/notes`, { method: 'PUT', body: JSON.stringify({ notes }) }),
  getAIInsights: (id) => request(`/visits/${id}/ai-insights`),

  // Dashboard
  getDashboard: () => request('/dashboard'),

  // Reports
  getTasksByRegion: () => request('/reports/tasks-by-region'),
  getAgentPerformance: () => request('/reports/agent-performance'),
  getRecentVisits: () => request('/reports/recent-visits'),
  getTaskStatusDist: () => request('/reports/task-status-distribution'),
  getActivityLogs: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/reports/activity-logs${query ? `?${query}` : ''}`);
  }
};
