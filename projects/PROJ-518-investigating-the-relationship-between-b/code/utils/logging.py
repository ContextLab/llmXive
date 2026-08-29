import csv
import os
from pathlib import Path
from typing import Optional
from config import get_config

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Appends an exclusion log entry to data_exclusion_log.txt.
    
    Args:
        reason: Standardized reason code (MISSING_SCAN, MISSING_SCORE, HIGH_MOTION)
        subject_id: The ID of the excluded subject
    """
    config = get_config()
    log_path = Path(config.DATA_PATH) / "exclusion_log.csv"
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['subject_id', 'reason', 'timestamp'])
        
        import datetime
        timestamp = datetime.datetime.now().isoformat()
        writer.writerow([subject_id, reason, timestamp])