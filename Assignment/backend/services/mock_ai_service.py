"""
Mock AI Service
Analyzes visit notes and generates structured AI outputs:
- Summary
- Follow-up recommendation
- Risk flag
- Suggested next action
"""
import re
import random

# ── Risk keyword dictionaries ────────────────────────────────────────────────
RISK_KEYWORDS = {
    'high': ['urgent', 'critical', 'failure', 'broken', 'emergency', 'danger',
             'hazard', 'violation', 'unsafe', 'immediate'],
    'medium': ['concern', 'issue', 'delay', 'problem', 'discrepancy', 'complaint',
               'risk', 'warning', 'overdue', 'damaged'],
    'low': ['minor', 'slight', 'small', 'cosmetic', 'note', 'observation', 'suggestion']
}

# ── Follow-up templates ─────────────────────────────────────────────────────
FOLLOW_UP_TEMPLATES = [
    'Schedule a follow-up visit within {days} days to verify {topic}.',
    'Escalate {topic} to management for review and action.',
    'Coordinate with the team to address {topic} before the next review cycle.',
    'Document findings and share with stakeholders for {topic}.',
    'Arrange a meeting with the client to discuss {topic} and next steps.'
]

# ── Action templates by risk level ───────────────────────────────────────────
ACTION_TEMPLATES = {
    'high': [
        'Immediately escalate to senior management and schedule emergency resolution.',
        'Create urgent follow-up task and notify all stakeholders within 24 hours.',
        'Initiate emergency protocol and document all findings for compliance review.'
    ],
    'medium': [
        'Create a follow-up task to address identified concerns within the next 3-5 business days.',
        'Schedule a review meeting with the team lead to discuss findings and plan corrective action.',
        'Update task priority and assign additional resources if needed.'
    ],
    'low': [
        'Log observations for the monthly review report. No immediate action required.',
        'Include findings in the next scheduled team briefing.',
        'Update documentation and continue monitoring in subsequent visits.'
    ],
    'none': [
        'Proceed with standard workflow. Mark task for routine follow-up.',
        'Archive visit notes and update task status accordingly.',
        'No further action needed. Continue with scheduled activities.'
    ]
}

# ── Topic patterns ───────────────────────────────────────────────────────────
TOPIC_PATTERNS = [
    (re.compile(r'(?:equipment|machine|device|tool)', re.IGNORECASE), 'equipment status'),
    (re.compile(r'(?:safety|compliance|regulation|audit)', re.IGNORECASE), 'safety compliance'),
    (re.compile(r'(?:client|customer|account|partner)', re.IGNORECASE), 'client relationship'),
    (re.compile(r'(?:inventory|stock|supply|count)', re.IGNORECASE), 'inventory management'),
    (re.compile(r'(?:repair|fix|replace|maintenance)', re.IGNORECASE), 'maintenance needs'),
    (re.compile(r'(?:train|onboard|procedure|process)', re.IGNORECASE), 'procedural updates'),
    (re.compile(r'(?:survey|feedback|satisfaction|response)', re.IGNORECASE), 'feedback analysis'),
    (re.compile(r'(?:map|location|site|facility)', re.IGNORECASE), 'site assessment'),
]


def extract_topics(notes):
    """Extract key topics from notes using simple keyword/pattern matching."""
    found = [topic for pattern, topic in TOPIC_PATTERNS if pattern.search(notes)]
    return found if found else ['general operations']


def assess_risk(notes):
    """Assess risk level based on keyword detection."""
    lower_notes = notes.lower()
    for keyword in RISK_KEYWORDS['high']:
        if keyword in lower_notes:
            return 'high'
    for keyword in RISK_KEYWORDS['medium']:
        if keyword in lower_notes:
            return 'medium'
    for keyword in RISK_KEYWORDS['low']:
        if keyword in lower_notes:
            return 'low'
    return 'none'


def generate_summary(notes):
    """Generate a condensed summary from notes."""
    sentences = [s.strip() for s in re.split(r'[.!?]+', notes) if len(s.strip()) > 10]
    topics = extract_topics(notes)
    risk = assess_risk(notes)

    if len(sentences) <= 2:
        summary = f"Visit notes indicate activity related to {' and '.join(topics)}. "
        summary += (sentences[0] + '.') if sentences else 'Brief update provided.'
    else:
        summary = f"Comprehensive visit covering {', '.join(topics)}. "
        summary += f"Key points: {'. '.join(s for s in sentences[:2])}."
        if len(sentences) > 2:
            summary += f" Additional {len(sentences) - 2} observation(s) noted."

    if risk in ('high', 'medium'):
        summary += f" Risk level assessed as {risk} — attention recommended."

    return summary


def generate_follow_up(notes):
    """Generate follow-up recommendation."""
    risk = assess_risk(notes)
    topics = extract_topics(notes)
    primary_topic = topics[0]

    days = '1-2' if risk == 'high' else ('3-5' if risk == 'medium' else '7-10')
    template = random.choice(FOLLOW_UP_TEMPLATES)

    return template.replace('{days}', days).replace('{topic}', primary_topic)


def suggest_action(notes):
    """Suggest next action based on risk level."""
    risk = assess_risk(notes)
    actions = ACTION_TEMPLATES.get(risk, ACTION_TEMPLATES['none'])
    return random.choice(actions)


def analyze_visit_notes(notes):
    """
    Main analysis function — accepts visit notes, returns structured AI output.

    Args:
        notes: The visit notes text to analyze

    Returns:
        dict with keys: summary, follow_up_recommendation, risk_flag, suggested_next_action
    """
    if not notes or not notes.strip():
        return {
            'summary': 'No visit notes provided for analysis.',
            'follow_up_recommendation': 'Agent should add detailed visit notes for proper analysis.',
            'risk_flag': 'none',
            'suggested_next_action': 'Request the field agent to update visit notes with observations and findings.'
        }

    return {
        'summary': generate_summary(notes),
        'follow_up_recommendation': generate_follow_up(notes),
        'risk_flag': assess_risk(notes),
        'suggested_next_action': suggest_action(notes)
    }
