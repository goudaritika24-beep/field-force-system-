import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const DEMO_USERS = [
  { username: 'admin', password: 'admin123', role: 'Admin', desc: 'Full system access' },
  { username: 'rm_north', password: 'rm123', role: 'Regional Manager', desc: 'North Region scope' },
  { username: 'tl_alpha', password: 'tl123', role: 'Team Lead', desc: 'Alpha Squad scope' },
  { username: 'agent1', password: 'agent123', role: 'Field Agent', desc: 'Own tasks & visits only' },
  { username: 'auditor', password: 'audit123', role: 'Auditor', desc: 'Read-only access' },
];

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  };

  const quickLogin = async (user) => {
    setUsername(user.username);
    setPassword(user.password);
    setError('');
    try {
      await login(user.username, user.password);
      navigate('/');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div className="login-page">
      <div className="login-bg-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="login-logo">⚡</div>
            <h1>FieldOps</h1>
            <p>Task & Visit Management System</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            {error && <div className="error-message">{error}</div>}

            <div className="form-group">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                required
                autoFocus
              />
            </div>

            <div className="form-group">
              <label htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                required
              />
            </div>

            <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="demo-credentials">
            <h4>Quick Login — Demo Accounts</h4>
            <div className="demo-grid">
              {DEMO_USERS.map((u) => (
                <button
                  key={u.username}
                  className="demo-btn"
                  onClick={() => quickLogin(u)}
                  disabled={loading}
                >
                  <span className="demo-role">{u.role}</span>
                  <span className="demo-desc">{u.desc}</span>
                  <span className="demo-creds">{u.username} / {u.password}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
