import os
import sys
import logging
import re
from pathlib import Path
from utils import setup_logging, ensure_dir, safe_write_csv

logger = logging.getLogger(__name__)

def parse_excluded_subjects_from_log(log_path: str) -> set:
    """Parse excluded subject IDs from a log file."""
    excluded = set()
    if not os.path.exists(log_path):
        return excluded
    
    with open(log_path, 'r') as f:
        for line in f:
            # Look for patterns like "Subject 100307 excluded"
            match = re.search(r'Subject\s+(\d+)\s+excluded', line)
            if match:
                excluded.add(match.group(1))
    
    return excluded

def get_all_subjects_from_logs(log_dir: str) -> dict:
    """
    Collect all subject information from log files.
    Returns dict: {subject_id: {'status': 'valid'/'excluded', 'reason': str}}
    """
    subjects = {}
    log_dir_path = Path(log_dir)
    
    if not log_dir_path.exists():
        return subjects
    
    # Parse motion exclusions
    motion_log = log_dir_path / "motion_exclusions.log"
    if motion_log.exists():
        excluded = parse_excluded_subjects_from_log(str(motion_log))
        for sub_id in excluded:
            subjects[sub_id] = {'status': 'excluded', 'reason': 'motion'}
    
    # Parse parcel quality issues
    parcel_log = log_dir_path / "parcel_quality.log"
    if parcel_log.exists():
        with open(parcel_log, 'r') as f:
            for line in f:
                match = re.search(r'Subject\s+(\d+)', line)
                if match:
                    sub_id = match.group(1)
                    if sub_id not in subjects:
                        subjects[sub_id] = {'status': 'valid', 'reason': ''}
                    subjects[sub_id]['status'] = 'invalid_parcels'
                    subjects[sub_id]['reason'] = 'high_nan_count'
    
    return subjects

def main():
    """Main entry point for persisting valid subjects."""
    log_dir = "data/logs"
    processed_dir = "data/processed"
    
    ensure_dir(log_dir)
    ensure_dir(processed_dir)
    
    # Get all subject statuses
    all_subjects = get_all_subjects_from_logs(log_dir)
    
    # Filter valid subjects
    valid_subjects = [sub_id for sub_id, info in all_subjects.items() 
                     if info['status'] == 'valid']
    
    # If no subjects found in logs, assume all are valid (placeholder logic)
    if not valid_subjects and all_subjects:
        # Fallback: if we have excluded subjects, the rest are valid
        excluded = {sub_id for sub_id, info in all_subjects.items() 
                   if info['status'] != 'valid'}
        # In a real scenario, we'd have a list of all available subjects
        # For now, we'll just use the excluded ones as a reference
        logger.warning("No explicitly valid subjects found in logs. Using exclusion list.")
    
    # Write valid subjects to CSV
    output_path = Path(processed_dir) / "valid_subjects.csv"
    import pandas as pd
    df = pd.DataFrame({"subject_id": valid_subjects})
    safe_write_csv(df, str(output_path))
    
    logger.info(f"Persisted {len(valid_subjects)} valid subjects to {output_path}")

if __name__ == "__main__":
    main()
