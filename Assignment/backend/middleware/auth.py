"""
JWT Authentication middleware for Flask.
Verifies Bearer tokens and attaches user info to flask.g
"""
import json
from functools import wraps
from flask import request, jsonify, g
import jwt

from db.database import get_db, dict_from_row

JWT_SECRET = 'fieldops-secret-key-2024'
JWT_ALGORITHM = 'HS256'


def authenticate(f):
    """Decorator that verifies JWT and attaches user info to g.user."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authentication required. Please provide a valid token.'}), 401

        token = auth_header.split(' ', 1)[1]

        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired. Please login again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token.'}), 401

        conn = get_db()
        user = conn.execute("""
            SELECT u.id, u.username, u.role_id, r.name as role, r.permissions,
                   ep.id as profile_id, ep.full_name, ep.team_id, t.region_id
            FROM users u
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN employee_profiles ep ON ep.user_id = u.id
            LEFT JOIN teams t ON ep.team_id = t.id
            WHERE u.id = ? AND u.is_active = 1
        """, (decoded['userId'],)).fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'User not found or inactive.'}), 401

        g.user = {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'roleId': user['role_id'],
            'profileId': user['profile_id'],
            'fullName': user['full_name'],
            'teamId': user['team_id'],
            'regionId': user['region_id'],
            'permissions': json.loads(user['permissions'])
        }

        return f(*args, **kwargs)
    return decorated
