"""
Recruitment Tracking System for Feasibility Pilot Study.

Manages participant records for the N=15-20 feasibility pilot.
Implements the system to track recruitment without recruiting humans.
"""
import json
import os
import sys
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

# Ensure project paths are set up
try:
    from utils.setup_paths import ensure_project_dirs
except ImportError:
    # Fallback if running as module vs script
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.setup_paths import ensure_project_dirs

# Constants
PILOT_MIN_SIZE = 15
PILOT_MAX_SIZE = 20
CONDITIONS = ["LLM", "Human", "None"]
DATA_FILE = "data/raw/participants_raw.json"

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

def ensure_data_file_exists(file_path: str = DATA_FILE) -> None:
    """
    Ensure the data file and its directory exist.
    Initializes the file with the required schema if it doesn't exist.
    """
    ensure_project_dirs()
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not path.exists():
        logger.info(f"Initializing {file_path} with Feasibility Pilot schema (N={PILOT_MIN_SIZE}-{PILOT_MAX_SIZE})")
        initial_data = {
            "metadata": {
                "study_phase": "Feasibility Pilot",
                "total_capacity": PILOT_MAX_SIZE,
                "min_capacity": PILOT_MIN_SIZE,
                "conditions": CONDITIONS,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "version": "1.0"
            },
            "participants": []
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, indent=2)
        logger.info(f"Created {file_path} with empty participants array.")
    else:
        logger.info(f"Data file {file_path} already exists.")

def load_participants(file_path: str = DATA_FILE) -> Dict[str, Any]:
    """Load the participants data from the JSON file."""
    path = Path(file_path)
    if not path.exists():
        ensure_data_file_exists(file_path)
    
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_participants(data: Dict[str, Any], file_path: str = DATA_FILE) -> None:
    """Save the participants data to the JSON file."""
    path = Path(file_path)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    logger.info(f"Saved {len(data['participants'])} participant records to {file_path}")

def add_participant_record(file_path: str = DATA_FILE, 
                           condition: Optional[str] = None,
                           status: str = "pending") -> Dict[str, Any]:
    """
    Add a new participant record to the tracking system.
    Does NOT recruit the human; creates a placeholder for tracking.
    """
    if condition and condition not in CONDITIONS:
        raise ValueError(f"Invalid condition: {condition}. Must be one of {CONDITIONS}")
    
    data = load_participants(file_path)
    
    if len(data['participants']) >= data['metadata']['total_capacity']:
        raise ValueError(f"Recruitment limit reached: {data['metadata']['total_capacity']} participants.")
    
    new_participant = {
        "participant_id": str(uuid.uuid4()),
        "condition": condition,  # Assigned later by T014b logic
        "status": status,  # pending, recruited, completed, dropped
        "enrollment_date": None,
        "completion_date": None,
        "notes": ""
    }
    
    data['participants'].append(new_participant)
    save_participants(data, file_path)
    logger.info(f"Added new participant record: {new_participant['participant_id']}")
    return new_participant

def get_participant_stats(file_path: str = DATA_FILE) -> Dict[str, Any]:
    """Get statistics about current recruitment status."""
    data = load_participants(file_path)
    total = len(data['participants'])
    by_condition = {cond: 0 for cond in CONDITIONS}
    by_status = {}
    
    for p in data['participants']:
        cond = p.get('condition')
        if cond and cond in by_condition:
            by_condition[cond] += 1
        
        status = p.get('status', 'unknown')
        by_status[status] = by_status.get(status, 0) + 1
    
    return {
        "total_participants": total,
        "capacity": data['metadata']['total_capacity'],
        "by_condition": by_condition,
        "by_status": by_status,
        "remaining_capacity": data['metadata']['total_capacity'] - total
    }

def validate_schema(file_path: str = DATA_FILE) -> bool:
    """
    Validate that the data file matches the expected schema.
    Checks for metadata block and participants array structure.
    """
    try:
        data = load_participants(file_path)
        
        # Check top-level keys
        if 'metadata' not in data:
            logger.error("Missing 'metadata' key in data file.")
            return False
        if 'participants' not in data:
            logger.error("Missing 'participants' key in data file.")
            return False
        
        # Check metadata fields
        meta = data['metadata']
        required_meta = ['study_phase', 'total_capacity', 'min_capacity', 'conditions']
        for field in required_meta:
            if field not in meta:
                logger.error(f"Missing metadata field: {field}")
                return False
        
        # Check capacity constraints
        if not (PILOT_MIN_SIZE <= meta['total_capacity'] <= PILOT_MAX_SIZE):
            logger.error(f"Capacity {meta['total_capacity']} outside valid range [{PILOT_MIN_SIZE}, {PILOT_MAX_SIZE}]")
            return False
        
        # Check participants structure
        if not isinstance(data['participants'], list):
            logger.error("'participants' must be a list.")
            return False
        
        for i, p in enumerate(data['participants']):
            if 'participant_id' not in p:
                logger.error(f"Participant at index {i} missing 'participant_id'.")
                return False
        
        logger.info("Schema validation passed.")
        return True
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        return False

def main():
    """
    Main entry point for the recruitment tracker.
    Initializes the data file and prints current stats.
    """
    ensure_project_dirs()
    logger.info("Starting Recruitment Tracking System...")
    
    # Ensure file exists with correct schema
    ensure_data_file_exists()
    
    # Validate schema
    if not validate_schema():
        logger.error("Schema validation failed. Aborting.")
        sys.exit(1)
    
    # Print stats
    stats = get_participant_stats()
    print(json.dumps(stats, indent=2))
    
    logger.info("Recruitment Tracking System initialized successfully.")
    logger.info(f"Capacity: {stats['total_participants']}/{stats['capacity']}")
    logger.info(f"Remaining: {stats['remaining_capacity']}")

if __name__ == "__main__":
    main()
