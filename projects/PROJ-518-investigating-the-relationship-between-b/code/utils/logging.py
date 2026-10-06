import csv
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import get_config

def log_exclusion(reason: str, subject_id: str) -> None:
    """
    Logs an exclusion event to the data exclusion log file.
    
    Args:
        reason: The standardized reason code (e.g., 'MISSING_SCAN', 'MISSING_SCORE', 'HIGH_MOTION').
        subject_id: The ID of the excluded subject.
        
    The log file is stored at: data/interim/data_exclusion_log.txt
    Format: CSV with columns: subject_id, reason, timestamp
    """
    config = get_config()
    log_path = Path(config.DATA_PATH) / "interim" / "data_exclusion_log.txt"
    
    # Ensure directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    
    file_exists = os.path.exists(log_path)
    
    with open(log_path, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['subject_id', 'reason', 'timestamp'])
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerow({
            'subject_id': subject_id,
            'reason': reason,
            'timestamp': timestamp
        })