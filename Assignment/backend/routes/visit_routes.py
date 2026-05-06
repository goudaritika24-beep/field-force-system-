"""
Visit routes — lifecycle management (create, start, complete, notes, AI insights).
All routes require authentication.
"""
from flask import Blueprint, request, jsonify, g

from db.database import get_db, dict_from_row, dicts_from_rows
from middleware.auth import authenticate
from middleware.rbac import authorize, build_visit_scope_clause
from utils.activity_logger import log_activity
from services.mock_ai_service import analyze_visit_notes

visit_bp = Blueprint('visits', __name__)


@visit_bp.before_request
def before_request():
    """All visit routes require authentication (skip CORS preflight)."""
    if request.method == 'OPTIONS':
        return
    return authenticate(lambda: None)()


@visit_bp.route('/', methods=['GET'])
@authorize('visits', 'read')
def list_visits():
    """GET /api/visits — List visits with scope-based filtering."""
    try:
        status = request.args.get('status')
        task_id = request.args.get('task_id')
        agent_id = request.args.get('agent_id')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        offset = (page - 1) * limit

        scope_clause, scope_params = build_visit_scope_clause(g.user)

        where = f'WHERE 1=1 {scope_clause}'
        params = list(scope_params)

        if status:
            where += ' AND v.status = ?'
            params.append(status)
        if task_id:
            where += ' AND v.task_id = ?'
            params.append(int(task_id))
        if agent_id:
            where += ' AND v.agent_id = ?'
            params.append(int(agent_id))

        conn = get_db()

        visits = conn.execute(f"""
            SELECT v.*,
                   ep.full_name as agent_name,
                   tk.title as task_title,
                   t2.name as team_name,
                   r.name as region_name
            FROM visits v
            JOIN employee_profiles ep ON v.agent_id = ep.id
            JOIN tasks tk ON v.task_id = tk.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            LEFT JOIN regions r ON t2.region_id = r.id
            {where}
            ORDER BY v.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [limit, offset]).fetchall()

        count_row = conn.execute(f"""
            SELECT COUNT(*) as total
            FROM visits v
            JOIN employee_profiles ep ON v.agent_id = ep.id
            LEFT JOIN teams t2 ON ep.team_id = t2.id
            {where}
        """, params).fetchone()

        conn.close()

        return jsonify({
            'visits': dicts_from_rows(visits),
            'pagination': {
                'page': page,
                'limit': limit,
                'total': count_row['total'],
                'totalPages': -(-count_row['total'] // limit)
            }
        })

    except Exception as e:
        print(f"List visits error: {e}")
        return jsonify({'error': 'Failed to fetch visits.'}), 500


@visit_bp.route('/', methods=['POST'])
@authorize('visits', 'create')
def create_visit():
    """POST /api/visits — Create a new visit for a task."""
    try:
        data = request.get_json(silent=True) or {}
        task_id = data.get('task_id')
        agent_id = data.get('agent_id')
        location = data.get('location', '')

        if not task_id:
            return jsonify({'error': 'task_id is required.'}), 400

        conn = get_db()
        task = conn.execute('SELECT * FROM tasks WHERE id = ?', (task_id,)).fetchone()
        if not task:
            conn.close()
            return jsonify({'error': 'Task not found.'}), 404

        # Use the assigned agent or provided agent
        visit_agent_id = agent_id or task['assigned_to']
        if not visit_agent_id:
            conn.close()
            return jsonify({'error': 'No agent specified. Assign the task first or provide agent_id.'}), 400

        cur = conn.execute(
            "INSERT INTO visits (task_id, agent_id, status, location) VALUES (?, ?, 'scheduled', ?)",
            (task_id, visit_agent_id, location)
        )
        visit_id = cur.lastrowid
        conn.commit()

        log_activity(g.user['id'], 'visit_created', 'visit', visit_id, {
            'task_id': task_id, 'agent_id': visit_agent_id
        })

        visit = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        conn.close()

        return jsonify(dict_from_row(visit)), 201

    except Exception as e:
        print(f"Create visit error: {e}")
        return jsonify({'error': 'Failed to create visit.'}), 500


@visit_bp.route('/<int:visit_id>/start', methods=['PUT'])
@authorize('visits', 'update')
def start_visit(visit_id):
    """PUT /api/visits/<id>/start — Start a visit (Field Agent - own visits only)."""
    try:
        conn = get_db()
        visit = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        if not visit:
            conn.close()
            return jsonify({'error': 'Visit not found.'}), 404

        # Field agents can only start their own visits
        if g.user['role'] == 'Field Agent' and visit['agent_id'] != g.user['profileId']:
            conn.close()
            return jsonify({'error': 'You can only start your own visits.'}), 403

        if visit['status'] != 'scheduled':
            conn.close()
            return jsonify({'error': f"Cannot start a visit with status '{visit['status']}'."}), 400

        conn.execute(
            "UPDATE visits SET status = 'in_progress', started_at = datetime('now') WHERE id = ?",
            (visit_id,)
        )

        # Also update task status
        conn.execute(
            "UPDATE tasks SET status = 'in_progress', updated_at = datetime('now') WHERE id = ?",
            (visit['task_id'],)
        )
        conn.commit()

        log_activity(g.user['id'], 'visit_started', 'visit', visit_id, {
            'location': visit['location']
        })

        updated = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        conn.close()

        return jsonify(dict_from_row(updated))

    except Exception as e:
        print(f"Start visit error: {e}")
        return jsonify({'error': 'Failed to start visit.'}), 500


@visit_bp.route('/<int:visit_id>/complete', methods=['PUT'])
@authorize('visits', 'update')
def complete_visit(visit_id):
    """PUT /api/visits/<id>/complete — Complete a visit with outcome."""
    try:
        conn = get_db()
        visit = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        if not visit:
            conn.close()
            return jsonify({'error': 'Visit not found.'}), 404

        if g.user['role'] == 'Field Agent' and visit['agent_id'] != g.user['profileId']:
            conn.close()
            return jsonify({'error': 'You can only complete your own visits.'}), 403

        if visit['status'] != 'in_progress':
            conn.close()
            return jsonify({'error': f"Cannot complete a visit with status '{visit['status']}'."}), 400

        data = request.get_json(silent=True) or {}
        outcome = data.get('outcome', 'successful')
        notes = data.get('notes')

        conn.execute("""
            UPDATE visits
            SET status = 'completed', completed_at = datetime('now'),
                outcome = ?, notes = COALESCE(?, notes)
            WHERE id = ?
        """, (outcome, notes, visit_id))

        # Update task if all visits are complete
        open_visits = conn.execute("""
            SELECT COUNT(*) as count FROM visits
            WHERE task_id = ? AND status != 'completed' AND status != 'cancelled' AND id != ?
        """, (visit['task_id'], visit_id)).fetchone()

        if open_visits['count'] == 0:
            conn.execute(
                "UPDATE tasks SET status = 'completed', updated_at = datetime('now') WHERE id = ?",
                (visit['task_id'],)
            )

        conn.commit()

        log_activity(g.user['id'], 'visit_completed', 'visit', visit_id, {
            'outcome': outcome
        })

        # If notes provided, run AI analysis
        if notes:
            ai_result = analyze_visit_notes(notes)
            conn.execute("""
                INSERT INTO visit_ai_outputs
                    (visit_id, original_notes, ai_summary, follow_up_recommendation, risk_flag, suggested_next_action)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (visit_id, notes, ai_result['summary'], ai_result['follow_up_recommendation'],
                  ai_result['risk_flag'], ai_result['suggested_next_action']))
            conn.commit()

        updated = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        conn.close()

        return jsonify(dict_from_row(updated))

    except Exception as e:
        print(f"Complete visit error: {e}")
        return jsonify({'error': 'Failed to complete visit.'}), 500


@visit_bp.route('/<int:visit_id>/notes', methods=['PUT'])
@authorize('visits', 'update')
def add_notes(visit_id):
    """PUT /api/visits/<id>/notes — Add notes to a visit, triggers mock AI analysis."""
    try:
        conn = get_db()
        visit = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        if not visit:
            conn.close()
            return jsonify({'error': 'Visit not found.'}), 404

        if g.user['role'] == 'Field Agent' and visit['agent_id'] != g.user['profileId']:
            conn.close()
            return jsonify({'error': 'You can only update your own visit notes.'}), 403

        data = request.get_json(silent=True) or {}
        notes = data.get('notes', '').strip()

        if not notes:
            conn.close()
            return jsonify({'error': 'Notes cannot be empty.'}), 400

        conn.execute('UPDATE visits SET notes = ? WHERE id = ?', (notes, visit_id))

        # Run mock AI analysis
        ai_result = analyze_visit_notes(notes)

        # Delete old AI output for this visit if exists
        conn.execute('DELETE FROM visit_ai_outputs WHERE visit_id = ?', (visit_id,))

        conn.execute("""
            INSERT INTO visit_ai_outputs
                (visit_id, original_notes, ai_summary, follow_up_recommendation, risk_flag, suggested_next_action)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (visit_id, notes, ai_result['summary'], ai_result['follow_up_recommendation'],
              ai_result['risk_flag'], ai_result['suggested_next_action']))

        conn.commit()

        log_activity(g.user['id'], 'visit_notes_added', 'visit', visit_id, {
            'notes_length': len(notes)
        })

        updated = conn.execute('SELECT * FROM visits WHERE id = ?', (visit_id,)).fetchone()
        conn.close()

        return jsonify({
            'visit': dict_from_row(updated),
            'aiInsights': ai_result
        })

    except Exception as e:
        print(f"Add notes error: {e}")
        return jsonify({'error': 'Failed to add visit notes.'}), 500


@visit_bp.route('/<int:visit_id>/ai-insights', methods=['GET'])
@authorize('visits', 'read')
def get_ai_insights(visit_id):
    """GET /api/visits/<id>/ai-insights — Get AI analysis output for a visit."""
    try:
        conn = get_db()
        ai_output = conn.execute(
            'SELECT * FROM visit_ai_outputs WHERE visit_id = ?', (visit_id,)
        ).fetchone()
        conn.close()

        if not ai_output:
            return jsonify({'error': 'No AI insights found for this visit. Add visit notes first.'}), 404

        return jsonify(dict_from_row(ai_output))

    except Exception as e:
        print(f"Get AI insights error: {e}")
        return jsonify({'error': 'Failed to fetch AI insights.'}), 500
