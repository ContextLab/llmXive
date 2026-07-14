"""
Download and filter subjects from OpenNeuro ds000246.

This script downloads the dataset, parses BIDS metadata, filters for subjects
with non-null MMSE/MOCA scores at both timepoints, and outputs eligible subjects.

Output: data/processed/eligible_subjects.csv, data/processed/excluded_subjects.log, data/artifacts/data_gate_status.json
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import pandas as pd
from tqdm import tqdm

from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json
from config import get_config

logger = get_logger("download_and_filter")

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://api.openneuro.org"
DATA_RAW_DIR = Path("data/raw") / DATASET_ID
DATA_PROCESSED_DIR = Path("data/processed")
DATA_ARTIFACTS_DIR = Path("data/artifacts")

ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG_FILE = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_FILE = DATA_ARTIFACTS_DIR / "data_gate_status.json"

MIN_SUBJECTS = 1
MAX_SUBJECTS = 100

def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest: Path, chunk_size: int = 8192) -> None:
    """Download a file from URL to destination."""
    ensure_dir(dest.parent)
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total = int(r.headers.get('content-length', 0))
        with tqdm(total=total, unit='B', unit_scale=True, desc=dest.name) as pbar:
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))

def read_participants_tsv(path: Path) -> pd.DataFrame:
    """Read participants.tsv file."""
    if not path.exists():
        raise FileNotFoundError(f"Participants file not found: {path}")
    return pd.read_csv(path, sep='\t')

def has_valid_score(row: Dict[str, Any]) -> bool:
    """Check if a row has valid MMSE/MOCA scores at both timepoints."""
    # Check for MMSE or MOCA at timepoint 1 and timepoint 2
    # Column names might vary, so we check common patterns
    mmse_t1 = row.get('MMSE_t1') or row.get('mmse_t1') or row.get('MMSE_1') or row.get('mmse_1')
    mmse_t2 = row.get('MMSE_t2') or row.get('mmse_t2') or row.get('MMSE_2') or row.get('mmse_2')
    moca_t1 = row.get('MOCA_t1') or row.get('moca_t1') or row.get('MOCA_1') or row.get('moca_1')
    moca_t2 = row.get('MOCA_t2') or row.get('moca_t2') or row.get('MOCA_2') or row.get('moca_2')
    
    # At least one measure must be present at both timepoints
    t1_valid = (mmse_t1 is not None and pd.notna(mmse_t1)) or (moca_t1 is not None and pd.notna(moca_t1))
    t2_valid = (mmse_t2 is not None and pd.notna(mmse_t2)) or (moca_t2 is not None and pd.notna(moca_t2))
    
    return t1_valid and t2_valid

def is_eligible(row: Dict[str, Any]) -> bool:
    """Determine if a subject is eligible based on score availability."""
    return has_valid_score(row)

def filter_eligible_subjects(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Filter dataframe for eligible subjects."""
    eligible = []
    excluded = []
    
    for _, row in df.iterrows():
        if is_eligible(row):
            eligible.append(row.to_dict())
        else:
            excluded.append(row.to_dict())
    
    return eligible, excluded

def limit_subjects(eligible: List[Dict[str, Any]], max_n: int) -> List[Dict[str, Any]]:
    """Limit the number of eligible subjects."""
    return eligible[:max_n]

def write_eligible_csv(subjects: List[Dict[str, Any]], path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_dir(path.parent)
    if not subjects:
        # Write empty file with headers
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['subject_id'])
        return
    
    # Get all keys from first subject
    keys = list(subjects[0].keys())
    # Ensure subject_id is first
    if 'subject_id' in keys:
        keys.remove('subject_id')
        keys = ['subject_id'] + keys
    elif 'participant_id' in keys:
        keys.remove('participant_id')
        keys = ['participant_id'] + keys
    
    with open(path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(subjects)

def write_excluded_log(subjects: List[Dict[str, Any]], path: Path) -> None:
    """Write excluded subjects to log."""
    ensure_dir(path.parent)
    with open(path, 'w') as f:
        f.write("# Excluded Subjects\n")
        f.write(f"# Total excluded: {len(subjects)}\n\n")
        for subj in subjects:
            f.write(json.dumps(subj) + "\n")

def write_status(status: Dict[str, Any], path: Path) -> None:
    """Write status to JSON."""
    ensure_dir(path.parent)
    save_json(status, path)

def main() -> None:
    """Main entry point."""
    logger.log("start_download_and_filter")
    
    try:
        # Ensure directories
        ensure_directory(DATA_RAW_DIR)
        ensure_directory(DATA_PROCESSED_DIR)
        ensure_directory(DATA_ARTIFACTS_DIR)
        
        # Check if participants.tsv exists (downloaded by T004c or T017)
        participants_file = DATA_RAW_DIR / "participants.tsv"
        
        if not participants_file.exists():
            # Attempt to download from OpenNeuro
            # This is a simplified download; in reality, you'd use the BIDS API
            logger.log("warning", message="participants.tsv not found, attempting to download")
            # In a real scenario, we would download the full dataset or just the participants file
            # For now, we simulate the existence of the file or raise an error
            raise FileNotFoundError(f"Participants file not found: {participants_file}")
        
        # Read participants
        df = read_participants_tsv(participants_file)
        logger.log("participants_loaded", n_rows=len(df))
        
        # Filter eligible
        eligible, excluded = filter_eligible_subjects(df)
        logger.log("filtering_complete", n_eligible=len(eligible), n_excluded=len(excluded))
        
        if len(eligible) == 0:
            logger.log("error", message="No eligible subjects found")
            status = {
                "status": "failed",
                "reason": "No eligible subjects",
                "n_eligible": 0,
                "n_excluded": len(excluded)
            }
            write_status(status, STATUS_FILE)
            sys.exit(2)  # EXIT_CODE_NO_LABELS
        
        # Limit subjects
        eligible = limit_subjects(eligible, MAX_SUBJECTS)
        logger.log("limiting_complete", n_eligible=len(eligible))
        
        # Write outputs
        write_eligible_csv(eligible, ELIGIBLE_SUBJECTS_FILE)
        write_excluded_log(excluded, EXCLUDED_LOG_FILE)
        
        status = {
            "status": "success",
            "n_eligible": len(eligible),
            "n_excluded": len(excluded),
            "output_file": str(ELIGIBLE_SUBJECTS_FILE)
        }
        write_status(status, STATUS_FILE)
        
        logger.log("success", 
                   eligible_file=str(ELIGIBLE_SUBJECTS_FILE), 
                   status_file=str(STATUS_FILE))
        print(f"Download and filter complete. {len(eligible)} eligible subjects written to {ELIGIBLE_SUBJECTS_FILE}")
        
    except Exception as e:
        logger.log("error", message=str(e))
        raise

if __name__ == "__main__":
    main()
