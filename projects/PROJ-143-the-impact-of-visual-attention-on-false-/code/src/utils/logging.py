"""
Logging utilities for exclusion reasons and study status.

Implements FR-011: Log exclusion reasons for ID mismatches.
"""
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json

# Ensure project root is in path if running as script
if __name__ == "__main__" and __package__ is None:
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

# Default paths relative to project root
DEFAULT_LOG_DIR = "data/processed"
EXCLUSION_LOG_FILENAME = "exclusion_log.json"
STUDY_STATUS_FILENAME = "study_status.json"


def get_log_path(filename: str = EXCLUSION_LOG_FILENAME) -> Path:
    """
    Get the full path for a log file, creating the directory if it doesn't exist.
    
    Args:
        filename: Name of the log file.
        
    Returns:
        Path object pointing to the log file.
    """
    # Determine project root relative to this file
    # Assuming structure: code/src/utils/logging.py -> root is code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    log_dir = project_root / DEFAULT_LOG_DIR
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    return log_dir / filename


def _load_existing_log(filepath: Path) -> list:
    """
    Load existing log entries from a JSON file, or return an empty list if file doesn't exist.
    
    Args:
        filepath: Path to the log file.
        
    Returns:
        List of existing log entries.
    """
    if not filepath.exists():
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError):
        return []


def log_exclusion(
    record_id: str,
    exclusion_reason: str,
    source: str = "linking",
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an exclusion reason for an ID mismatch or other data quality issue.
    
    Implements FR-011: Log exclusion reasons for ID mismatches.
    
    Args:
        record_id: The unique identifier of the excluded record (e.g., image_id, participant_id).
        exclusion_reason: A string describing why the record was excluded (e.g., "ID mismatch", "missing transcript").
        source: The module or process that triggered the exclusion (default: "linking").
        details: Optional dictionary with additional context (e.g., expected_id, actual_id).
    """
    filepath = get_log_path(EXCLUSION_LOG_FILENAME)
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "record_id": record_id,
        "exclusion_reason": exclusion_reason,
        "source": source,
        "details": details or {}
    }
    
    existing_logs = _load_existing_log(filepath)
    existing_logs.append(log_entry)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing_logs, f, indent=2, ensure_ascii=False)


def log_study_status(
    status: str,
    message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the overall status of the study (e.g., valid, invalid, incomplete).
    
    Args:
        status: The status string (e.g., "valid", "invalid", "pending").
        message: A descriptive message about the status.
        metadata: Optional dictionary with additional context (e.g., failure_rate, threshold).
    """
    filepath = get_log_path(STUDY_STATUS_FILENAME)
    
    status_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": status,
        "message": message,
        "metadata": metadata or {}
    }
    
    # Overwrite previous status (only keep the latest)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(status_entry, f, indent=2, ensure_ascii=False)