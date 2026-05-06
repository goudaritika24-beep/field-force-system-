"""
Seed script — populates the database with test data.
Run: python -m db.seed   (from the backend/ directory)
"""
import json
import sys
import os

# Add parent directory to path so we can import db.database
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import bcrypt
from db.database import get_db, init_db

# ── Helpers ──────────────────────────────────────────────────────────────────
from datetime import datetime, timedelta

def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def now_str():
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

def days_from_now(d):
    return (datetime.utcnow() + timedelta(days=d)).strftime('%Y-%m-%d %H:%M:%S')

def days_ago(d):
    return (datetime.utcnow() - timedelta(days=d)).strftime('%Y-%m-%d %H:%M:%S')


def seed():
    print('🌱 Seeding database...')

    # Ensure tables exist
    init_db()
    conn = get_db()
    cur = conn.cursor()

    # Clear existing data in reverse FK order
    cur.executescript("""
        DELETE FROM visit_ai_outputs;
        DELETE FROM activity_logs;
        DELETE FROM visits;
        DELETE FROM tasks;
        DELETE FROM employee_profiles;
        DELETE FROM users;
        DELETE FROM teams;
        DELETE FROM regions;
        DELETE FROM roles;
        DELETE FROM sqlite_sequence;
    """)

    # ── Roles ────────────────────────────────────────────────────────────────
    role_permissions = {
        'Admin': json.dumps({
            'tasks': ['create', 'read', 'update', 'delete', 'assign'],
            'visits': ['create', 'read', 'update', 'delete'],
            'reports': ['read'],
            'logs': ['read'],
            'users': ['create', 'read', 'update', 'delete']
        }),
        'Regional Manager': json.dumps({
            'tasks': ['create', 'read', 'update', 'assign'],
            'visits': ['read'],
            'reports': ['read'],
            'logs': ['read'],
            'users': ['read']
        }),
        'Team Lead': json.dumps({
            'tasks': ['create', 'read', 'update', 'assign'],
            'visits': ['read'],
            'reports': ['read'],
            'logs': [],
            'users': ['read']
        }),
        'Field Agent': json.dumps({
            'tasks': ['read'],
            'visits': ['read', 'update'],
            'reports': [],
            'logs': [],
            'users': []
        }),
        'Auditor': json.dumps({
            'tasks': ['read'],
            'visits': ['read'],
            'reports': ['read'],
            'logs': ['read'],
            'users': ['read']
        })
    }

    for name, perms in role_permissions.items():
        cur.execute('INSERT INTO roles (name, permissions) VALUES (?, ?)', (name, perms))
    print('  ✓ Roles created')

    # ── Regions ──────────────────────────────────────────────────────────────
    for r in ['North', 'South', 'East', 'West']:
        cur.execute('INSERT INTO regions (name) VALUES (?)', (r,))
    print('  ✓ Regions created')

    # ── Teams ────────────────────────────────────────────────────────────────
    teams = [
        ('Alpha Squad', 1), ('Bravo Unit', 1),       # North
        ('Charlie Force', 2), ('Delta Ops', 2),       # South
        ('Echo Patrol', 3), ('Foxtrot Crew', 3),      # East
        ('Golf Team', 4), ('Hotel Brigade', 4),       # West
    ]
    for name, region_id in teams:
        cur.execute('INSERT INTO teams (name, region_id) VALUES (?, ?)', (name, region_id))
    print('  ✓ Teams created')

    # ── Users & Employee Profiles ────────────────────────────────────────────
    def insert_user(username, pw, role_id):
        cur.execute(
            'INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)',
            (username, hash_pw(pw), role_id)
        )
        return cur.lastrowid

    def insert_profile(user_id, full_name, email, phone, team_id, designation):
        cur.execute(
            'INSERT INTO employee_profiles (user_id, full_name, email, phone, team_id, designation) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, full_name, email, phone, team_id, designation)
        )
        return cur.lastrowid

    # Admin
    admin_id = insert_user('admin', 'admin123', 1)
    insert_profile(admin_id, 'Arjun Mehta', 'arjun@fieldops.com', '9000000001', None, 'System Administrator')

    # Regional Manager (North region - teams 1, 2)
    rm_id = insert_user('rm_north', 'rm123', 2)
    insert_profile(rm_id, 'Priya Sharma', 'priya@fieldops.com', '9000000002', 1, 'Regional Manager - North')

    # Team Lead (Alpha Squad - team 1)
    tl_id = insert_user('tl_alpha', 'tl123', 3)
    insert_profile(tl_id, 'Ravi Kumar', 'ravi@fieldops.com', '9000000003', 1, 'Team Lead - Alpha Squad')

    # Field Agents
    fa1_id = insert_user('agent1', 'agent123', 4)
    insert_profile(fa1_id, 'Sneha Reddy', 'sneha@fieldops.com', '9000000004', 1, 'Field Agent')

    fa2_id = insert_user('agent2', 'agent123', 4)
    insert_profile(fa2_id, 'Karan Patel', 'karan@fieldops.com', '9000000005', 1, 'Field Agent')

    fa3_id = insert_user('agent3', 'agent123', 4)
    insert_profile(fa3_id, 'Meera Nair', 'meera@fieldops.com', '9000000006', 3, 'Field Agent')

    fa4_id = insert_user('agent4', 'agent123', 4)
    insert_profile(fa4_id, 'Deepak Joshi', 'deepak@fieldops.com', '9000000007', 5, 'Field Agent')

    # Auditor
    aud_id = insert_user('auditor', 'audit123', 5)
    insert_profile(aud_id, 'Nisha Gupta', 'nisha@fieldops.com', '9000000008', None, 'Compliance Auditor')

    # Additional Regional Manager (South region)
    rm2_id = insert_user('rm_south', 'rm123', 2)
    insert_profile(rm2_id, 'Vikram Singh', 'vikram@fieldops.com', '9000000009', 3, 'Regional Manager - South')

    # Additional Team Lead (Charlie Force - team 3)
    tl2_id = insert_user('tl_charlie', 'tl123', 3)
    insert_profile(tl2_id, 'Ananya Das', 'ananya@fieldops.com', '9000000010', 3, 'Team Lead - Charlie Force')

    print('  ✓ Users & profiles created')

    # Profile IDs: admin=1, rm_north=2, tl_alpha=3, agent1=4, agent2=5, agent3=6, agent4=7, auditor=8, rm_south=9, tl_charlie=10

    # ── Tasks ────────────────────────────────────────────────────────────────
    task_data = [
        ('Site Inspection - Warehouse A', 'Inspect safety equipment and fire exits at Warehouse A in the north district.', 'high', 'assigned', admin_id, 4, days_from_now(3), days_ago(2), days_ago(1)),
        ('Customer Onboarding - Retail Hub', 'Complete onboarding procedures for the new retail hub partner.', 'medium', 'in_progress', rm_id, 4, days_from_now(5), days_ago(3), days_ago(1)),
        ('Equipment Maintenance Check', 'Verify maintenance logs and condition of field equipment.', 'low', 'pending', tl_id, None, days_from_now(7), days_ago(1), days_ago(1)),
        ('Client Follow-up - Premium Account', 'Follow up with premium client regarding service renewal.', 'critical', 'assigned', rm_id, 5, days_from_now(1), days_ago(4), days_ago(2)),
        ('Territory Mapping - Sector 12', 'Map and document all service points in Sector 12.', 'medium', 'completed', tl_id, 5, days_ago(1), days_ago(10), days_ago(1)),
        ('Safety Audit - South Plant', 'Conduct safety compliance audit at south manufacturing plant.', 'high', 'assigned', rm2_id, 6, days_from_now(2), days_ago(3), days_ago(1)),
        ('New Product Demo - East Region', 'Demonstrate new product line to prospective East region clients.', 'medium', 'pending', admin_id, None, days_from_now(10), days_ago(1), days_ago(1)),
        ('Inventory Verification', 'Verify inventory counts at all south region storage facilities.', 'high', 'in_progress', rm2_id, 6, days_from_now(4), days_ago(5), days_ago(2)),
        ('Training Session - Q2 Updates', 'Conduct field agent training on updated Q2 procedures.', 'low', 'pending', admin_id, None, days_from_now(14), now_str(), now_str()),
        ('Emergency Repair - Client Site', 'Urgent repair needed at client location due to equipment failure.', 'critical', 'in_progress', tl_id, 4, days_from_now(0), days_ago(1), days_ago(0)),
        ('Market Survey - West Zone', 'Conduct market survey across west zone retail outlets.', 'medium', 'assigned', admin_id, 7, days_from_now(6), days_ago(2), days_ago(1)),
        ('Compliance Documentation', 'Prepare and submit compliance documentation for north region.', 'high', 'assigned', rm_id, 5, days_from_now(3), days_ago(1), days_ago(1)),
        ('Client Satisfaction Survey', 'Visit top 5 clients in south region for satisfaction feedback.', 'medium', 'completed', rm2_id, 6, days_ago(3), days_ago(14), days_ago(3)),
        ('Facility Upgrade Assessment', 'Assess north facilities for potential upgrades.', 'low', 'cancelled', rm_id, 4, days_ago(5), days_ago(20), days_ago(5)),
    ]
    for t in task_data:
        cur.execute(
            'INSERT INTO tasks (title, description, priority, status, created_by, assigned_to, due_date, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            t
        )
    print('  ✓ Tasks created')

    # ── Visits ───────────────────────────────────────────────────────────────
    visit_data = [
        (1, 4, 'scheduled', None, None, None, None, 'Warehouse A, North District', days_ago(1)),
        (2, 4, 'in_progress', days_ago(1), None, 'Met with store manager. Reviewing paperwork.', None, 'Retail Hub, Sector 7', days_ago(1)),
        (4, 5, 'scheduled', None, None, None, None, 'Premium Client HQ, Floor 12', days_ago(2)),
        (5, 5, 'completed', days_ago(5), days_ago(2), 'Mapped all 15 service points in Sector 12. Found 2 locations need relocation. Documentation complete.', 'successful', 'Sector 12 Field Area', days_ago(5)),
        (6, 6, 'scheduled', None, None, None, None, 'South Manufacturing Plant', days_ago(1)),
        (8, 6, 'in_progress', days_ago(2), None, 'Started verification at Facility 1. Counts are accurate so far. Minor discrepancies in electronics category.', None, 'South Storage Facility 1', days_ago(2)),
        (10, 4, 'in_progress', days_ago(0), None, 'Arrived at client site. Equipment failure confirmed - main pump unit needs replacement. Ordered parts.', None, 'Client Site - Industrial Park', days_ago(0)),
        (11, 7, 'scheduled', None, None, None, None, 'West Zone - Retail Strip Mall', days_ago(1)),
        (13, 6, 'completed', days_ago(10), days_ago(4), 'Visited all 5 top clients. Overall satisfaction is high. Two clients raised concerns about response time. One client interested in premium upgrade.', 'successful', 'South Region - Various Client Sites', days_ago(10)),
        (14, 4, 'cancelled', None, None, 'Task was cancelled - facility upgrade postponed.', None, 'North Facility Complex', days_ago(5)),
    ]
    for v in visit_data:
        cur.execute(
            'INSERT INTO visits (task_id, agent_id, status, started_at, completed_at, notes, outcome, location, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            v
        )
    print('  ✓ Visits created')

    # ── Visit AI Outputs ─────────────────────────────────────────────────────
    ai_data = [
        (4,
         'Mapped all 15 service points in Sector 12. Found 2 locations need relocation. Documentation complete.',
         'Agent completed comprehensive mapping of 15 service points in Sector 12. Two locations identified for relocation due to accessibility concerns.',
         'Schedule relocation planning meeting for the 2 identified service points within the next week.',
         'low',
         'Create relocation task for the 2 service points and assign to facilities team.'),
        (9,
         'Visited all 5 top clients. Overall satisfaction is high. Two clients raised concerns about response time. One client interested in premium upgrade.',
         'Client satisfaction survey completed across 5 premium accounts. High overall satisfaction with targeted concerns around service response times. Upsell opportunity identified.',
         'Address response time concerns with operations team. Schedule premium upgrade presentation for interested client.',
         'medium',
         'Create follow-up tasks: (1) Response time improvement plan, (2) Premium upgrade proposal for interested client.'),
    ]
    for a in ai_data:
        cur.execute(
            'INSERT INTO visit_ai_outputs (visit_id, original_notes, ai_summary, follow_up_recommendation, risk_flag, suggested_next_action) VALUES (?, ?, ?, ?, ?, ?)',
            a
        )
    print('  ✓ AI outputs created')

    # ── Activity Logs ────────────────────────────────────────────────────────
    log_data = [
        (admin_id, 'task_created', 'task', 1, json.dumps({'title': 'Site Inspection - Warehouse A'}), days_ago(2)),
        (admin_id, 'task_assigned', 'task', 1, json.dumps({'assigned_to': 'Sneha Reddy'}), days_ago(1)),
        (rm_id, 'task_created', 'task', 2, json.dumps({'title': 'Customer Onboarding - Retail Hub'}), days_ago(3)),
        (rm_id, 'task_assigned', 'task', 2, json.dumps({'assigned_to': 'Sneha Reddy'}), days_ago(2)),
        (fa1_id, 'visit_started', 'visit', 2, json.dumps({'location': 'Retail Hub, Sector 7'}), days_ago(1)),
        (rm_id, 'task_created', 'task', 4, json.dumps({'title': 'Client Follow-up - Premium Account'}), days_ago(4)),
        (tl_id, 'task_created', 'task', 5, json.dumps({'title': 'Territory Mapping - Sector 12'}), days_ago(10)),
        (fa2_id, 'visit_completed', 'visit', 4, json.dumps({'outcome': 'successful'}), days_ago(2)),
        (fa2_id, 'visit_notes_added', 'visit', 4, json.dumps({'notes_length': 95}), days_ago(2)),
        (rm2_id, 'task_created', 'task', 6, json.dumps({'title': 'Safety Audit - South Plant'}), days_ago(3)),
        (fa1_id, 'visit_started', 'visit', 7, json.dumps({'location': 'Client Site - Industrial Park'}), days_ago(0)),
        (tl_id, 'status_changed', 'task', 10, json.dumps({'from': 'assigned', 'to': 'in_progress'}), days_ago(0)),
        (fa3_id, 'visit_completed', 'visit', 9, json.dumps({'outcome': 'successful'}), days_ago(4)),
        (admin_id, 'task_created', 'task', 9, json.dumps({'title': 'Training Session - Q2 Updates'}), now_str()),
    ]
    for log in log_data:
        cur.execute(
            'INSERT INTO activity_logs (user_id, action, entity_type, entity_id, details, created_at) VALUES (?, ?, ?, ?, ?, ?)',
            log
        )
    print('  ✓ Activity logs created')

    conn.commit()
    conn.close()

    print('\n✅ Database seeded successfully!')
    print('\n📋 Test Credentials:')
    print('  Admin:            admin / admin123')
    print('  Regional Manager: rm_north / rm123  (North Region)')
    print('  Regional Manager: rm_south / rm123  (South Region)')
    print('  Team Lead:        tl_alpha / tl123  (Alpha Squad)')
    print('  Team Lead:        tl_charlie / tl123 (Charlie Force)')
    print('  Field Agent:      agent1 / agent123 (Alpha Squad)')
    print('  Field Agent:      agent2 / agent123 (Alpha Squad)')
    print('  Field Agent:      agent3 / agent123 (Charlie Force)')
    print('  Field Agent:      agent4 / agent123 (Echo Patrol)')
    print('  Auditor:          auditor / audit123')


if __name__ == '__main__':
    seed()
