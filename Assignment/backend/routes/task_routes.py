"""
Task routes — CRUD, assignment, and agent listing.
All routes require authentication.
"""
import json
from flask import Blueprint, request, jsonify, g

from db.database import get_db, dict_from_row, dicts_from_rows
from middleware.auth import authenticate
from middleware.rbac import authorize, build_task_scope_clause
from utils.activity_logger import log_activity

task_bp = Blueprint('tasks', __name__)


@task_bp.before_request
def before_request():
    """All task routes require authentication (skip CORS preflight)."""
    if request.method == 'OPTIONS':
        return
    return authenticate(lambda: None)()


@task_bp.route('/agents/list', methods=['GET'])
@authorize('tasks', 'read')
def list_agents():
    """GET /api/tasks/agents/list — Get field agents for assignment dropdown."""
    try:
        conn = get_db()
        user = g.user

        query = """
            SELECT ep.id, ep.full_name, ep.designation, ep.team_id,
                   t.name as team_name, r.name as region_name
            FROM employee_profiles ep
            JOIN users u ON ep.user_id = u.id
            JOIN roles rl ON u.role_id = rl.id
            LEFT JOIN teams t ON ep.team_id = t.id
            LEFT JOIN regions r ON t.region_id = r.id
            WHERE rl.name = 'Field Agent'
        """
        params = []

        if user['role'] == 'Regional Manager':
            query += ' AND t.region_id = ?'
            params.append(user['regionId'])
        elif user['role'] == 'Team Lead':
            query += ' AND ep.team_id = ?'
            params.append(user['teamId'])

        query += ' ORDER BY ep.full_name'
        agents = conn.execute(query, params).fetchall()
        conn.close()

        return jsonify(dicts_from_rows(agents))

    except Exception as e:
        print(f"List agents error: {e}")
        return jsonify({'error': 'Failed to fetch agents.'}), 500


@task_bp.route('/', methods=['GET'])
@authorize('tasks', 'read')
def list_tasks():
    """GET /api/tasks — List tasks with scope-based filtering and pagination."""
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')
        assigned_to = request.args.get('assigned_to')
        search = request.args.get('search')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        scope_clause, scope_params = build_task_scope_clause(g.user)

        where = f'WHERE 1=1 {scope_clause}'
        params = list(scope_params)

        if status:
            where += ' AND tk.status = ?'
            params.append(status)
        if priority:
            where += ' AND tk.priority = ?'
            params.append(priority)
        if assigned_to:
            where += ' AND tk.assigned_to = ?'
            params.append(int(assigned_to))
        if search:
            where += ' AND (tk.title LIKE ? OR tk.description LIKE ?)'
            params.append(f'%{search}%')
            params.append(f'%{search}%')

        conn = get_db()

        tasks = conn.execute(f"""
            SELECT tk.*,
                   creator.username as created_by_username,
                   ep.full_name as assigned_to_name,
                   ep.team_id,
                   t2.name as team_name,
                   t2.region_id,
                   r.name as region_name
            FROM tasks tk
            LEFT JOIN users creator ON tk.created_by = creator.id
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            LEFT JOIN regions r ON t2.region_id = r.id
            {where}
            ORDER BY
              CASE tk.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
              END,
              tk.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()

        count_row = conn.execute(f"""
            SELECT COUNT(*) as total
            FROM tasks tk
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            {where}
        """, params).fetchone()

        conn.close()

        return jsonify({
            'tasks': dicts_from_rows(tasks),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': count_row['total'],
                'totalPages': -(-count_row['total'] // limit)  # ceil division
            }
        })

    except Exception as e:
        print(f"List tasks error: {e}")
        return jsonify({'error': 'Failed to fetch tasks.'}), 500


@task_bp.route('/<int:task_id>', methods=['GET'])
@authorize('tasks', 'read')
def get_task(task_id):
    """GET /api/tasks/<id> — Get task details with visits."""
    try:
        conn = get_db()

        task = conn.execute("""
            SELECT tk.*,
                   creator.username as created_by_username,
                   ep.full_name as assigned_to_name,
                   ep.team_id,
                   t2.name as team_name,
                   t2.region_id,
                   r.name as region_name
            FROM tasks tk
            LEFT JOIN users creator ON tk.created_by = creator.id
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            LEFT JOIN regions r ON t2.region_id = r.id
            WHERE tk.id = ?
        """, (task_id,)).fetchone()

        if not task:
            conn.close()
            return jsonify({'error': 'Task not found.'}), 404

        # Scope check
        scope_clause, scope_params = build_task_scope_clause(g.user)
        scoped = conn.execute(f"""
            SELECT tk.id FROM tasks tk
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            WHERE tk.id = ? {scope_clause}
        """, [task_id] + list(scope_params)).fetchone()

        if not scoped:
            conn.close()
            return jsonify({'error': 'You do not have access to this task.'}), 403

        # Get visits for this task
        visits = conn.execute("""
            SELECT v.*, ep.full_name as agent_name
            FROM visits v
            JOIN employee_profiles ep ON v.agent_id = ep.id
            WHERE v.task_id = ?
            ORDER BY v.created_at DESC
        """, (task_id,)).fetchall()

        conn.close()

        result = dict_from_row(task)
        result['visits'] = dicts_from_rows(visits)
        return jsonify(result)

    except Exception as e:
        print(f"Get task error: {e}")
        return jsonify({'error': 'Failed to fetch task details.'}), 500


@task_bp.route('/', methods=['POST'])
@authorize('tasks', 'create')
def create_task():
    """POST /api/tasks — Create a new task."""
    try:
        data = request.get_json(silent=True) or {}
        title = data.get('title')
        description = data.get('description', '')
        priority = data.get('priority', 'medium')
        due_date = data.get('due_date')
        assigned_to = data.get('assigned_to')

        if not title:
            return jsonify({'error': 'Task title is required.'}), 400

        status = 'assigned' if assigned_to else 'pending'

        conn = get_db()
        cur = conn.execute(
            "INSERT INTO tasks (title, description, priority, status, created_by, assigned_to, due_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, priority, status, g.user['id'], assigned_to, due_date)
        )
        task_id = cur.lastrowid
        conn.commit()

        log_activity(g.user['id'], 'task_created', 'task', task_id, {'title': title})

        if assigned_to:
            agent = conn.execute('SELECT full_name FROM employee_profiles WHERE id = ?', (assigned_to,)).fetchone()
            log_activity(g.user['id'], 'task_assigned', 'task', task_id, {
                'assigned_to': agent['full_name'] if agent else str(assigned_to)
            })

        task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        conn.close()

        return jsonify(dict_from_row(task)), 201

    except Exception as e:
        print(f"Create task error: {e}")
        return jsonify({'error': 'Failed to create task.'}), 500


@task_bp.route('/<int:task_id>', methods=['PUT'])
@authorize('tasks', 'update')
def update_task(task_id):
    """PUT /api/tasks/<id> — Update task details/status."""
    try:
        conn = get_db()
        task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        if not task:
            conn.close()
            return jsonify({'error': 'Task not found.'}), 404

        data = request.get_json(silent=True) or {}
        title = data.get('title')
        description = data.get('description')
        priority = data.get('priority')
        status = data.get('status')
        due_date = data.get('due_date')
        old_status = task['status']

        conn.execute("""
            UPDATE tasks
            SET title = COALESCE(?, title),
                description = COALESCE(?, description),
                priority = COALESCE(?, priority),
                status = COALESCE(?, status),
                due_date = COALESCE(?, due_date),
                updated_at = datetime('now')
            WHERE id = ?
        """, (title, description, priority, status, due_date, task_id))
        conn.commit()

        if status and status != old_status:
            log_activity(g.user['id'], 'status_changed', 'task', task_id, {
                'from': old_status, 'to': status
            })

        updated = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        conn.close()

        return jsonify(dict_from_row(updated))

    except Exception as e:
        print(f"Update task error: {e}")
        return jsonify({'error': 'Failed to update task.'}), 500


@task_bp.route('/<int:task_id>/assign', methods=['PUT'])
@authorize('tasks', 'assign')
def assign_task(task_id):
    """PUT /api/tasks/<id>/assign — Assign task to a field agent."""
    try:
        data = request.get_json(silent=True) or {}
        assigned_to = data.get('assigned_to')

        if not assigned_to:
            return jsonify({'error': 'assigned_to (profile ID) is required.'}), 400

        conn = get_db()
        task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        if not task:
            conn.close()
            return jsonify({'error': 'Task not found.'}), 404

        agent = conn.execute('SELECT * FROM employee_profiles WHERE id = ?', (assigned_to,)).fetchone()
        if not agent:
            conn.close()
            return jsonify({'error': 'Agent profile not found.'}), 400

        conn.execute(
            "UPDATE tasks SET assigned_to = ?, status = 'assigned', updated_at = datetime('now') WHERE id = ?",
            (assigned_to, task_id)
        )
        conn.commit()

        log_activity(g.user['id'], 'task_assigned', 'task', task_id, {
            'assigned_to': agent['full_name']
        })

        updated = conn.execute("""
            SELECT tk.*, ep.full_name as assigned_to_name
            FROM tasks tk
            LEFT JOIN employee_profiles ep ON tk.assigned_to = ep.id
            WHERE tk.id = ?
        """, (task_id,)).fetchone()
        conn.close()

        return jsonify(dict_from_row(updated))

    except Exception as e:
        print(f"Assign task error: {e}")
        return jsonify({'error': 'Failed to assign task.'}), 500
