import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const roleIcon = {
    'Admin': '👑',
    'Regional Manager': '🌍',
    'Team Lead': '👥',
    'Field Agent': '🔧',
    'Auditor': '📋'
  };

  const navItems = getNavItems(user?.role);

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">
          <span className="logo-icon">⚡</span>
          <span className="logo-text">FieldOps</span>
        </div>
      </div>

      <div className="sidebar-user">
        <div className="user-avatar">{user?.fullName?.[0] || 'U'}</div>
        <div className="user-info">
          <span className="user-name">{user?.fullName || 'User'}</span>
          <span className="user-role">
            {roleIcon[user?.role] || '👤'} {user?.role}
          </span>
          {user?.teamName && (
            <span className="user-team">{user.teamName}</span>
          )}
          {user?.regionName && (
            <span className="user-region">📍 {user.regionName}</span>
          )}
        </div>
      </div>

      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <button className="logout-btn" onClick={handleLogout}>
          <span className="nav-icon">🚪</span>
          <span className="nav-label">Logout</span>
        </button>
      </div>
    </aside>
  );
}

function getNavItems(role) {
  const items = [
    { path: '/', icon: '📊', label: 'Dashboard', roles: ['Admin', 'Regional Manager', 'Team Lead', 'Field Agent', 'Auditor'] },
    { path: '/tasks', icon: '📝', label: 'Tasks', roles: ['Admin', 'Regional Manager', 'Team Lead', 'Field Agent', 'Auditor'] },
    { path: '/visits', icon: '📍', label: 'Visits', roles: ['Admin', 'Regional Manager', 'Team Lead', 'Field Agent', 'Auditor'] },
    { path: '/reports', icon: '📈', label: 'Reports', roles: ['Admin', 'Regional Manager', 'Team Lead', 'Auditor'] },
    { path: '/activity-logs', icon: '📜', label: 'Activity Logs', roles: ['Admin', 'Auditor'] },
  ];

  return items.filter(item => item.roles.includes(role));
}
