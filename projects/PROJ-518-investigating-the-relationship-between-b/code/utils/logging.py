import csv
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from config import get_config

# Standardized reason codes for exclusion logging
REASON_MISSING_SCAN = "MISSING_SCAN"
REASON_MISSING_SCORE = "MISSING_SCORE"
REASON_HIGH_MOTION = "HIGH_MOTION"

def log_exclusion(reason: str, subject_id: str, output_filename: Optional[str] = None) -> None:
    """
    Logs an exclusion decision to the data exclusion log file.
    
    Args:
        reason: The standardized reason code (e.g., MISSING_SCAN, MISSING_SCORE, HIGH_MOTION).
        subject_id: The ID of the excluded subject.
        output_filename: Optional override for the log filename. Defaults to 'data_exclusion_log.txt'.
    
    Raises:
        FileNotFoundError: If the config data path does not exist.
        IOError: If the log file cannot be written.
    """
    config = get_config()
    
    if output_filename is None:
        output_filename = "data_exclusion_log.txt"
    
    log_path = Path(config.DATA_PATH) / output_filename
    
    # Ensure the directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().isoformat()
    
    file_exists = os.path.isfile(log_path)
    
    with open(log_path, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        
        # Write header if file is new
        if not file_exists:
            writer.writerow(['subject_id', 'reason', 'timestamp'])
        
        writer.writerow([subject_id, reason, timestamp])
