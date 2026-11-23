"""
Backend API for Participant Interaction Data Collection.

Handles submissions, manages session state, and applies Latin-square assignment logic.
Depends on T007 (Base data models) and T020 (Assignment logic).
"""
import os
import sys
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.models import Participant, Task, InteractionLog
from utils.assignment_generator import assign_conditions, generate_cohort_assignments
from utils.config_manager import get_config
from utils.logging_utils import get_logger
from utils.hash_artifacts import hash_file

logger = get_logger(__name__)

# Constants
CONDITIONS = ["baseline", "llm_sim", "rule"]
SESSION_FILE = "data/interaction_logs/session_state.json"
ASSIGNMENT_FILE = "data/interaction_logs/assignments.json"
LOGS_FILE = "data/interaction_logs/raw_logs.csv"

def ensure_directories():
    """Ensure required data directories exist."""
    dirs = [
        "data/interaction_logs",
        "data/summaries",
        "data/defects4j"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def load_or_create_session_state() -> Dict[str, Any]:
    """Load existing session state or initialize a new one."""
    ensure_directories()
    session_path = Path(SESSION_FILE)
    if session_path.exists():
        with open(session_path, 'r') as f:
            return json.load(f)
    else:
        return {
            "sessions": {},
            "cohort_size": 0,
            "assignments": []
        }

def save_session_state(state: Dict[str, Any]):
    """Persist session state to disk."""
    ensure_directories()
    session_path = Path(SESSION_FILE)
    with open(session_path, 'w') as f:
        json.dump(state, f, indent=2)

def generate_participant_id() -> str:
    """Generate a unique participant ID."""
    return f"P-{uuid.uuid4().hex[:8].upper()}"

def register_participant(cohort_size: int) -> Tuple[str, List[str]]:
    """
    Register a new participant and assign conditions based on Latin-square design.
    
    Args:
        cohort_size: The intended total size of the cohort.
        
    Returns:
        Tuple of (participant_id, list of assigned conditions in order)
    """
    state = load_or_create_session_state()
    
    # If no assignments exist yet, generate them for the cohort
    if not state["assignments"]:
        logger.info(f"Generating Latin-square assignments for cohort size {cohort_size}")
        assignments = generate_cohort_assignments(cohort_size, CONDITIONS)
        state["assignments"] = assignments
        state["cohort_size"] = cohort_size
        save_session_state(state)
        logger.info(f"Generated {len(assignments)} assignments")
    
    # Assign the next available slot
    current_count = len(state["sessions"])
    if current_count >= len(state["assignments"]):
        logger.warning(f"Cohort full. Current: {current_count}, Max: {len(state['assignments'])}")
        raise ValueError("Cohort is full. No more participants can be registered.")
    
    participant_id = generate_participant_id()
    assigned_conditions = state["assignments"][current_count]["conditions"]
    
    state["sessions"][participant_id] = {
        "registered_at": datetime.utcnow().isoformat(),
        "conditions": assigned_conditions,
        "tasks_completed": 0,
        "status": "active"
    }
    
    save_session_state(state)
    logger.info(f"Registered participant {participant_id} with conditions {assigned_conditions}")
    
    return participant_id, assigned_conditions

def get_participant_session(participant_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve session details for a participant."""
    state = load_or_create_session_state()
    return state["sessions"].get(participant_id)

def validate_submission(participant_id: str, submission: Dict[str, Any]) -> bool:
    """
    Validate an interaction submission.
    
    Required fields: task_id, condition, timestamp_ms, selected_line, ground_truth_line
    """
    required_fields = ["task_id", "condition", "timestamp_ms", "selected_line", "ground_truth_line"]
    for field in required_fields:
        if field not in submission:
            logger.error(f"Missing required field: {field}")
            return False
    
    session = get_participant_session(participant_id)
    if not session:
        logger.error(f"Invalid participant ID: {participant_id}")
        return False
    
    if session["status"] != "active":
        logger.error(f"Participant {participant_id} is not active")
        return False
    
    if submission["condition"] not in session["conditions"]:
        logger.error(f"Invalid condition {submission['condition']} for participant {participant_id}")
        return False
    
    # Validate timestamp precision (basic check)
    if not isinstance(submission["timestamp_ms"], (int, float)):
        logger.error("timestamp_ms must be numeric")
        return False
        
    return True

def log_interaction(participant_id: str, submission: Dict[str, Any]) -> bool:
    """
    Log a participant interaction to the raw logs CSV.
    
    Args:
        participant_id: The participant's unique ID
        submission: Dictionary containing interaction data
        
    Returns:
        True if successful, False otherwise
    """
    if not validate_submission(participant_id, submission):
        return False
    
    try:
        # Prepare log entry
        log_entry = {
            "participant_id": participant_id,
            "task_id": submission["task_id"],
            "condition": submission["condition"],
            "timestamp_ms": submission["timestamp_ms"],
            "selected_line": submission["selected_line"],
            "ground_truth_line": submission["ground_truth_line"],
            "logged_at": datetime.utcnow().isoformat()
        }
        
        # Append to CSV
        ensure_directories()
        logs_path = Path(LOGS_FILE)
        file_exists = logs_path.exists()
        
        with open(logs_path, 'a', newline='') as f:
            import csv
            writer = csv.DictWriter(f, fieldnames=log_entry.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(log_entry)
        
        # Update session state
        state = load_or_create_session_state()
        if participant_id in state["sessions"]:
            state["sessions"][participant_id]["tasks_completed"] += 1
            save_session_state(state)
        
        logger.info(f"Logged interaction for {participant_id}, task {submission['task_id']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to log interaction: {str(e)}")
        return False

def complete_participant_session(participant_id: str) -> bool:
    """Mark a participant's session as complete."""
    state = load_or_create_session_state()
    if participant_id in state["sessions"]:
        state["sessions"][participant_id]["status"] = "completed"
        state["sessions"][participant_id]["completed_at"] = datetime.utcnow().isoformat()
        save_session_state(state)
        logger.info(f"Completed session for participant {participant_id}")
        return True
    return False

def get_cohort_summary() -> Dict[str, Any]:
    """Get summary statistics of the current cohort."""
    state = load_or_create_session_state()
    
    total = len(state["sessions"])
    active = sum(1 for s in state["sessions"].values() if s["status"] == "active")
    completed = sum(1 for s in state["sessions"].values() if s["status"] == "completed")
    
    return {
        "total_participants": total,
        "active_participants": active,
        "completed_participants": completed,
        "cohort_size_target": state["cohort_size"],
        "assignments_generated": len(state["assignments"]) > 0
    }

def main():
    """
    Main entry point for testing the participant API.
    Simulates a full study flow: register, log interactions, complete.
    """
    print("=== Participant API Test ===")
    
    # Initialize with a small cohort
    cohort_size = 3
    print(f"Registering {cohort_size} participants...")
    
    registered_ids = []
    for i in range(cohort_size):
        pid, conditions = register_participant(cohort_size)
        registered_ids.append(pid)
        print(f"  Participant {pid} assigned: {conditions}")
    
    # Simulate interactions
    print("\nSimulating interactions...")
    tasks = ["task_001", "task_002", "task_003"]
    
    for pid in registered_ids:
        session = get_participant_session(pid)
        conditions = session["conditions"]
        
        for idx, task_id in enumerate(tasks):
            condition = conditions[idx % len(conditions)]
            submission = {
                "task_id": task_id,
                "condition": condition,
                "timestamp_ms": int(datetime.utcnow().timestamp() * 1000),
                "selected_line": 15,
                "ground_truth_line": 18
            }
            
            success = log_interaction(pid, submission)
            print(f"  {pid} - {task_id} ({condition}): {'OK' if success else 'FAIL'}")
        
        complete_participant_session(pid)
    
    # Summary
    summary = get_cohort_summary()
    print(f"\nCohort Summary: {json.dumps(summary, indent=2)}")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main()