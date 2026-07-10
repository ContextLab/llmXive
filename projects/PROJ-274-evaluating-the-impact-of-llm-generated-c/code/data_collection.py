import json
import os
import sys
import logging
import random
import hashlib
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
LOGS_FILE = os.path.join(RAW_DIR, "participant_logs.json")
DROPOUTS_FILE = os.path.join(RAW_DIR, "dropouts.json")
CHECKSUM_FILE = os.path.join(DATA_DIR, "checksums.txt")

def ensure_data_directory():
    """Ensure all required data directories exist."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "processed"), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, "reports"), exist_ok=True)
    logger.info(f"Data directories ensured at {DATA_DIR}")

def load_existing_logs() -> List[Dict[str, Any]]:
    """Load existing participant logs from the JSON file."""
    if not os.path.exists(LOGS_FILE):
        return []
    try:
        with open(LOGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load logs from {LOGS_FILE}: {e}")
        return []

def save_logs(logs: List[Dict[str, Any]]):
    """Save the list of participant logs to the JSON file."""
    with open(LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, default=str)
    logger.info(f"Saved {len(logs)} logs to {LOGS_FILE}")

def save_dropouts(dropouts: List[Dict[str, Any]]):
    """Save dropout records to the JSON file."""
    with open(DROPOUTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(dropouts, f, indent=2, default=str)
    logger.info(f"Saved {len(dropouts)} dropout records to {DROPOUTS_FILE}")

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"Checksum file not found: {file_path}")
        return "FILE_NOT_FOUND"

def update_checksums():
    """Generate checksums for all raw data files and append to checksums.txt."""
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Files to checksum
    files_to_checksum = [LOGS_FILE, DROPOUTS_FILE]
    
    with open(CHECKSUM_FILE, 'a', encoding='utf-8') as checksum_f:
        for file_path in files_to_checksum:
            if os.path.exists(file_path):
                checksum = calculate_checksum(file_path)
                timestamp = datetime.now().isoformat()
                line = f"{timestamp} | {os.path.basename(file_path)} | {checksum}\n"
                checksum_f.write(line)
                logger.info(f"Checksum generated for {file_path}: {checksum}")
            else:
                logger.warning(f"Skipping checksum for missing file: {file_path}")

def enforce_recruitment_gate(recruited_count: int, min_required: int = 15):
    """Enforce the minimum recruitment count before study execution."""
    if recruited_count < min_required:
        error_msg = f"Recruitment count < 15 (current: {recruited_count}). Aborting study."
        logger.error(error_msg)
        sys.exit(1)
    logger.info(f"Recruitment gate passed: {recruited_count} >= {min_required}")

def assign_participant(participant_id: str, condition: Optional[str] = None) -> Dict[str, Any]:
    """Assign a participant to a condition (LLM, Human, or None) if not specified."""
    conditions = ["LLM", "Human", "None"]
    if condition is None:
        condition = random.choice(conditions)
    
    return {
        "participant_id": participant_id,
        "condition": condition,
        "assigned_at": datetime.now().isoformat()
    }

def log_session_start(participant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Log the start of a study session."""
    participant_data["session_start"] = datetime.now().isoformat()
    participant_data["session_active"] = True
    participant_data["help_requests"] = []
    participant_data["time_on_task"] = 0
    logger.info(f"Session started for participant {participant_data.get('participant_id')}")
    return participant_data

def log_session_end(participant_data: Dict[str, Any]) -> Dict[str, Any]:
    """Log the end of a study session."""
    participant_data["session_end"] = datetime.now().isoformat()
    participant_data["session_active"] = False
    if "session_start" in participant_data:
        start = datetime.fromisoformat(participant_data["session_start"])
        end = datetime.fromisoformat(participant_data["session_end"])
        participant_data["time_on_task"] = (end - start).total_seconds()
    logger.info(f"Session ended for participant {participant_data.get('participant_id')}")
    return participant_data

def log_help_request(participant_data: Dict[str, Any], question: str, category: str = "general"):
    """Log a help request (clarification question) for a participant."""
    if "help_requests" not in participant_data:
        participant_data["help_requests"] = []
    
    request = {
        "timestamp": datetime.now().isoformat(),
        "content": question,
        "category": category
    }
    participant_data["help_requests"].append(request)
    logger.info(f"Help request logged for {participant_data.get('participant_id')}: {category}")

def process_help_requests(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process help requests to calculate cognitive load proxy."""
    for log in logs:
        if "help_requests" in log and log["help_requests"]:
            count = len(log["help_requests"])
            total_time = log.get("time_on_task", 0)
            # Avoid division by zero
            avg_time = (total_time / count) if count > 0 else 0
            log["cognitive_load_proxy"] = count * avg_time
        else:
            log["cognitive_load_proxy"] = 0
    return logs

def calculate_cognitive_load_proxy(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Alias for process_help_requests for backward compatibility."""
    return process_help_requests(logs)

def capture_helpfulness_survey(participant_data: Dict[str, Any], score: int, comment: str = "") -> Dict[str, Any]:
    """Capture subjective helpfulness survey results."""
    if not (1 <= score <= 5):
        logger.warning(f"Invalid survey score {score} for participant {participant_data.get('participant_id')}. Defaulting to 3.")
        score = 3
    
    participant_data["helpfulness_score"] = score
    participant_data["helpfulness_comment"] = comment
    logger.info(f"Helpfulness survey captured: {score}/5 for {participant_data.get('participant_id')}")
    return participant_data

def apply_stop_loss_intervention(participant_data: Dict[str, Any], max_time_minutes: int = 45):
    """Apply stop-loss intervention if time exceeds limit."""
    time_on_task = participant_data.get("time_on_task", 0)
    max_time_seconds = max_time_minutes * 60
    
    if time_on_task > max_time_seconds:
        participant_data["intervention_flag"] = True
        participant_data["time_capped"] = True
        participant_data["final_time"] = max_time_seconds
        participant_data["status"] = "capped"
        logger.warning(f"Stop-loss intervention applied for {participant_data.get('participant_id')}")
    return participant_data

def handle_abandoned_records(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Handle incomplete/abandoned records: exclude from time analysis, retain for dropout reporting."""
    dropouts = []
    valid_logs = []
    
    for log in logs:
        if log.get("session_active", False) or log.get("status") == "abandoned":
            log["status"] = "abandoned"
            dropouts.append(log)
            logger.info(f"Marked as abandoned: {log.get('participant_id')}")
        else:
            valid_logs.append(log)
    
    if dropouts:
        save_dropouts(dropouts)
    
    return valid_logs

def export_raw_data(logs: List[Dict[str, Any]]):
    """Export raw data to participant_logs.json and generate checksum."""
    ensure_data_directory()
    save_logs(logs)
    update_checksums()
    logger.info("Raw data export completed with checksum generation.")

def main():
    """
    Main entry point for data collection and export.
    This function demonstrates the full flow:
    1. Ensure directories
    2. Load existing logs (or start empty)
    3. Simulate a few participants (for testing the export function)
    4. Process help requests
    5. Apply interventions
    6. Export to raw data and generate checksum
    """
    ensure_data_directory()
    
    # Load existing or start fresh
    logs = load_existing_logs()
    
    # Simulate a mock participant if logs are empty (for demonstration of the export)
    # In a real run, this would be populated by the actual study loop.
    if not logs:
        logger.info("No existing logs found. Simulating 2 participants for export demonstration.")
        for i in range(2):
            p_id = f"PID-{datetime.now().strftime('%Y%m%d')}-{i:03d}"
            p_data = assign_participant(p_id)
            p_data = log_session_start(p_data)
            
            # Simulate some help requests
            log_help_request(p_data, "How do I install the dependencies?", "setup")
            log_help_request(p_data, "Why is this function returning None?", "api")
            
            # Simulate time on task (random between 10 and 60 minutes)
            p_data["time_on_task"] = random.uniform(10 * 60, 60 * 60)
            
            p_data = log_session_end(p_data)
            
            # Apply stop loss if needed
            p_data = apply_stop_loss_intervention(p_data)
            
            # Capture survey
            capture_helpfulness_survey(p_data, random.randint(1, 5))
            
            logs.append(p_data)
    
    # Process derived metrics
    logs = process_help_requests(logs)
    
    # Handle abandoned records (filter out active ones for final export if needed, 
    # but here we keep them for the raw export as per "retain for dropout reporting")
    # We filter out those that are truly active (session_active=True) to mark as abandoned
    logs = handle_abandoned_records(logs)
    
    # Export and checksum
    export_raw_data(logs)
    
    logger.info("Data collection simulation and export complete.")

if __name__ == "__main__":
    main()
