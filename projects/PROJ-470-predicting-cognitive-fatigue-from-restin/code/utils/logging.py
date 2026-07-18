import logging
import sys
from pathlib import Path
from datetime import datetime
import json
import csv

def get_logger(name):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def log_participant_exclusion(participant_id, reason):
    logger = get_logger("logging")
    logger.warning(f"Excluding participant {participant_id}: {reason}")
    # In a real implementation, write to CSV
    log_path = Path("logs/exclusion_log.csv")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_exists = log_path.exists() and log_path.stat().st_size > 0
    with open(log_path, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["participant_id", "reason", "timestamp"])
        writer.writerow([participant_id, reason, datetime.now().isoformat()])

def log_artifact_rejection(segment_id, reason):
    logger = get_logger("logging")
    logger.warning(f"Rejecting artifact {segment_id}: {reason}")

def save_rejection_summary(summary):
    # Save summary to JSON or CSV
    pass

def get_rejection_counts():
    return {}

def save_exclusion_log_csv(data):
    pass
