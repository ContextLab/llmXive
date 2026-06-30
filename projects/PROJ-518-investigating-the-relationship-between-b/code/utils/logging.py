import csv
import os
from pathlib import Path
from typing import Optional
from config import get_config

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Log an exclusion decision to a CSV file.

    Args:
        reason: The reason for exclusion (e.g., 'MISSING_SCAN', 'MISSING_SCORE', 'HIGH_MOTION').
        subject_id: The ID of the excluded subject.
    """
    config = get_config()
    project_root = Path(__file__).resolve().parent.parent.parent
    log_file = project_root / "data" / "interim" / "data_exclusion_log.txt"
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = os.path.exists(log_file)
    
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'reason', 'subject_id'])
        writer.writerow(['', reason, subject_id])