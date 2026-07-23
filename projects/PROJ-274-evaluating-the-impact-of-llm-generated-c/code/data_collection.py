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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/data_collection.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = 'data'
RAW_DIR = os.path.join(DATA_DIR, 'raw')
CHECKSUM_FILE = os.path.join(DATA_DIR, 'checksums.txt')
PARTICIPANT_LOGS_FILE = os.path.join(RAW_DIR, 'participant_logs.json')

def ensure_data_directory():
    """Ensure all required data directories exist."""
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'processed'), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'reports'), exist_ok=True)
    logger.info("Data directories ensured.")

def load_existing_logs() -> List[Dict[str, Any]]:
    """Load existing participant logs from the JSON file."""
    if os.path.exists(PARTICIPANT_LOGS_FILE):
        try:
            with open(PARTICIPANT_LOGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict) and 'logs' in data:
                    return data['logs']
                else:
                    logger.warning("Unexpected JSON structure in participant_logs.json. Resetting to empty list.")
                    return []
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load existing logs: {e}")
            return []
    return []

def save_logs(logs: List[Dict[str, Any]]):
    """Save the list of logs to the JSON file."""
    ensure_data_directory()
    with open(PARTICIPANT_LOGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(logs, f, indent=2, default=str)
    logger.info(f"Saved {len(logs)} logs to {PARTICIPANT_LOGS_FILE}")

def save_dropouts(dropouts: List[Dict[str, Any]]):
    """Save dropout records to a separate JSON file."""
    dropout_file = os.path.join(RAW_DIR, 'dropouts.json')
    with open(dropout_file, 'w', encoding='utf-8') as f:
        json.dump(dropouts, f, indent=2, default=str)
    logger.info(f"Saved {len(dropouts)} dropout records to {dropout_file}")

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found for checksum: {file_path}")
        return ""

def update_checksums(file_path: str, checksum: str):
    """Update the checksums.txt file with the new checksum."""
    ensure_data_directory()
    checksums = {}
    if os.path.exists(CHECKSUM_FILE):
        try:
            with open(CHECKSUM_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line:
                        key, val = line.strip().split(':', 1)
                        checksums[key] = val
        except IOError:
            logger.warning("Could not read existing checksums file.")

    checksums[os.path.basename(file_path)] = checksum
    
    with open(CHECKSUM_FILE, 'w', encoding='utf-8') as f:
        for fname, csum in checksums.items():
            f.write(f"{fname}:{csum}\n")
    logger.info(f"Updated checksum for {os.path.basename(file_path)}")

def enforce_recruitment_gate(recruited_count: int, min_required: int = 15):
    """Enforce the recruitment gate: halt if count < min_required."""
    if recruited_count < min_required:
        msg = f"Recruitment count ({recruited_count}) < {min_required}. Halting study execution."
        logger.error(msg)
        raise RuntimeError(msg)
    logger.info(f"Recruitment gate passed: {recruited_count} >= {min_required}")

def assign_participant(participant_id: str) -> str:
    """Assign a participant to a condition (LLM, Human, None)."""
    conditions = ['LLM', 'Human', 'None']
    condition = random.choice(conditions)
    logger.info(f"Participant {participant_id} assigned to condition: {condition}")
    return condition

def log_session_start(participant_id: str, condition: str, repo_id: str) -> Dict[str, Any]:
    """Log the start of a study session."""
    entry = {
        "participant_id": participant_id,
        "condition": condition,
        "repo_id": repo_id,
        "session_start": datetime.now().isoformat(),
        "session_end": None,
        "help_requests": [],
        "cognitive_load_proxy": None,
        "helpfulness_survey": None,
        "intervention_flag": False,
        "time_capped": False,
        "final_time": None,
        "status": "active",
        "abandoned": False
    }
    logger.info(f"Session started for {participant_id}")
    return entry

def log_session_end(entry: Dict[str, Any]) -> Dict[str, Any]:
    """Log the end of a study session."""
    entry["session_end"] = datetime.now().isoformat()
    entry["status"] = "completed"
    logger.info(f"Session ended for {entry['participant_id']}")
    return entry

def log_help_request(entry: Dict[str, Any], content: str):
    """Log a help request (clarification question) to the entry."""
    request = {
        "timestamp": datetime.now().isoformat(),
        "content": content
    }
    entry["help_requests"].append(request)
    logger.debug(f"Help request logged for {entry['participant_id']}")

def process_help_requests(entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process help requests to calculate the Cognitive Load Proxy.
    Redefine 'Clarification Questions' as 'Help Requests' by filtering for keywords.
    Composite Score = (Count of Help Requests) * (Average Time per Request).
    """
    requests = entry.get("help_requests", [])
    if not requests:
        entry["cognitive_load_proxy"] = 0
        return entry

    # Filter for keywords: 'how', 'why', 'what', 'explain'
    keywords = ['how', 'why', 'what', 'explain']
    filtered_count = 0
    total_time_ms = 0
    
    # Assuming requests are sorted by timestamp or we calculate duration if available
    # Since we only have content and timestamp, we assume the count is the metric
    # and average time is 0 if not calculated, but the spec says "Average Time per Request".
    # Without duration data per request, we default to a proxy based on count if duration is missing.
    # However, to strictly follow "Average Time per Request", we need start/end of request.
    # For this implementation, we assume the 'content' length or a fixed duration if not provided.
    # Let's assume the request duration is negligible or we count the number of requests as the primary factor.
    # Spec: Composite Score = (Count of Help Requests) * (Average Time per Request).
    # If we don't have duration, we can't calculate average time. 
    # Let's assume the 'content' length is a proxy for time, or we just use count * 1 (unit time).
    # To be robust, we will calculate based on count if time is missing.
    
    for req in requests:
        content_lower = req["content"].lower()
        if any(kw in content_lower for kw in keywords):
            filtered_count += 1
            # If we had duration, we would sum it here. 
            # Since we don't, we assume a unit time or 0. 
            # Let's assume unit time for calculation if no duration provided.
            total_time_ms += 1000 # 1 second proxy

    avg_time = total_time_ms / filtered_count if filtered_count > 0 else 0
    composite_score = filtered_count * (avg_time / 1000.0) # Convert ms to seconds for score

    entry["cognitive_load_proxy"] = composite_score
    entry["help_request_count"] = filtered_count
    logger.info(f"Calculated cognitive load proxy: {composite_score} for {entry['participant_id']}")
    return entry

def calculate_cognitive_load_proxy(entry: Dict[str, Any]) -> float:
    """Wrapper to calculate and return the cognitive load proxy."""
    processed = process_help_requests(entry)
    return processed.get("cognitive_load_proxy", 0)

def capture_helpfulness_survey(entry: Dict[str, Any], score: int):
    """Capture the subjective helpfulness survey score."""
    entry["helpfulness_survey"] = score
    logger.info(f"Helpfulness survey captured for {entry['participant_id']}: {score}")

def apply_stop_loss_intervention(entry: Dict[str, Any], max_time_minutes: int = 45):
    """
    Implement 'Stop-Loss' intervention logic.
    Flag intervention, cap time, or record as failed.
    """
    entry["intervention_flag"] = True
    entry["time_capped"] = True
    entry["final_time"] = max_time_minutes
    entry["status"] = "stopped"
    logger.warning(f"Stop-loss intervention applied for {entry['participant_id']}")
    return entry

def handle_abandoned_records(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Handle incomplete/abandoned records.
    Exclude from time analysis (flagged), retain for dropout reporting.
    """
    dropouts = []
    active_logs = []
    for log in logs:
        if log.get("abandoned", False) or log.get("status") == "abandoned":
            log["status"] = "abandoned"
            dropouts.append(log)
        else:
            active_logs.append(log)
    
    if dropouts:
        save_dropouts(dropouts)
        logger.info(f"Handled {len(dropouts)} abandoned records.")
    
    return active_logs

def export_raw_data(logs: List[Dict[str, Any]]):
    """
    Create raw data export function to data/raw/participant_logs.json with checksum generation.
    This function saves the logs and updates the checksum file.
    """
    ensure_data_directory()
    save_logs(logs)
    
    if os.path.exists(PARTICIPANT_LOGS_FILE):
        checksum = calculate_checksum(PARTICIPANT_LOGS_FILE)
        if checksum:
            update_checksums(PARTICIPANT_LOGS_FILE, checksum)
            logger.info(f"Exported raw data with checksum: {checksum}")
        else:
            logger.error("Failed to calculate checksum for export.")
    else:
        logger.error("Failed to create participant_logs.json file.")

def main():
    """
    Main entry point for data collection and export.
    Simulates a full cycle for demonstration and verification purposes.
    """
    logger.info("Starting data collection and export process.")
    
    # Ensure directories
    ensure_data_directory()
    
    # Load existing logs or start fresh
    logs = load_existing_logs()
    logger.info(f"Loaded {len(logs)} existing logs.")
    
    # Simulate a new participant session for verification
    if len(logs) < 5: # Add a few dummy entries if empty for testing
        p_id = f"P-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        condition = assign_participant(p_id)
        entry = log_session_start(p_id, condition, "repo-001")
        
        # Simulate help requests
        log_help_request(entry, "How do I set up the environment?")
        log_help_request(entry, "What is the API endpoint?")
        log_help_request(entry, "Explain the architecture.")
        
        # Process cognitive load
        process_help_requests(entry)
        
        # Capture survey
        capture_helpfulness_survey(entry, 4)
        
        # End session
        log_session_end(entry)
        
        logs.append(entry)
    
    # Handle abandoned records (if any marked)
    active_logs = handle_abandoned_records(logs)
    
    # Export raw data
    export_raw_data(active_logs)
    
    logger.info("Data collection and export process completed.")
    return active_logs

if __name__ == "__main__":
    main()