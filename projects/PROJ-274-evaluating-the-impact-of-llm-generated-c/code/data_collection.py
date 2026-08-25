import json
import os
import sys
import logging
import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.setup_paths import ensure_project_dirs

logger = logging.getLogger(__name__)

def ensure_data_directory(subdir="raw"):
    """Ensure the data directory structure exists."""
    ensure_project_dirs()
    data_dir = project_root / "data" / subdir
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def calculate_checksum(data):
    """Calculate SHA256 checksum of data."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    return hashlib.sha256(data).hexdigest()

def update_checksums(logs, output_file):
    """Update checksums in logs."""
    content = json.dumps(logs, sort_keys=True)
    checksum = calculate_checksum(content)
    return checksum

def load_existing_logs(file_path):
    """Load existing logs from a JSON file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                logger.warning(f"Corrupt log file at {file_path}, starting fresh.")
                return []
    return []

def save_logs(logs, file_path):
    """Save logs to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(logs, f, indent=2)
    logger.info(f"Saved logs to {file_path}")

def assign_participant(participant_list, condition_list):
    """Assign a participant to a condition."""
    if not participant_list or not condition_list:
        return None
    return {
        "participant_id": participant_list[0],
        "condition": random.choice(condition_list)
    }

def log_session_start(logs, participant_id, condition):
    """Log the start of a session."""
    event = {
        "event_type": "session_start",
        "participant_id": participant_id,
        "condition": condition,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logs.append(event)
    return event

def log_session_end(logs, participant_id, duration, status):
    """Log the end of a session."""
    event = {
        "event_type": "session_end",
        "participant_id": participant_id,
        "duration_seconds": duration,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    logs.append(event)
    return event

def apply_stop_loss_intervention(logs, participant_id, max_time=2700):
    """Apply stop-loss intervention if task time exceeds limit."""
    # Find the participant's records
    participant_records = [r for r in logs if r.get("participant_id") == participant_id]
    for record in participant_records:
        if record.get("status") == "completed":
            record["status"] = "failed"
            record["intervention_status"] = "stop_loss"
            record["max_time_applied"] = max_time
    return logs

def handle_abandoned_records(logs, participant_id, reason="Participant left early"):
    """Handle incomplete/abandoned records by flagging them."""
    # Find the participant's records
    participant_records = [r for r in logs if r.get("participant_id") == participant_id]
    for record in participant_records:
        if record.get("status") not in ["failed", "incomplete"]:
            record["status"] = "incomplete"
            record["intervention_status"] = "abandoned"
            record["abandonment_reason"] = reason
    return logs

def main():
    """Main entry point for data collection utilities."""
    print("Data collection utilities module.")

if __name__ == "__main__":
    main()