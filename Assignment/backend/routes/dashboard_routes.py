"""
Dashboard routes — scoped summary statistics.
"""
from flask import Blueprint, request, jsonify, g

from db.database import get_db, dicts_from_rows
from middleware.auth import authenticate
from middleware.rbac import build_task_scope_clause, build_visit_scope_clause

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.before_request
def before_request():
    """Dashboard requires authentication (skip CORS preflight)."""
    if request.method == 'OPTIONS':
        return
    return authenticate(lambda: None)()


@dashboard_bp.route('/', methods=['GET'])
def get_dashboard():
    """GET /api/dashboard — Returns scoped summary statistics."""
    try:
        conn = get_db()
        task_clause, task_params = build_task_scope_clause(g.user)
        visit_clause, visit_params = build_visit_scope_clause(g.user)

        # Task stats
        task_stats = conn.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN tk.status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN tk.status = 'assigned' THEN 1 ELSE 0 END) as assigned,
                SUM(CASE WHEN tk.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN tk.status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN tk.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN tk.priority = 'critical' AND tk.status NOT IN ('completed','cancelled') THEN 1 ELSE 0 END) as critical_active
            FROM tasks tk
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            WHERE 1=1 {task_clause}
        """, task_params).fetchone()

        # Visit stats
        visit_stats = conn.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN v.status = 'scheduled' THEN 1 ELSE 0 END) as scheduled,
                SUM(CASE WHEN v.status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN v.status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM visits v
            JOIN employee_profiles ep ON v.agent_id = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            WHERE 1=1 {visit_clause}
        """, visit_params).fetchone()

        # Overdue tasks
        overdue_count = conn.execute(f"""
            SELECT COUNT(*) as count
            FROM tasks tk
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            WHERE tk.due_date < datetime('now')
              AND tk.status NOT IN ('completed', 'cancelled')
              {task_clause}
        """, task_params).fetchone()

        # Recent activity (last 10)
        recent_activity = conn.execute("""
            SELECT al.*, u.username, ep.full_name
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            LEFT JOIN employee_profiles ep ON ep.user_id = u.id
            ORDER BY al.created_at DESC
            LIMIT 10
        """).fetchall()

        # Task priority distribution
        priority_dist = conn.execute(f"""
            SELECT tk.priority, COUNT(*) as count
            FROM tasks tk
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            WHERE tk.status NOT IN ('completed', 'cancelled')
              {task_clause}
            GROUP BY tk.priority
        """, task_params).fetchall()

        # Visits completed this week
        weekly_visits = conn.execute(f"""
            SELECT DATE(v.completed_at) as date, COUNT(*) as count
            FROM visits v
            JOIN employee_profiles ep ON v.agent_id = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            WHERE v.status = 'completed'
              AND v.completed_at >= datetime('now', '-7 days')
              {visit_clause}
            GROUP BY DATE(v.completed_at)
            ORDER BY date
        """, visit_params).fetchall()

        conn.close()

        return jsonify({
            'tasks': dict(task_stats),
            'visits': dict(visit_stats),
            'overdueTasks': overdue_count['count'],
            'recentActivity': dicts_from_rows(recent_activity),
            'priorityDistribution': dicts_from_rows(priority_dist),
            'weeklyVisits': dicts_from_rows(weekly_visits)
        })

    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': 'Failed to fetch dashboard data.'}), 500
