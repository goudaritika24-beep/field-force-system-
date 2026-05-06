"""
Role-Based Access Control (RBAC) middleware.
Provides authorization decorator and scope-based SQL clause builders.
"""
from functools import wraps
from flask import jsonify, g


def authorize(module, action):
    """
    Decorator that checks if the authenticated user's role has
    the required permission for a module/action.
    Usage: @authorize('tasks', 'create')
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = g.user
            permissions = user.get('permissions', {})

            if module not in permissions:
                return jsonify({
                    'error': f"Access denied. Your role ({user['role']}) does not have access to the {module} module."
                }), 403

            if action not in permissions[module]:
                return jsonify({
                    'error': f"Access denied. Your role ({user['role']}) cannot perform '{action}' on {module}."
                }), 403

            return f(*args, **kwargs)
        return decorated
    return decorator


def get_scope_filter(user):
    """
    Returns a scope filter object based on the user's role.
    Used by routes to filter queries by region/team/agent.
    """
    role = user['role']
    if role in ('Admin', 'Auditor'):
        return {'scope': 'global', 'filter': {}}
    elif role == 'Regional Manager':
        return {'scope': 'region', 'filter': {'regionId': user['regionId']}}
    elif role == 'Team Lead':
        return {'scope': 'team', 'filter': {'teamId': user['teamId']}}
    elif role == 'Field Agent':
        return {'scope': 'self', 'filter': {'profileId': user['profileId']}}
    else:
        return {'scope': 'none', 'filter': {}}


def build_task_scope_clause(user):
    """
    Build SQL WHERE clause fragment based on user scope for tasks.
    Returns (clause_string, params_list)
    """
    sf = get_scope_filter(user)
    scope = sf['scope']
    filt = sf['filter']

    if scope == 'global':
        return ('', [])
    elif scope == 'region':
        return ('AND t2.region_id = ?', [filt['regionId']])
    elif scope == 'team':
        return ('AND ep.team_id = ?', [filt['teamId']])
    elif scope == 'self':
        return ('AND tk.assigned_to = ?', [filt['profileId']])
    else:
        return ('AND 1 = 0', [])


def build_visit_scope_clause(user):
    """
    Build SQL WHERE clause fragment based on user scope for visits.
    Returns (clause_string, params_list)
    """
    sf = get_scope_filter(user)
    scope = sf['scope']
    filt = sf['filter']

    if scope == 'global':
        return ('', [])
    elif scope == 'region':
        return ('AND t2.region_id = ?', [filt['regionId']])
    elif scope == 'team':
        return ('AND ep.team_id = ?', [filt['teamId']])
    elif scope == 'self':
        return ('AND v.agent_id = ?', [filt['profileId']])
    else:
        return ('AND 1 = 0', [])
