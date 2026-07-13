"""
Flask experiment interface for the code generation productivity study.
Provides endpoints for problem presentation, code submission, and session management.
"""
import os
import sys
import json
import logging
import uuid
from datetime import datetime, timezone
from functools import wraps
from flask import Flask, request, jsonify, g

# Import from existing project modules
from experiment.consent import is_participant_consented, load_consent_record
from experiment.problem_loader import load_all_problems
from experiment.problem_validator import validate_problem_set
from experiment.timestamp_recorder import (
    get_current_utc_timestamp,
    record_problem_view,
    record_code_submission,
    record_condition_switch,
)
from experiment.condition_manager import ConditionManager
from experiment.submission_handler import SubmissionHandler
from experiment.randomization import initialize_participant_session
from logs.experiment import setup_experiment_logger, log_experiment_event
from config.settings import get_experiment_config

# Configure logging
logger = setup_experiment_logger()
config = get_experiment_config()

app = Flask(__name__)

# Global state for active sessions (in production, use a database)
active_sessions = {}
condition_managers = {}
submission_handlers = {}

def require_consented(f):
    """Decorator to ensure participant has consented before accessing endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        participant_id = request.headers.get('X-Participant-ID')
        if not participant_id:
            return jsonify({"error": "Missing participant ID"}), 400

        if not is_participant_consented(participant_id):
            return jsonify({"error": "Participant has not provided consent"}), 403

        g.participant_id = participant_id
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "timestamp": get_current_utc_timestamp()})

@app.route('/register', methods=['POST'])
def register_participant():
    """Register a new participant and generate their ID."""
    data = request.get_json()
    email = data.get('email')
    experience_years = data.get('experience_years')

    if not email or experience_years is None:
        return jsonify({"error": "Email and experience years are required"}), 400

    participant_id = str(uuid.uuid4())
    
    # Initialize session
    session = initialize_participant_session(participant_id, experience_years)
    active_sessions[participant_id] = session
    
    # Initialize condition manager
    condition_managers[participant_id] = ConditionManager(participant_id)
    
    # Initialize submission handler
    submission_handlers[participant_id] = SubmissionHandler(participant_id)

    log_experiment_event(
        event_type="participant_registered",
        participant_id=participant_id,
        metadata={"email": email, "experience_years": experience_years}
    )

    return jsonify({
        "participant_id": participant_id,
        "condition": session["condition"],
        "seed": session["seed"],
        "timestamp": get_current_utc_timestamp()
    }), 201

@app.route('/start-session', methods=['POST'])
@require_consented
def start_session():
    """Start an experiment session for a participant."""
    participant_id = g.participant_id

    if participant_id not in active_sessions:
        return jsonify({"error": "Participant not registered"}), 404

    session = active_sessions[participant_id]
    if session.get("started"):
        return jsonify({"error": "Session already started"}), 400

    session["started"] = True
    session["start_time"] = get_current_utc_timestamp()
    
    # Log session start
    log_experiment_event(
        event_type="session_started",
        participant_id=participant_id,
        metadata={"condition": session["condition"]}
    )

    return jsonify({
        "status": "started",
        "condition": session["condition"],
        "problem_order": session["problem_order"],
        "timestamp": get_current_utc_timestamp()
    })

@app.route('/next-problem', methods=['GET'])
@require_consented
def get_next_problem():
    """Get the next problem for the participant based on their condition and order."""
    participant_id = g.participant_id

    if participant_id not in active_sessions:
        return jsonify({"error": "Participant not registered"}), 404

    session = active_sessions[participant_id]
    if not session.get("started"):
        return jsonify({"error": "Session not started"}), 400

    # Get current problem index
    current_index = session.get("current_problem_index", 0)
    problem_order = session.get("problem_order", [])

    if current_index >= len(problem_order):
        return jsonify({
            "status": "complete",
            "message": "All problems completed",
            "timestamp": get_current_utc_timestamp()
        })

    problem_id = problem_order[current_index]
    
    # Load problems
    problems = load_all_problems()
    problem = next((p for p in problems if p["id"] == problem_id), None)

    if not problem:
        logger.error(f"Problem {problem_id} not found")
        return jsonify({"error": "Problem not found"}), 404

    # Record problem view timestamp
    record_problem_view(participant_id, problem_id)

    # Increment index
    session["current_problem_index"] = current_index + 1

    return jsonify({
        "problem": problem,
        "problem_id": problem_id,
        "condition": session["condition"],
        "attempt_number": current_index + 1,
        "total_problems": len(problem_order),
        "timestamp": get_current_utc_timestamp()
    })

@app.route('/submit-code', methods=['POST'])
@require_consented
def submit_code():
    """Submit code solution for the current problem."""
    participant_id = g.participant_id
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data provided"}), 400

    problem_id = data.get("problem_id")
    code = data.get("code")
    language = data.get("language", "python")

    if not problem_id or not code:
        return jsonify({"error": "Problem ID and code are required"}), 400

    if participant_id not in active_sessions:
        return jsonify({"error": "Participant not registered"}), 404

    session = active_sessions[participant_id]
    
    # Get current condition
    condition_manager = condition_managers.get(participant_id)
    current_condition = condition_manager.get_current_condition() if condition_manager else session["condition"]

    # Create submission
    submission_handler = submission_handlers.get(participant_id)
    if not submission_handler:
        return jsonify({"error": "Submission handler not initialized"}), 500

    submission_id = submission_handler.create_submission(
        participant_id=participant_id,
        problem_id=problem_id,
        code=code,
        language=language,
        condition=current_condition
    )

    # Record submission timestamp
    record_code_submission(participant_id, problem_id, submission_id)

    # Log submission
    log_experiment_event(
        event_type="code_submitted",
        participant_id=participant_id,
        metadata={
            "problem_id": problem_id,
            "submission_id": submission_id,
            "condition": current_condition,
            "language": language
        }
    )

    return jsonify({
        "submission_id": submission_id,
        "status": "submitted",
        "timestamp": get_current_utc_timestamp()
    })

@app.route('/condition', methods=['GET'])
@require_consented
def get_current_condition():
    """Get the current condition for the participant."""
    participant_id = g.participant_id

    if participant_id not in active_sessions:
        return jsonify({"error": "Participant not registered"}), 404

    session = active_sessions[participant_id]
    condition_manager = condition_managers.get(participant_id)

    current_condition = condition_manager.get_current_condition() if condition_manager else session["condition"]

    return jsonify({
        "condition": current_condition,
        "timestamp": get_current_utc_timestamp()
    })

@app.route('/switch-condition', methods=['POST'])
@require_consented
def switch_condition():
    """Switch to the next condition (for within-subject design)."""
    participant_id = g.participant_id
    data = request.get_json()
    force_switch = data.get("force", False)

    if participant_id not in active_sessions:
        return jsonify({"error": "Participant not registered"}), 404

    condition_manager = condition_managers.get(participant_id)
    if not condition_manager:
        return jsonify({"error": "Condition manager not initialized"}), 500

    try:
        new_condition = condition_manager.switch_condition(force_switch=force_switch)
        
        # Record condition switch timestamp
        record_condition_switch(participant_id, new_condition)

        # Log condition switch
        log_experiment_event(
            event_type="condition_switched",
            participant_id=participant_id,
            metadata={"new_condition": new_condition}
        )

        return jsonify({
            "condition": new_condition,
            "timestamp": get_current_utc_timestamp()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/complete-session', methods=['POST'])
@require_consented
def complete_session():
    """Complete the experiment session for a participant."""
    participant_id = g.participant_id

    if participant_id not in active_sessions:
        return jsonify({"error": "Participant not registered"}), 404

    session = active_sessions[participant_id]
    session["completed"] = True
    session["end_time"] = get_current_utc_timestamp()

    # Log session completion
    log_experiment_event(
        event_type="session_completed",
        participant_id=participant_id,
        metadata={
            "total_problems": len(session.get("problem_order", [])),
            "condition": session["condition"]
        }
    )

    return jsonify({
        "status": "completed",
        "timestamp": get_current_utc_timestamp()
    })

def init_app():
    """Initialize the Flask application with configuration."""
    app.config['DEBUG'] = config.get('debug', False)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max code size
    return app

if __name__ == '__main__':
    init_app()
    port = int(os.environ.get('PORT', 5000))
    debug = config.get('debug', False)
    app.run(host='0.0.0.0', port=port, debug=debug)