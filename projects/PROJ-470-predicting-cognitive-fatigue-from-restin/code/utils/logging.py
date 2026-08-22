"""
Logging utilities for participant exclusion and artifact rejection.
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
import json
import csv
import os

# Ensure logs directory exists
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

EXCLUSION_LOG_PATH = LOGS_DIR / "exclusion_log.csv"

def get_logger(name):
    """Get a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_artifact_rejection(participant_id, reason, timestamp=None):
    """
    Log an artifact rejection event to the exclusion log CSV.
    """
    if timestamp is None:
        timestamp = datetime.now().isoformat()
    
    # Ensure header exists if file is new
    file_exists = os.path.exists(EXCLUSION_LOG_PATH)
    
    with open(EXCLUSION_LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['participant_id', 'reason', 'timestamp'])
        writer.writerow([participant_id, reason, timestamp])

def log_participant_exclusion(participant_id, reason, timestamp=None):
    """
    Log a participant exclusion event to the exclusion log CSV.
    """
    log_artifact_rejection(participant_id, reason, timestamp)

def save_rejection_summary(rejections):
    """
    Save a summary of rejections (optional).
    """
    summary_path = LOGS_DIR / "rejection_summary.json"
    with open(summary_path, 'w') as f:
        json.dump(rejections, f, indent=2)

def get_rejection_counts():
    """
    Read the exclusion log and return counts by reason.
    """
    if not os.path.exists(EXCLUSION_LOG_PATH):
        return {}
    
    counts = {}
    with open(EXCLUSION_LOG_PATH, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            reason = row['reason']
            counts[reason] = counts.get(reason, 0) + 1
    return counts

def save_exclusion_log_csv(data):
    """
    Save a list of exclusion records to the CSV.
    """
    file_exists = os.path.exists(EXCLUSION_LOG_PATH)
    with open(EXCLUSION_LOG_PATH, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['participant_id', 'reason', 'timestamp'])
        for record in data:
            writer.writerow([record['participant_id'], record['reason'], record['timestamp']])
