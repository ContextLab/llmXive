"""
T017: Download ds000246, filter for longitudinal MMSE/MOCA, output eligible subjects.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Local imports matching API surface
from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
BASE_URL = "https://api.openneuro.org"
PARTICIPANTS_URL = f"{BASE_URL}/datasets/{DATASET_ID}/files/participants.tsv"
MAX_SUBJECTS = 100
EXIT_CODE_NO_ELIGIBLE = 3
EXIT_CODE_SUCCESS = 0

# Output paths
DATA_PROCESSED = Path("data/processed")
DATA_RAW = Path("data/raw")
DATA_ARTIFACTS = Path("data/artifacts")

ELIGIBLE_CSV = DATA_PROCESSED / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS / "data_gate_status.json"

logger = get_logger("download_and_filter")


@log_operation
def ensure_directory(dir_path: Path) -> None:
    """Ensure a directory exists."""
    dir_path.mkdir(parents=True, exist_ok=True)


@log_operation
def download_dataset_metadata(url: str, dest_path: Path, max_retries: int = 3) -> bool:
    """
    Download a file from OpenNeuro API.
    Returns True on success, False on failure.
    """
    for attempt in range(1, max_retries + 1):
        try:
            logger.log("download_attempt", url=url, attempt=attempt)
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.log("download_success", path=str(dest_path))
                return True
            else:
                logger.log("download_failed_status", status=response.status_code)
        except requests.exceptions.RequestException as e:
            logger.log("download_exception", error=str(e))
        
        if attempt < max_retries:
            time.sleep(2 ** attempt) # Exponential backoff

    return False


@log_operation
def read_participants_file(path: Path) -> List[Dict[str, Any]]:
    """
    Parse the participants.tsv file into a list of dictionaries.
    Handles both TSV and potential JSON/CSV variations if needed, but assumes TSV for ds000246.
    """
    if not path.exists():
        logger.log("file_missing", path=str(path))
        return []

    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        # Check if it's TSV or CSV
        first_line = f.readline()
        f.seek(0)
        
        delimiter = '\t' if '\t' in first_line else ','
        
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            rows.append(row)
    
    return rows


@log_operation
def has_valid_score(row: Dict[str, Any], score_col: str) -> bool:
    """
    Check if a specific score column exists and has a non-null numeric value.
    Handles 'NaN', 'n/a', 'null', empty strings.
    """
    if score_col not in row:
        return False
    
    val = row[score_col]
    if val is None:
        return False
    
    val_str = str(val).strip().lower()
    if val_str in ('', 'nan', 'n/a', 'null', 'none', '.'):
        return False
    
    try:
        float(val)
        return True
    except ValueError:
        return False


@log_operation
def is_eligible(row: Dict[str, Any]) -> bool:
    """
    Check if a subject has valid MMSE or MOCA scores at BOTH timepoints.
    Spec/Constitution requires longitudinal data.
    We look for columns like 'MMSE_t1', 'MMSE_t2' or 'MOCA_t1', 'MOCA_t2'.
    If specific timepoint columns don't exist, we check for generic 'MMSE' and 'MOCA'
    but require that the subject has at least two rows or the data indicates longitudinal structure.
    However, standard BIDS participants.tsv usually has one row per subject with wide-format columns.
    
    Strategy:
    1. Check for MMSE_t1, MMSE_t2 OR MOCA_t1, MOCA_t2.
    2. If those specific columns don't exist, check for 'MMSE' and 'MOCA' and assume if both exist,
       they represent the necessary data (or the dataset structure implies it). 
       But the task says "at both timepoints", so we strictly look for t1/t2 columns.
    """
    # Check for MMSE at t1 and t2
    mmse_t1 = has_valid_score(row, 'MMSE_t1') or has_valid_score(row, 'MMSE_T1')
    mmse_t2 = has_valid_score(row, 'MMSE_t2') or has_valid_score(row, 'MMSE_T2')
    
    # Check for MOCA at t1 and t2
    moca_t1 = has_valid_score(row, 'MOCA_t1') or has_valid_score(row, 'MOCA_T1')
    moca_t2 = has_valid_score(row, 'MOCA_t2') or has_valid_score(row, 'MOCA_T2')
    
    # Also check generic if timepoint columns are missing (fallback for some ds variations)
    # But strict interpretation: need both timepoints.
    # If the dataset uses 'MMSE' and 'MOCA' without suffixes, we might need to infer.
    # Let's assume standard wide format with t1/t2 suffixes as per typical longitudinal BIDS.
    
    if mmse_t1 and mmse_t2:
        return True
    if moca_t1 and moca_t2:
        return True
        
    # Fallback: if columns are just 'MMSE' and 'MOCA', we can't verify "both timepoints"
    # unless the dataset has multiple rows per subject (long format).
    # For ds000246, it's likely wide format. If t1/t2 are missing, we can't confirm eligibility.
    # So we strictly require t1/t2.
    
    return False


@log_operation
def filter_eligible_subjects(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter rows that are eligible."""
    return [row for row in rows if is_eligible(row)]


@log_operation
def limit_subjects(subjects: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """Limit the number of subjects to N."""
    return subjects[:limit]


@log_operation
def write_eligible_csv(subjects: List[Dict[str, Any]], path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_directory(path.parent)
    if not subjects:
        # Write empty file with header if possible, or just create it
        with open(path, 'w', newline='', encoding='utf-8') as f:
            pass # Empty file
        return

    # Use the keys from the first subject to determine headers
    headers = list(subjects[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(subjects)
    
    logger.log("eligible_csv_written", path=str(path), count=len(subjects))


@log_operation
def write_excluded_log(rows: List[Dict[str, Any]], path: Path) -> None:
    """Write excluded subjects to a log file."""
    ensure_directory(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 40 + "\n")
        for i, row in enumerate(rows):
            subj_id = row.get('participant_id', f'row_{i}')
            f.write(f"Subject: {subj_id}\n")
            f.write(f"  Reason: Missing required longitudinal scores (MMSE_t1/t2 or MOCA_t1/t2)\n")
            f.write(f"  Data: {row}\n")
            f.write("-" * 40 + "\n")
    
    logger.log("excluded_log_written", path=str(path), count=len(rows))


@log_operation
def write_status(eligible_count: int, excluded_count: int, error: Optional[str] = None) -> None:
    """Write the data gate status JSON."""
    ensure_directory(STATUS_JSON.parent)
    status = {
        "status": "success" if error is None else "error",
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(STATUS_JSON, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    
    logger.log("status_written", path=str(STATUS_JSON))


@log_operation
def main() -> int:
    """Main entry point for T017."""
    logger.log("start")
    
    # Ensure directories
    ensure_directory(DATA_PROCESSED)
    ensure_directory(DATA_RAW)
    ensure_directory(DATA_ARTIFACTS)
    
    # Download participants file
    participants_path = DATA_RAW / DATASET_ID / "participants.tsv"
    success = download_dataset_metadata(PARTICIPANTS_URL, participants_path)
    
    if not success:
        error_msg = f"Failed to download participants.tsv from {PARTICIPANTS_URL}"
        logger.log("fatal_error", error=error_msg)
        write_status(0, 0, error=error_msg)
        return EXIT_CODE_NO_ELIGIBLE
    
    # Parse
    rows = read_participants_file(participants_path)
    if not rows:
        error_msg = "No data found in participants.tsv"
        logger.log("fatal_error", error=error_msg)
        write_status(0, 0, error=error_msg)
        return EXIT_CODE_NO_ELIGIBLE
    
    # Filter
    eligible = filter_eligible_subjects(rows)
    excluded = [r for r in rows if r not in eligible]
    
    # Limit
    eligible = limit_subjects(eligible, MAX_SUBJECTS)
    
    # Write outputs
    write_eligible_csv(eligible, ELIGIBLE_CSV)
    write_excluded_log(excluded, EXCLUDED_LOG)
    write_status(len(eligible), len(excluded))
    
    if len(eligible) == 0:
        logger.log("no_eligible_subjects")
        return EXIT_CODE_NO_ELIGIBLE
    
    logger.log("success", eligible_count=len(eligible), excluded_count=len(excluded))
    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())