import csv
import os
from pathlib import Path
from typing import Optional
from config import get_config

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Appends a CSV row to data_exclusion_log.txt with the standardized reason code.
    
    Args:
        reason: The standardized reason code (e.g., 'MISSING_SCAN', 'MISSING_SCORE', 'HIGH_MOTION').
        subject_id: The ID of the excluded subject.
    """
    config = get_config()
    log_path = config.DATA_PATH / "exclusion_log.csv"
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['subject_id', 'reason', 'timestamp'])
        
        # In a real implementation, we would use datetime.datetime.now().isoformat()
        # For this task, we use a placeholder or current time if imported
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        writer.writerow([subject_id, reason, timestamp])
