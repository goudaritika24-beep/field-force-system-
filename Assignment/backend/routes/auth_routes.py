"""
Auth routes — login and current user info.
"""
import json
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from flask import Blueprint, request, jsonify, g

from db.database import get_db, dict_from_row
from middleware.auth import authenticate, JWT_SECRET, JWT_ALGORITHM

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """POST /api/auth/login — Authenticate user and return JWT + user profile."""
    try:
        data = request.get_json(silent=True) or {}
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({'error': 'Username and password are required.'}), 400

        conn = get_db()
        user = conn.execute("""
            SELECT u.id, u.username, u.password_hash, u.role_id, u.is_active,
                   r.name as role, r.permissions,
                   ep.id as profile_id, ep.full_name, ep.email, ep.phone,
                   ep.team_id, ep.designation,
                   t.name as team_name, t.region_id,
                   reg.name as region_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN employee_profiles ep ON ep.user_id = u.id
            LEFT JOIN teams t ON ep.team_id = t.id
            LEFT JOIN regions reg ON t.region_id = reg.id
            WHERE u.username = ?
        """, (username,)).fetchone()
        conn.close()

        if not user:
            return jsonify({'error': 'Invalid username or password.'}), 401

        if not user['is_active']:
            return jsonify({'error': 'Account is deactivated. Contact administrator.'}), 401

        if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return jsonify({'error': 'Invalid username or password.'}), 401

        # Generate JWT
        payload = {
            'userId': user['id'],
            'role': user['role'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'role': user['role'],
                'roleId': user['role_id'],
                'profileId': user['profile_id'],
                'fullName': user['full_name'],
                'email': user['email'],
                'phone': user['phone'],
                'teamId': user['team_id'],
                'teamName': user['team_name'],
                'regionId': user['region_id'],
                'regionName': user['region_name'],
                'designation': user['designation'],
                'permissions': json.loads(user['permissions'])
            }
        })

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Internal server error during login.'}), 500


@auth_bp.route('/me', methods=['GET'])
@authenticate
def get_me():
    """GET /api/auth/me — Returns current authenticated user info."""
    try:
        conn = get_db()
        user = conn.execute("""
            SELECT u.id, u.username, r.name as role, r.permissions,
                   ep.id as profile_id, ep.full_name, ep.email, ep.phone,
                   ep.team_id, ep.designation,
                   t.name as team_name, t.region_id,
                   reg.name as region_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            LEFT JOIN employee_profiles ep ON ep.user_id = u.id
            LEFT JOIN teams t ON ep.team_id = t.id
            LEFT JOIN regions reg ON t.region_id = reg.id
            WHERE u.id = ?
        """, (g.user['id'],)).fetchone()
        conn.close()

        return jsonify({
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'profileId': user['profile_id'],
            'fullName': user['full_name'],
            'email': user['email'],
            'phone': user['phone'],
            'teamId': user['team_id'],
            'teamName': user['team_name'],
            'regionId': user['region_id'],
            'regionName': user['region_name'],
            'designation': user['designation'],
            'permissions': json.loads(user['permissions'])
        })

    except Exception as e:
        print(f"Get me error: {e}")
        return jsonify({'error': 'Internal server error.'}), 500
