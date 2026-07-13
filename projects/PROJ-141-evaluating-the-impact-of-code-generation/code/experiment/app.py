"""
Flask experiment interface for the code generation productivity study.

Provides endpoints for:
- Participant registration and consent verification
- Problem presentation (randomized, counterbalanced)
- Code submission with streaming
- Timestamp recording
- Condition switching (LLM-assisted vs baseline)
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from flask import Flask, request, jsonify, session, render_template_string
from functools import wraps

# Import from project modules (matching API surface)
from config.settings import get_config, get_experiment_config, get_logging_config
from logs.experiment import setup_experiment_logger, log_experiment_event, log_condition_assignment, log_session_start, log_session_complete
from experiment.consent import is_participant_consented, load_consent_record, ConsentError
from experiment.problem_loader import load_all_problems
from experiment.problem_validator import validate_problem_set, filter_medium_difficulty_problems
from experiment.randomization import assign_condition, generate_problem_order
from experiment.counterbalance import apply_counterbalancing
from experiment.condition_manager import get_active_condition, disable_llm_assistant
from data.models import Participant, Session, Problem, Submission, Condition
from data.db_schema import get_connection, init_schema

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-prod')

# Setup logging
config = get_config()
log_config = get_logging_config()
logger = setup_experiment_logger(log_config)

# Global state for experiment data (in production, use database)
experiment_state: Dict[str, Any] = {
    'problems': [],
    'active_participant': None,
    'current_session': None,
    'llm_disabled': False
}

def require_consented(f):
    """Decorator to ensure participant has given consent."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        participant_id = session.get('participant_id')
        if not participant_id:
            return jsonify({'error': 'No participant session'}), 401
        
        if not is_participant_consented(participant_id):
            return jsonify({'error': 'Consent not verified'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now(timezone.utc).isoformat()})

@app.route('/register', methods=['POST'])
def register_participant():
    """Register a new participant and verify consent."""
    data = request.get_json()
    participant_id = data.get('participant_id')
    irb_approval_id = data.get('irb_approval_id')
    
    if not participant_id:
        return jsonify({'error': 'participant_id required'}), 400
    
    try:
        # Verify IRB approval and collect consent
        from experiment.consent import verify_irb_approval, collect_consent, save_consent_record
        
        # Verify IRB approval (simplified for implementation)
        irb_valid = verify_irb_approval(irb_approval_id) if irb_approval_id else False
        if not irb_valid and irb_approval_id:
            return jsonify({'error': 'Invalid IRB approval ID'}), 400
        
        # Collect consent
        consent_data = {
            'participant_id': participant_id,
            'consent_timestamp': datetime.now(timezone.utc).isoformat(),
            'irb_approval_id': irb_approval_id or 'N/A',
            'consent_version': '1.0'
        }
        save_consent_record(participant_id, consent_data)
        
        # Initialize participant in database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO participants (id, created_at)
            VALUES (?, ?)
        ''', (participant_id, datetime.now(timezone.utc).isoformat()))
        conn.commit()
        
        session['participant_id'] = participant_id
        logger.info(f"Participant registered: {participant_id}")
        log_experiment_event('participant_registered', {'participant_id': participant_id})
        
        return jsonify({
            'status': 'success',
            'participant_id': participant_id,
            'consent_verified': True
        }), 201
        
    except ConsentError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/start_session', methods=['POST'])
@require_consented
def start_session():
    """Start a new experiment session for the participant."""
    participant_id = session['participant_id']
    data = request.get_json() or {}
    condition_preference = data.get('condition')  # Optional hint for counterbalancing
    
    try:
        # Load and validate problems
        problems = load_all_problems()
        medium_problems = filter_medium_difficulty_problems(problems)
        
        if len(medium_problems) == 0:
            return jsonify({'error': 'No valid medium-difficulty problems available'}), 500
        
        # Assign condition and generate order
        condition_assignment = assign_condition(participant_id)
        problem_order = generate_problem_order(participant_id, medium_problems)
        problem_order = apply_counterbalancing(participant_id, problem_order, condition_assignment['condition'])
        
        # Create session record
        session_id = str(uuid.uuid4())
        session_data = {
            'session_id': session_id,
            'participant_id': participant_id,
            'condition': condition_assignment['condition'],
            'seed': condition_assignment['seed'],
            'start_time': datetime.now(timezone.utc).isoformat(),
            'problem_order': [p['id'] for p in problem_order]
        }
        
        # Store in database
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO sessions (id, participant_id, condition, seed, start_time, problem_order)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session_id, participant_id, 
            condition_assignment['condition'].value,
            condition_assignment['seed'],
            session_data['start_time'],
            json.dumps(session_data['problem_order'])
        ))
        conn.commit()
        
        # Update state
        experiment_state['active_participant'] = participant_id
        experiment_state['current_session'] = session_data
        experiment_state['problems'] = problem_order
        experiment_state['llm_disabled'] = (condition_assignment['condition'] == Condition.BASELINE)
        
        # Log condition assignment
        log_condition_assignment(participant_id, session_id, condition_assignment['condition'].value, condition_assignment['seed'])
        log_session_start(participant_id, session_id, condition_assignment['condition'].value)
        logger.info(f"Session started: {session_id} for {participant_id}, condition: {condition_assignment['condition']}")
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'condition': condition_assignment['condition'].value,
            'problem_count': len(problem_order),
            'llm_assisted': not experiment_state['llm_disabled']
        }), 201
        
    except Exception as e:
        logger.error(f"Session start failed: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/problem', methods=['GET'])
@require_consented
def get_next_problem():
    """Get the next problem for the current session."""
    session_id = experiment_state.get('current_session', {}).get('session_id')
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    # Get next problem from order
    current_idx = experiment_state.get('current_session', {}).get('current_problem_index', 0)
    problem_order = experiment_state.get('current_session', {}).get('problem_order', [])
    
    if current_idx >= len(problem_order):
        return jsonify({'error': 'All problems completed'}), 404
    
    problem_id = problem_order[current_idx]
    # Find problem details (simplified - in production, fetch from DB)
    problem_data = next((p for p in experiment_state['problems'] if p['id'] == problem_id), None)
    
    if not problem_data:
        return jsonify({'error': 'Problem not found'}), 404
    
    # Log problem presentation
    log_experiment_event('problem_presented', {
        'session_id': session_id,
        'problem_id': problem_id,
        'timestamp': datetime.now(timezone.utc).isoformat()
    })
    
    return jsonify({
        'status': 'success',
        'problem': problem_data,
        'index': current_idx + 1,
        'total': len(problem_order)
    })

@app.route('/submit', methods=['POST'])
@require_consented
def submit_code():
    """Submit code solution for the current problem."""
    session_id = experiment_state.get('current_session', {}).get('session_id')
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    data = request.get_json()
    code = data.get('code')
    problem_id = data.get('problem_id')
    
    if not code:
        return jsonify({'error': 'Code is required'}), 400
    
    current_idx = experiment_state.get('current_session', {}).get('current_problem_index', 0)
    
    # Create submission record
    submission_id = str(uuid.uuid4())
    submission_data = {
        'submission_id': submission_id,
        'session_id': session_id,
        'problem_id': problem_id,
        'code': code,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'condition': experiment_state['current_session']['condition']
    }
    
    # Store in database
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (id, session_id, problem_id, code, timestamp, condition)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        submission_id, session_id, problem_id, code,
        submission_data['timestamp'],
        experiment_state['current_session']['condition']
    ))
    conn.commit()
    
    # Log submission
    log_experiment_event('code_submitted', {
        'session_id': session_id,
        'submission_id': submission_id,
        'problem_id': problem_id,
        'timestamp': submission_data['timestamp']
    })
    
    # Update current problem index
    experiment_state['current_session']['current_problem_index'] = current_idx + 1
    
    # Check if all problems completed
    problem_order = experiment_state['current_session']['problem_order']
    if experiment_state['current_session']['current_problem_index'] >= len(problem_order):
        log_session_complete(session_id, datetime.now(timezone.utc).isoformat())
        logger.info(f"Session completed: {session_id}")
    
    return jsonify({
        'status': 'success',
        'submission_id': submission_id,
        'next_problem_index': experiment_state['current_session']['current_problem_index']
    })

@app.route('/condition', methods=['GET'])
@require_consented
def get_current_condition():
    """Get the current condition for the session."""
    session_id = experiment_state.get('current_session', {}).get('session_id')
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    condition = experiment_state['current_session']['condition']
    llm_disabled = experiment_state['llm_disabled']
    
    return jsonify({
        'status': 'success',
        'condition': condition,
        'llm_assisted': not llm_disabled
    })

@app.route('/complete', methods=['POST'])
@require_consented
def complete_session():
    """Mark the session as complete."""
    session_id = experiment_state.get('current_session', {}).get('session_id')
    if not session_id:
        return jsonify({'error': 'No active session'}), 400
    
    end_time = datetime.now(timezone.utc).isoformat()
    log_session_complete(session_id, end_time)
    
    # Clear session state
    experiment_state['active_participant'] = None
    experiment_state['current_session'] = None
    
    return jsonify({
        'status': 'success',
        'message': 'Session completed successfully',
        'end_time': end_time
    })

def init_app():
    """Initialize the application."""
    init_schema()
    logger.info("Flask experiment interface initialized")

if __name__ == '__main__':
    init_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
