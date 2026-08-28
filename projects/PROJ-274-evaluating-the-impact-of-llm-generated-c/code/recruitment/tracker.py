"""
Recruitment Tracking System for Feasibility Pilot (N=15-20).

This module manages participant records for the study. It initializes the
data file with the correct schema and provides utilities to track recruitment
status. It does NOT perform actual human recruitment; that is a manual process.
"""
import json
import os
import sys
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path to allow imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.setup_paths import ensure_project_dirs

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# Constants
PARTICIPANT_DATA_PATH = "data/raw/participants_raw.json"
MAX_PILOT_SIZE = 20
MIN_PILOT_SIZE = 15
CONDITIONS = ["llm", "human", "none"]

def ensure_data_file_exists():
    """Ensure the data directory and file exist. Initialize with schema if empty."""
    # Ensure directory structure exists
    ensure_project_dirs()
    
    data_path = Path(PARTICIPANT_DATA_PATH)
    data_path.parent.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        logger.info(f"Initializing new participant data file at {data_path}")
        initial_data = {
            "metadata": {
                "version": "1.0",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "max_capacity": MAX_PILOT_SIZE,
                "min_required": MIN_PILOT_SIZE,
                "conditions": CONDITIONS,
                "description": "Feasibility Pilot Participant Tracker (N=15-20)"
            },
            "participants": []
        }
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        return True
    return False

def load_participants() -> Dict[str, Any]:
    """Load the current participant data from disk."""
    data_path = Path(PARTICIPANT_DATA_PATH)
    if not data_path.exists():
        ensure_data_file_exists()
    
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_participants(data: Dict[str, Any]):
    """Save participant data to disk."""
    data_path = Path(PARTICIPANT_DATA_PATH)
    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def add_participant_record(partial_record: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Add a new participant record to the tracker.
    
    If partial_record is provided, it merges with defaults.
    If not, creates a placeholder record with a generated ID.
    
    Returns the full new record.
    """
    data = load_participants()
    
    if len(data["participants"]) >= MAX_PILOT_SIZE:
        raise ValueError(f"Recruitment limit reached: {MAX_PILOT_SIZE} participants.")

    new_id = str(uuid.uuid4())
    default_record = {
        "participant_id": new_id,
        "status": "pending",  # pending, recruited, assigned, completed, dropped
        "condition": None,    # llm, human, none (assigned later)
        "recruited_at": None,
        "assigned_at": None,
        "completed_at": None,
        "notes": ""
    }

    if partial_record:
        # Merge provided fields, but keep generated ID if not provided
        if "participant_id" not in partial_record:
            partial_record["participant_id"] = new_id
        new_record = {**default_record, **partial_record}
    else:
        new_record = default_record

    data["participants"].append(new_record)
    save_participants(data)
    logger.info(f"Added participant record: {new_record['participant_id']}")
    return new_record

def get_participant_stats() -> Dict[str, Any]:
    """Return summary statistics of the current recruitment state."""
    data = load_participants()
    participants = data["participants"]
    
    total = len(participants)
    status_counts = {}
    condition_counts = {}
    
    for p in participants:
        status = p.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        
        cond = p.get("condition")
        if cond:
            condition_counts[cond] = condition_counts.get(cond, 0) + 1

    return {
        "total_recruited": total,
        "max_capacity": MAX_PILOT_SIZE,
        "min_required": MIN_PILOT_SIZE,
        "status_breakdown": status_counts,
        "condition_breakdown": condition_counts,
        "remaining_slots": MAX_PILOT_SIZE - total
    }

def validate_schema(data: Dict[str, Any]) -> bool:
    """
    Validate that the data structure matches the expected schema.
    Checks for required top-level keys and participant record structure.
    """
    required_keys = ["metadata", "participants"]
    if not all(k in data for k in required_keys):
        logger.error("Missing required top-level keys in participant data.")
        return False

    # Check metadata
    meta = data["metadata"]
    if "max_capacity" not in meta or meta["max_capacity"] != MAX_PILOT_SIZE:
        logger.error("Invalid metadata: max_capacity must be 20.")
        return False
    
    if "min_required" not in meta or meta["min_required"] != MIN_PILOT_SIZE:
        logger.error("Invalid metadata: min_required must be 15.")
        return False

    # Check participants structure
    for p in data["participants"]:
        if "participant_id" not in p:
            logger.error("Participant record missing 'participant_id'.")
            return False
        if "status" not in p:
            logger.error("Participant record missing 'status'.")
            return False

    return True

def main():
    """
    Main entry point for the tracker.
    Initializes the data file if missing and prints current stats.
    """
    logger.info("Recruitment Tracker System initialized.")
    
    # Ensure file exists
    ensure_data_file_exists()
    
    # Load and validate
    data = load_participants()
    if not validate_schema(data):
        logger.error("Schema validation failed. Please check the data file.")
        sys.exit(1)
    
    # Print stats
    stats = get_participant_stats()
    print(json.dumps(stats, indent=2))
    
    # If we have fewer than MIN_PILOT_SIZE, we might want to add placeholders
    # to demonstrate the system capacity, but we do NOT auto-recruit real humans.
    if stats["total_recruited"] < MIN_PILOT_SIZE:
        logger.info(f"Current recruitment ({stats['total_recruited']}) is below minimum required ({MIN_PILOT_SIZE}).")
        logger.info("Use add_participant_record() to manually add records as volunteers are recruited.")

if __name__ == "__main__":
    main()
