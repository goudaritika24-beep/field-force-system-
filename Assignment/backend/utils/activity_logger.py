"""
Activity Logger — records important actions to the activity_logs table.
"""
import json
from db.database import get_db


def log_activity(user_id, action, entity_type, entity_id, details=None):
    """
    Log an activity to the activity_logs table.

    Args:
        user_id: ID of the user performing the action
        action: Action type (e.g., 'task_created', 'visit_started')
        entity_type: Entity type ('task', 'visit', etc.)
        entity_id: ID of the affected entity
        details: Additional context dict (will be JSON-serialized)
    """
    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details) VALUES (?, ?, ?, ?, ?)",
            (user_id, action, entity_type, entity_id, json.dumps(details or {}))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to log activity: {e}")
