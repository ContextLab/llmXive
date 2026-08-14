import json
import os
import sys
import logging
import random
import hashlib
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_collection.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PARTICIPANT_LOGS_FILE = os.path.join(RAW_DIR, "participant_logs.json")
CHECKSUM_FILE = os.path.join(DATA_DIR, "checksums.txt")

def ensure_data_directory():
    """Ensure the data directories exist."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

def calculate_checksum(data: str) -> str:
    """Calculate SHA256 checksum of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def update_checksums(file_path: str, checksum: str, artifact_name: str):
    """Update the checksums file with a new entry."""
    os.makedirs(os.path.dirname(CHECKSUM_FILE), exist_ok=True)
    timestamp = datetime.now().isoformat()
    entry = f"{artifact_name}:{file_path}:{checksum}:{timestamp}\n"
    
    with open(CHECKSUM_FILE, 'a') as f:
        f.write(entry)
    
    logger.info(f"Updated checksum for {artifact_name}: {checksum}")

def load_existing_logs() -> List[Dict[str, Any]]:
    """Load existing participant logs from file."""
    if os.path.exists(PARTICIPANT_LOGS_FILE):
        with open(PARTICIPANT_LOGS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Existing participant_logs.json is corrupted. Starting fresh.")
                return []
    return []

def save_logs(logs: List[Dict[str, Any]]):
    """Save participant logs to file with checksum generation."""
    ensure_data_directory()
    
    # Serialize to JSON with consistent formatting
    json_content = json.dumps(logs, indent=2, ensure_ascii=False)
    
    # Write to file
    with open(PARTICIPANT_LOGS_FILE, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    # Calculate and record checksum
    checksum = calculate_checksum(json_content)
    update_checksums(PARTICIPANT_LOGS_FILE, checksum, "participant_logs.json")
    
    logger.info(f"Saved {len(logs)} participant logs to {PARTICIPANT_LOGS_FILE}")
    logger.info(f"Checksum: {checksum}")

def assign_participant(participant_id: str) -> Dict[str, str]:
    """Assign a participant to a condition (LLM, Human, or None)."""
    conditions = ["LLM", "Human", "None"]
    condition = random.choice(conditions)
    
    return {
        "participant_id": participant_id,
        "condition": condition,
        "assigned_at": datetime.now().isoformat()
    }

def log_session_start(participant_id: str, condition: str) -> Dict[str, Any]:
    """Log the start of a participant session."""
    return {
        "participant_id": participant_id,
        "condition": condition,
        "session_start": datetime.now().isoformat(),
        "session_end": None,
        "help_requests": [],
        "helpfulness_rating": None,
        "intervention_flag": False,
        "time_capped": False,
        "final_time": None,
        "status": "in_progress",
        "abandoned": False
    }

def log_session_end(session_log: Dict[str, Any], final_time: float) -> Dict[str, Any]:
    """Log the end of a participant session."""
    session_log["session_end"] = datetime.now().isoformat()
    session_log["final_time"] = final_time
    session_log["status"] = "completed"
    return session_log

def log_help_request(session_log: Dict[str, Any], question_content: str) -> Dict[str, Any]:
    """Log a clarification question asked by a participant."""
    help_request = {
        "timestamp": datetime.now().isoformat(),
        "content": question_content
    }
    session_log["help_requests"].append(help_request)
    return session_log

def process_help_requests(session_log: Dict[str, Any]) -> int:
    """Process and count help requests for a session."""
    return len(session_log["help_requests"])

def capture_helpfulness_survey(session_log: Dict[str, Any], rating: int) -> Dict[str, Any]:
    """Capture the subjective helpfulness rating from a participant."""
    if not (1 <= rating <= 5):
        raise ValueError("Helpfulness rating must be between 1 and 5")
    session_log["helpfulness_rating"] = rating
    return session_log

def apply_stop_loss_intervention(session_log: Dict[str, Any], max_time_minutes: int = 60) -> Dict[str, Any]:
    """Apply stop-loss intervention if time exceeds limit."""
    # This would typically be called during analysis of session time
    # For now, it sets the flag and caps the time
    session_log["intervention_flag"] = True
    session_log["time_capped"] = True
    session_log["final_time"] = max_time_minutes * 60  # Convert to seconds
    session_log["status"] = "stopped"
    return session_log

def handle_abandoned_records(session_log: Dict[str, Any]) -> Dict[str, Any]:
    """Mark a session as abandoned."""
    session_log["abandoned"] = True
    session_log["status"] = "abandoned"
    # Note: Abandoned records are retained for dropout reporting but excluded from time analysis
    return session_log

def enforce_recruitment_gate(current_count: int, min_required: int = 15) -> bool:
    """Enforce the recruitment gate for the study."""
    if current_count < min_required:
        logger.warning(f"Recruitment count ({current_count}) < {min_required}; proceeding with variance estimation only for pilot")
    return True  # Allow study to continue in pilot mode

def save_dropouts(dropout_logs: List[Dict[str, Any]], output_path: str = None):
    """Save dropout records to a separate file."""
    if not output_path:
        output_path = os.path.join(RAW_DIR, "dropout_logs.json")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    json_content = json.dumps(dropout_logs, indent=2, ensure_ascii=False)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    checksum = calculate_checksum(json_content)
    update_checksums(output_path, checksum, "dropout_logs.json")
    
    logger.info(f"Saved {len(dropout_logs)} dropout records to {output_path}")

def export_raw_data(logs: List[Dict[str, Any]], output_path: str = None):
    """
    Export raw participant logs to the specified output path with checksum generation.
    This is the main function for T020: Create raw data export function.
    
    Args:
        logs: List of participant log dictionaries
        output_path: Path to write the JSON file (defaults to data/raw/participant_logs.json)
    """
    if output_path is None:
        output_path = PARTICIPANT_LOGS_FILE
    
    ensure_data_directory()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Serialize to JSON with consistent formatting
    json_content = json.dumps(logs, indent=2, ensure_ascii=False)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    
    # Calculate and record checksum
    checksum = calculate_checksum(json_content)
    update_checksums(output_path, checksum, os.path.basename(output_path))
    
    logger.info(f"Exported {len(logs)} participant logs to {output_path}")
    logger.info(f"Checksum: {checksum}")
    
    return {
        "path": output_path,
        "count": len(logs),
        "checksum": checksum,
        "timestamp": datetime.now().isoformat()
    }

def main():
    """
    Main entry point for data collection and export.
    Demonstrates the full flow of participant data collection and export.
    """
    logger.info("Starting data collection and export process...")
    
    # Ensure directories exist
    ensure_data_directory()
    
    # Load existing logs or start fresh
    logs = load_existing_logs()
    logger.info(f"Loaded {len(logs)} existing logs")
    
    # Simulate a few participants for demonstration
    # In a real scenario, this would be driven by the experiment runner
    if len(logs) == 0:
        logger.info("No existing logs found. Creating mock participants for demonstration.")
        
        for i in range(3):
            participant_id = f"PART-{1000 + i}"
            assignment = assign_participant(participant_id)
            session = log_session_start(participant_id, assignment["condition"])
            
            # Simulate some help requests
            if random.random() > 0.5:
                session = log_help_request(session, f"How do I set up the environment for {assignment['condition']}?")
                session = log_help_request(session, f"Why does the API return this error?")
            
            # Simulate a helpfulness rating
            rating = random.randint(1, 5)
            session = capture_helpfulness_survey(session, rating)
            
            # Simulate session completion time (in seconds)
            final_time = random.uniform(300, 3600)  # 5 to 60 minutes
            session = log_session_end(session, final_time)
            
            logs.append(session)
        
        # Enforce recruitment gate
        enforce_recruitment_gate(len(logs))
    
    # Export raw data
    export_result = export_raw_data(logs)
    
    logger.info(f"Data collection and export complete. Result: {export_result}")
    return export_result

if __name__ == "__main__":
    main()
