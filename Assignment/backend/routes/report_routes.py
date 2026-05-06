"""
Report routes — SQL-based reports and activity logs.
"""
from flask import Blueprint, request, jsonify, g

from db.database import get_db, dict_from_row, dicts_from_rows
from middleware.auth import authenticate
from middleware.rbac import authorize

report_bp = Blueprint('reports', __name__)


@report_bp.before_request
def before_request():
    """All report routes require authentication (skip CORS preflight)."""
    if request.method == 'OPTIONS':
        return
    return authenticate(lambda: None)()


@report_bp.route('/tasks-by-region', methods=['GET'])
@authorize('reports', 'read')
def tasks_by_region():
    """
    GET /api/reports/tasks-by-region
    Report 1: Pending tasks grouped by region and team with priority breakdown.
    """
    try:
        conn = get_db()
        data = conn.execute("""
            SELECT r.name AS region, t.name AS team,
                   COUNT(tk.id) AS pending_tasks,
                   SUM(CASE WHEN tk.priority = 'critical' THEN 1 ELSE 0 END) as critical,
                   SUM(CASE WHEN tk.priority = 'high' THEN 1 ELSE 0 END) as high,
                   SUM(CASE WHEN tk.priority = 'medium' THEN 1 ELSE 0 END) as medium,
                   SUM(CASE WHEN tk.priority = 'low' THEN 1 ELSE 0 END) as low
            FROM tasks tk
            JOIN employee_profiles ep ON tk.assigned_to = ep.id
            JOIN teams t ON ep.team_id = t.id
            JOIN regions r ON t.region_id = r.id
            WHERE tk.status IN ('pending', 'assigned', 'in_progress')
            GROUP BY r.name, t.name
            ORDER BY pending_tasks DESC
        """).fetchall()
        conn.close()

        return jsonify({'report': 'Pending Tasks by Region & Team', 'data': dicts_from_rows(data)})

    except Exception as e:
        print(f"Report tasks-by-region error: {e}")
        return jsonify({'error': 'Failed to generate report.'}), 500


@report_bp.route('/agent-performance', methods=['GET'])
@authorize('reports', 'read')
def agent_performance():
    """
    GET /api/reports/agent-performance
    Report 2: Average completion time per field agent with visit success rate.
    """
    try:
        conn = get_db()
        data = conn.execute("""
            SELECT ep.full_name as agent_name,
                   t.name as team_name,
                   r.name as region_name,
                   COUNT(tk.id) as total_completed,
                   ROUND(AVG(julianday(tk.updated_at) - julianday(tk.created_at)), 2) as avg_days_to_complete,
                   COUNT(DISTINCT v.id) as total_visits,
                   SUM(CASE WHEN v.outcome = 'successful' THEN 1 ELSE 0 END) as successful_visits
            FROM tasks tk
            JOIN employee_profiles ep ON tk.assigned_to = ep.id
            JOIN teams t ON ep.team_id = t.id
            JOIN regions r ON t.region_id = r.id
            LEFT JOIN visits v ON v.task_id = tk.id AND v.agent_id = ep.id AND v.status = 'completed'
            WHERE tk.status = 'completed'
            GROUP BY ep.id
            ORDER BY avg_days_to_complete ASC
        """).fetchall()
        conn.close()

        return jsonify({'report': 'Agent Performance Summary', 'data': dicts_from_rows(data)})

    except Exception as e:
        print(f"Report agent-performance error: {e}")
        return jsonify({'error': 'Failed to generate report.'}), 500


@report_bp.route('/recent-visits', methods=['GET'])
@authorize('reports', 'read')
def recent_visits():
    """
    GET /api/reports/recent-visits
    Report 3: Visits completed in the last 7 days.
    """
    try:
        conn = get_db()
        data = conn.execute("""
            SELECT DATE(v.completed_at) AS visit_date,
                   COUNT(v.id) AS completed_visits,
                   ep.full_name AS agent,
                   t.name as team_name,
                   r.name as region_name,
                   GROUP_CONCAT(DISTINCT v.outcome) as outcomes
            FROM visits v
            JOIN employee_profiles ep ON v.agent_id = ep.id
            JOIN teams t ON ep.team_id = t.id
            JOIN regions r ON t.region_id = r.id
            WHERE v.status = 'completed'
              AND v.completed_at >= datetime('now', '-7 days')
            GROUP BY DATE(v.completed_at), ep.id
            ORDER BY visit_date DESC
        """).fetchall()

        # Also get summary
        summary = conn.execute("""
            SELECT
                COUNT(*) as total_completed,
                COUNT(DISTINCT v.agent_id) as agents_active,
                ROUND(AVG(julianday(v.completed_at) - julianday(v.started_at)), 2) as avg_visit_duration_days
            FROM visits v
            WHERE v.status = 'completed'
              AND v.completed_at >= datetime('now', '-7 days')
        """).fetchone()

        conn.close()

        return jsonify({
            'report': 'Visits Completed - Last 7 Days',
            'data': dicts_from_rows(data),
            'summary': dict_from_row(summary)
        })

    except Exception as e:
        print(f"Report recent-visits error: {e}")
        return jsonify({'error': 'Failed to generate report.'}), 500


@report_bp.route('/task-status-distribution', methods=['GET'])
@authorize('reports', 'read')
def task_status_distribution():
    """
    GET /api/reports/task-status-distribution
    Bonus Report: Task status distribution by manager.
    """
    try:
        conn = get_db()
        data = conn.execute("""
            SELECT u.username as created_by,
                   ep_creator.full_name as manager_name,
                   tk.status,
                   COUNT(*) as count
            FROM tasks tk
            JOIN users u ON tk.created_by = u.id
            LEFT JOIN employee_profiles ep_creator ON ep_creator.user_id = u.id
            GROUP BY u.id, tk.status
            ORDER BY u.username, tk.status
        """).fetchall()
        conn.close()

        return jsonify({'report': 'Task Status Distribution by Manager', 'data': dicts_from_rows(data)})

    except Exception as e:
        print(f"Report task-status error: {e}")
        return jsonify({'error': 'Failed to generate report.'}), 500


@report_bp.route('/activity-logs', methods=['GET'])
@authorize('logs', 'read')
def activity_logs():
    """
    GET /api/reports/activity-logs
    Activity logs with filtering and pagination.
    """
    try:
        action_filter = request.args.get('action')
        entity_type = request.args.get('entity_type')
        user_id = request.args.get('user_id')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        where = 'WHERE 1=1'
        params = []

        if action_filter:
            where += ' AND al.action = ?'
            params.append(action_filter)
        if entity_type:
            where += ' AND al.entity_type = ?'
            params.append(entity_type)
        if user_id:
            where += ' AND al.user_id = ?'
            params.append(int(user_id))

        conn = get_db()

        logs = conn.execute(f"""
            SELECT al.*, u.username, ep.full_name,
                   r.name as user_role
            FROM activity_logs al
            JOIN users u ON al.user_id = u.id
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN employee_profiles ep ON ep.user_id = u.id
            {where}
            ORDER BY al.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()

        count_row = conn.execute(f"""
            SELECT COUNT(*) as total FROM activity_logs al {where}
        """, params).fetchone()

        conn.close()

        return jsonify({
            'logs': dicts_from_rows(logs),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': count_row['total'],
                'totalPages': -(-count_row['total'] // limit)
            }
        })

    except Exception as e:
        print(f"Activity logs error: {e}")
        return jsonify({'error': 'Failed to fetch activity logs.'}), 500
