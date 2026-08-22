import json
import os
import sys
import logging
import random
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure we are running from the project root or code directory
# Adjust paths relative to the script location
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

# Configure logging to a file in data/logs/
# We must ensure the directory exists before creating the handler
LOG_DIR = PROJECT_ROOT / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "data_collection.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants for paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
PARTICIPANT_LOGS_PATH = DATA_RAW_DIR / "participant_logs.json"

def ensure_data_directory():
    """Ensure all required data directories exist."""
    dirs = [DATA_RAW_DIR, LOG_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    logger.info(f"Ensured data directories exist: {[str(d) for d in dirs]}")

def calculate_checksum(data: str) -> str:
    """Calculate SHA-256 checksum of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def update_checksums(data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a checksum field to the data dictionary."""
    if isinstance(data, dict):
        # Serialize to JSON string for checksum (sorted keys for consistency)
        json_str = json.dumps(data, sort_keys=True)
        data['checksum'] = calculate_checksum(json_str)
    return data

def load_existing_logs() -> List[Dict[str, Any]]:
    """Load existing participant logs if the file exists."""
    if PARTICIPANT_LOGS_PATH.exists():
        try:
            with open(PARTICIPANT_LOGS_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'sessions' in data:
                    return data['sessions']
                else:
                    logger.warning("Existing logs file format unexpected, resetting.")
                    return []
        except json.JSONDecodeError:
            logger.error("Failed to decode existing logs file, resetting.")
            return []
    return []

def save_logs(sessions: List[Dict[str, Any]]):
    """Save the list of sessions to the participant_logs.json file."""
    # Structure the output as expected by downstream tasks
    output_data = {
        "export_timestamp": datetime.now().isoformat(),
        "sessions": sessions
    }
    
    # Calculate checksum for the whole payload
    output_str = json.dumps(output_data, sort_keys=True)
    output_data['checksum'] = calculate_checksum(output_str)

    with open(PARTICIPANT_LOGS_PATH, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved {len(sessions)} sessions to {PARTICIPANT_LOGS_PATH}")

def assign_participant(participant_id: int, mode: str) -> Dict[str, Any]:
    """Assign a condition (LLM, Human, None) to a participant."""
    conditions = ['llm_generated', 'human_generated', 'no_doc']
    # In mock mode, we can randomize. In real mode, this might be pre-assigned.
    condition = random.choice(conditions) if mode == 'mock' else conditions[participant_id % 3]
    
    return {
        "participant_id": participant_id,
        "condition": condition,
        "assignment_time": datetime.now().isoformat()
    }

def log_session_start(participant_id: int, condition: str) -> Dict[str, Any]:
    """Create a new session record."""
    return {
        "participant_id": participant_id,
        "condition": condition,
        "session_start": datetime.now().isoformat(),
        "session_end": None,
        "status": "in_progress",
        "task_time_seconds": 0,
        "clarification_questions": [],
        "clarification_question_count": 0,
        "intervention_status": None,
        "helpfulness_rating": None,
        "notes": []
    }

def log_session_end(session: Dict[str, Any], status: str = "completed") -> Dict[str, Any]:
    """Finalize a session record."""
    session["session_end"] = datetime.now().isoformat()
    session["status"] = status
    return session

def log_help_request(session: Dict[str, Any], question_text: str, source: str = "keyword") -> Dict[str, Any]:
    """Log a clarification question."""
    question_entry = {
        "timestamp": datetime.now().isoformat(),
        "text": question_text,
        "source": source
    }
    session["clarification_questions"].append(question_entry)
    session["clarification_question_count"] = len(session["clarification_questions"])
    return session

def process_help_requests(session: Dict[str, Any], questions: List[str]) -> Dict[str, Any]:
    """Process a list of questions and log them."""
    for q in questions:
        log_help_request(session, q)
    return session

def calculate_cognitive_load_proxy(session: Dict[str, Any]) -> float:
    """
    Calculate a proxy for cognitive load based on:
    1. Number of clarification questions
    2. Task time (normalized)
    This is a simple heuristic for the study.
    """
    q_count = session.get("clarification_question_count", 0)
    task_time = session.get("task_time_seconds", 0)
    
    # Simple weighted sum
    # Higher questions = higher load. Higher time = higher load.
    # Normalize time by a typical 30 min (1800s) for the proxy
    time_factor = min(task_time / 1800.0, 2.0) # Cap at 2x
    
    return (q_count * 0.5) + time_factor

def capture_helpfulness_survey(session: Dict[str, Any], rating: int) -> Dict[str, Any]:
    """Capture the subjective helpfulness rating (1-5)."""
    if 1 <= rating <= 5:
        session["helpfulness_rating"] = rating
    else:
        logger.warning(f"Invalid rating {rating} for participant {session['participant_id']}")
    return session

def apply_stop_loss_intervention(session: Dict[str, Any], max_time: int = 2700) -> Dict[str, Any]:
    """
    Apply stop-loss intervention if task time exceeds max_time.
    Sets status to 'failed', intervention_status to 'stop_loss'.
    """
    if session.get("task_time_seconds", 0) > max_time:
        session["status"] = "failed"
        session["intervention_status"] = "stop_loss"
        session["max_time_recorded"] = max_time
        session["notes"].append(f"Stop-loss intervention triggered at {max_time}s")
        logger.warning(f"Stop-loss triggered for participant {session['participant_id']}")
    return session

def handle_abandoned_records(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Mark records that have no end time or specific status as 'abandoned'.
    """
    for session in sessions:
        if session.get("status") == "in_progress" and session.get("session_end") is None:
            session["status"] = "abandoned"
            session["notes"].append("Marked as abandoned (no end time recorded)")
    return sessions

def save_dropouts(sessions: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Identify and count dropouts (abandoned or failed due to stop-loss).
    Returns a summary dict.
    """
    dropouts = [s for s in sessions if s.get("status") in ["abandoned", "failed"]]
    return {
        "total_dropouts": len(dropouts),
        "abandoned_count": len([s for s in dropouts if s.get("status") == "abandoned"]),
        "stop_loss_count": len([s for s in dropouts if s.get("intervention_status") == "stop_loss"])
    }

def export_raw_data(sessions: List[Dict[str, Any]]):
    """
    Main entry point for T020: Create raw data export function.
    This function ensures the final JSON structure is written to data/raw/participant_logs.json.
    """
    # Ensure directory exists
    ensure_data_directory()
    
    # The 'sessions' list is expected to be passed in from the main orchestration
    # or loaded if this is a standalone export utility.
    # For this task, we assume the caller has collected the sessions.
    
    # Update checksums for each session if not already done (defensive)
    for s in sessions:
        update_checksums(s)
    
    # Save to file
    save_logs(sessions)
    
    # Return the path for verification
    return str(PARTICIPANT_LOGS_PATH)

def main():
    """
    Main function for testing the data collection and export pipeline.
    Simulates a mock experiment run to verify T020 functionality.
    """
    logger.info("Starting data collection mock run for T020 verification.")
    
    # 1. Ensure directories
    ensure_data_directory()
    
    # 2. Simulate participants
    num_participants = 5
    sessions = []
    
    for i in range(num_participants):
        # Assign
        assignment = assign_participant(i, mode='mock')
        
        # Start session
        session = log_session_start(assignment['participant_id'], assignment['condition'])
        
        # Simulate some activity
        # Random questions
        num_questions = random.randint(0, 3)
        for _ in range(num_questions):
            log_help_request(session, f"Mock question {random.randint(100, 999)}")
        
        # Random task time (some might trigger stop loss)
        task_time = random.randint(600, 3000)
        session['task_time_seconds'] = task_time
        
        # Apply stop loss if needed
        session = apply_stop_loss_intervention(session)
        
        # Random rating
        if session['status'] != 'failed':
            rating = random.randint(1, 5)
            capture_helpfulness_survey(session, rating)
            session = log_session_end(session, "completed")
        else:
            session = log_session_end(session, "failed")
        
        sessions.append(session)
    
    # 3. Handle abandoned (none in this mock, but good to have)
    sessions = handle_abandoned_records(sessions)
    
    # 4. Export
    output_path = export_raw_data(sessions)
    
    # 5. Report
    dropout_summary = save_dropouts(sessions)
    logger.info(f"Export complete. Output: {output_path}")
    logger.info(f"Dropout Summary: {dropout_summary}")
    
    print(f"T020 Verification: Successfully wrote {output_path}")
    return output_path

if __name__ == "__main__":
    main()
