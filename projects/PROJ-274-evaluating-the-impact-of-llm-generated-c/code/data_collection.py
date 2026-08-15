import json
import os
import sys
import logging
import random
import hashlib
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/data_collection.log')
    ]
)
logger = logging.getLogger(__name__)

DATA_DIR = "data/raw"
LOGS_FILE = os.path.join(DATA_DIR, "participant_logs.json")
CHECKSUMS_FILE = "data/checksums.txt"

# Keywords for automatic detection of clarification questions
CLARIFICATION_KEYWORDS = ['how', 'why', 'what', 'explain']

def ensure_data_directory():
    """Ensure the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"Data directory ensured: {DATA_DIR}")

def calculate_checksum(data: str) -> str:
    """Calculate SHA-256 checksum of a string."""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

def update_checksums(filename: str, content: str):
    """Update the checksums file with the new content's checksum."""
    checksum = calculate_checksum(content)
    with open(CHECKSUMS_FILE, 'a') as f:
        f.write(f"{filename}:{checksum}\n")
    logger.info(f"Updated checksum for {filename}: {checksum}")

def load_existing_logs() -> List[Dict[str, Any]]:
    """Load existing participant logs if the file exists."""
    if os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Existing logs file is corrupted. Starting fresh.")
                return []
    return []

def save_logs(logs: List[Dict[str, Any]]):
    """Save logs to the JSON file and update checksum."""
    ensure_data_directory()
    json_content = json.dumps(logs, indent=2, default=str)
    with open(LOGS_FILE, 'w') as f:
        f.write(json_content)
    update_checksums(LOGS_FILE, json_content)
    logger.info(f"Saved {len(logs)} logs to {LOGS_FILE}")

def assign_participant(participant_id: str, condition: str) -> Dict[str, Any]:
    """Assign a participant to a condition and create initial log entry."""
    return {
        "participant_id": participant_id,
        "condition": condition,
        "start_time": None,
        "end_time": None,
        "help_requests": [],  # List of {timestamp, content, moderator_tagged}
        "help_request_count": 0,
        "cognitive_load_proxy": 0.0,
        "subjective_rating": None,
        "status": "incomplete",
        "intervention_flag": False,
        "time_capped": False,
        "final_time": None
    }

def log_session_start(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Log the start of a session."""
    log_entry["start_time"] = datetime.now().isoformat()
    log_entry["status"] = "active"
    logger.info(f"Session started for participant {log_entry['participant_id']}")
    return log_entry

def log_session_end(log_entry: Dict[str, Any], status: str = "complete") -> Dict[str, Any]:
    """Log the end of a session."""
    log_entry["end_time"] = datetime.now().isoformat()
    log_entry["status"] = status
    logger.info(f"Session ended for participant {log_entry['participant_id']} with status: {status}")
    return log_entry

def log_help_request(log_entry: Dict[str, Any], content: str, moderator_tagged: bool = False) -> Dict[str, Any]:
    """
    Log a clarification question (help request).
    
    Protocol:
    - Timestamp is auto-generated.
    - Content is the text of the question.
    - moderator_tagged is a boolean set via the chat interface.
    
    This function also updates the help_request_count.
    """
    timestamp = datetime.now().isoformat()
    help_request = {
        "timestamp": timestamp,
        "content": content,
        "moderator_tagged": moderator_tagged
    }
    
    if "help_requests" not in log_entry:
        log_entry["help_requests"] = []
    
    log_entry["help_requests"].append(help_request)
    log_entry["help_request_count"] = len(log_entry["help_requests"])
    
    logger.info(f"Help request logged for {log_entry['participant_id']}: {content} (tagged: {moderator_tagged})")
    return log_entry

def process_help_requests(log_entry: Dict[str, Any], raw_messages: List[str]) -> Dict[str, Any]:
    """
    Process a list of raw messages to detect and log clarification questions.
    
    Detection Logic:
    - Filter for keywords: 'how', 'why', 'what', 'explain' (case-insensitive).
    - If a message contains any of these keywords, it is logged as a help request.
    
    Args:
        log_entry: The participant's log entry.
        raw_messages: List of message strings from the session.
        
    Returns:
        Updated log entry with help requests logged.
    """
    for msg in raw_messages:
        msg_lower = msg.lower()
        if any(keyword in msg_lower for keyword in CLARIFICATION_KEYWORDS):
            # Auto-detect based on keywords
            log_help_request(log_entry, msg, moderator_tagged=False)
            logger.debug(f"Auto-detected help request: {msg}")
    return log_entry

def calculate_cognitive_load_proxy(log_entry: Dict[str, Any], 
                                   avg_frequency: float = 2.0, 
                                   avg_deviation: float = 100.0) -> float:
    """
    Calculate the Cognitive Load Proxy score.
    
    Formula:
    cognitive_load_proxy = (question_frequency / avg_frequency) * 0.5 + 
                           (task_time_deviation / avg_deviation) * 0.5
    
    Where:
    - question_frequency = help_request_count
    - task_time_deviation = abs(final_time - expected_time) (simplified here to a placeholder logic
      since exact expected time isn't in the log, we use a normalized deviation if available, 
      otherwise default to 0).
    
    Note: In a full implementation, 'expected_time' would be passed or stored.
    For this task, we assume a normalized deviation of 0 if not explicitly set, 
    or we can derive it from start/end times if needed.
    
    To satisfy the task requirement of a "composite score", we calculate it based on:
    1. Normalized question frequency.
    2. Normalized time deviation (using duration vs a baseline).
    
    Args:
        log_entry: The participant's log entry.
        avg_frequency: Baseline average help request count (default 2.0).
        avg_deviation: Baseline average time deviation (default 100.0).
        
    Returns:
        Float representing the cognitive load proxy.
    """
    question_count = log_entry.get("help_request_count", 0)
    
    # Calculate task duration
    start_str = log_entry.get("start_time")
    end_str = log_entry.get("end_time")
    
    task_time_deviation = 0.0
    if start_str and end_str:
        try:
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str)
            duration_seconds = (end - start).total_seconds()
            # Assume a baseline expected duration (e.g., 30 minutes = 1800 seconds)
            expected_duration = 1800.0
            task_time_deviation = abs(duration_seconds - expected_duration)
        except (ValueError, TypeError):
            task_time_deviation = 0.0
    
    # Normalize and combine
    freq_norm = question_count / avg_frequency if avg_frequency > 0 else 0
    time_norm = task_time_deviation / avg_deviation if avg_deviation > 0 else 0
    
    # Weighted combination (50/50 as per typical proxy design)
    cognitive_load = (freq_norm * 0.5) + (time_norm * 0.5)
    
    return round(cognitive_load, 4)

def capture_helpfulness_survey(log_entry: Dict[str, Any], rating: int) -> Dict[str, Any]:
    """Capture the subjective helpfulness survey rating (1-5)."""
    if not (1 <= rating <= 5):
        raise ValueError("Rating must be between 1 and 5.")
    log_entry["subjective_rating"] = rating
    logger.info(f"Survey captured for {log_entry['participant_id']}: {rating}")
    return log_entry

def apply_stop_loss_intervention(log_entry: Dict[str, Any], max_time_minutes: int = 60) -> Dict[str, Any]:
    """
    Apply stop-loss intervention if time exceeds max_time_minutes.
    
    Sets intervention_flag=True, time_capped=True, and final_time.
    """
    start_str = log_entry.get("start_time")
    if not start_str:
        return log_entry
    
    try:
        start = datetime.fromisoformat(start_str)
        now = datetime.now()
        elapsed_minutes = (now - start).total_seconds() / 60.0
        
        if elapsed_minutes > max_time_minutes:
            log_entry["intervention_flag"] = True
            log_entry["time_capped"] = True
            log_entry["final_time"] = now.isoformat()
            log_entry["status"] = "stopped"
            logger.warning(f"Stop-loss intervention applied for {log_entry['participant_id']}")
    except (ValueError, TypeError):
        pass
    
    return log_entry

def handle_abandoned_records(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """Handle incomplete/abandoned records."""
    if log_entry["status"] == "active" and not log_entry.get("end_time"):
        log_entry["status"] = "incomplete"
        log_entry["dropout_count"] = 1
        logger.warning(f"Record marked as incomplete/abandoned: {log_entry['participant_id']}")
    return log_entry

def enforce_recruitment_gate(current_count: int, min_required: int = 15) -> bool:
    """
    Enforce the recruitment gate (N >= 15).
    
    If count < 15, log a WARNING but allow proceeding in pilot mode.
    Returns True if proceeding, False if hard block (not implemented per spec for pilot).
    """
    if current_count < min_required:
        logger.warning(f"Recruitment count ({current_count}) < {min_required}; proceeding with variance estimation only for pilot.")
    return True

def save_dropouts(logs: List[Dict[str, Any]]) -> int:
    """
    Calculate and log the dropout count in real-time.
    Returns the count of incomplete records.
    """
    dropout_count = sum(1 for log in logs if log.get("status") == "incomplete")
    logger.info(f"Current dropout count: {dropout_count}")
    return dropout_count

def export_raw_data(logs: List[Dict[str, Any]]):
    """Export raw data to the JSON file."""
    save_logs(logs)
    logger.info("Raw data exported successfully.")

def main():
    """
    Main function to demonstrate the help request logging and cognitive load proxy calculation.
    This script runs a mock session to verify the implementation of T016.
    """
    ensure_data_directory()
    logs = load_existing_logs()
    
    # Simulate a participant
    participant_id = "mock_participant_001"
    condition = "LLM"
    
    # Check if already exists
    existing = next((log for log in logs if log["participant_id"] == participant_id), None)
    if existing:
        log_entry = existing
    else:
        log_entry = assign_participant(participant_id, condition)
        logs.append(log_entry)
    
    # Start session
    log_entry = log_session_start(log_entry)
    
    # Simulate raw messages (some contain keywords, some don't)
    raw_messages = [
        "I understand the code.",
        "How does this function work?",  # Keyword: how
        "Can you explain the architecture?", # Keyword: explain
        "What is the purpose of this variable?", # Keyword: what
        "Why is this error happening?", # Keyword: why
        "This is just a statement without keywords."
    ]
    
    # Process messages to detect help requests
    log_entry = process_help_requests(log_entry, raw_messages)
    
    # Simulate a moderator tagging a specific question (e.g., the last one)
    # In a real interface, this would be set via the chat interface
    if log_entry["help_requests"]:
        last_request = log_entry["help_requests"][-1]
        last_request["moderator_tagged"] = True
        logger.info(f"Moderator tagged request: {last_request['content']}")
    
    # End session
    log_entry = log_session_end(log_entry, "complete")
    
    # Calculate Cognitive Load Proxy
    # We pass default averages, but in a real run these might be dynamic
    log_entry["cognitive_load_proxy"] = calculate_cognitive_load_proxy(log_entry)
    
    # Save logs
    export_raw_data(logs)
    
    # Verification output
    print(f"Participant: {participant_id}")
    print(f"Help Request Count: {log_entry['help_request_count']}")
    print(f"Cognitive Load Proxy: {log_entry['cognitive_load_proxy']}")
    print(f"Help Requests Details: {log_entry['help_requests']}")
    
    # Verify file exists
    if os.path.exists(LOGS_FILE):
        print(f"SUCCESS: {LOGS_FILE} created.")
    else:
        print(f"FAILURE: {LOGS_FILE} not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()