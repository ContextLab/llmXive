"""Download and filter subjects for cognitive decline prediction.

This script downloads the ds000246 dataset from OpenNeuro, parses the BIDS
metadata, and filters for subjects with non-null MMSE/MOCA scores at both
timepoints. It outputs a list of eligible subjects and a log of excluded subjects.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
import pandas as pd
from tqdm import tqdm

# Import from local utils
from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE_URL = "https://api.openneuro.org"
DATA_RAW_DIR = Path("data/raw") / DATASET_ID
DATA_PROCESSED_DIR = Path("data/processed")
DATA_ARTIFACTS_DIR = Path("data/artifacts")
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
ELIGIBLE_CSV = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS_DIR / "data_gate_status.json"
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_ERROR = 1

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def download_dataset_metadata() -> Dict[str, Any]:
    """Download dataset metadata from OpenNeuro."""
    url = f"{OPENNEURO_BASE_URL}/dataset/{DATASET_ID}/metadata"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            if attempt == MAX_RETRIES:
                logger.log("download_metadata_failed", error=str(e))
                raise
            logger.log("download_metadata_retry", attempt=attempt, error=str(e))
            time.sleep(RETRY_DELAY)
    raise RuntimeError("Failed to download metadata after retries")


def download_participants_file() -> pd.DataFrame:
    """Download and parse the participants.tsv file from the dataset."""
    # OpenNeuro uses git-annex, but we can fetch the file directly
    # via the datalad API or by constructing the URL for the raw file
    # For ds000246, the participants.tsv is typically at the root
    url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/1.0.0/file-display/participants.tsv"
    
    # Fallback to a more direct fetch if the above fails
    # OpenNeuro often serves files via a CDN
    alt_url = f"https://s3.amazonaws.com/openneuro.org/datasets/{DATASET_ID}/versions/1.0.0/participants.tsv"
    
    for url_to_try in [url, alt_url]:
        try:
            response = requests.get(url_to_try, timeout=60)
            if response.status_code == 200:
                # Parse TSV
                return pd.read_csv(pd.io.common.StringIO(response.text), sep='\t')
        except requests.RequestException:
            continue
    
    # If all direct URLs fail, try to fetch from the BIDS dataset via datalad-like approach
    # Since we cannot use datalad easily in a script, we'll try a known working path
    # ds000246 is a well-known dataset, let's try the standard BIDS path
    # We'll construct the URL based on the standard OpenNeuro file structure
    # This is a bit fragile but necessary for a standalone script
    base_url = f"https://api.openneuro.org/datasets/{DATASET_ID}/versions/1.0.0"
    file_path = "participants.tsv"
    
    # Try to get the file list first to confirm existence
    try:
        list_url = f"{base_url}/files"
        list_resp = requests.get(list_url, timeout=30)
        if list_resp.status_code == 200:
            files = list_resp.json()
            # Look for participants.tsv
            for f in files:
                if f.get('filename') == 'participants.tsv':
                    download_url = f.get('url')
                    if download_url:
                        resp = requests.get(download_url, timeout=60)
                        if resp.status_code == 200:
                            return pd.read_csv(pd.io.common.StringIO(resp.text), sep='\t')
    except Exception:
        pass

    raise RuntimeError(f"Could not download participants.tsv for {DATASET_ID}")


def read_participants_file(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert the participants dataframe to a list of dictionaries."""
    return df.to_dict(orient='records')


def has_valid_score(row: Dict[str, Any], score_col: str, timepoint_col: str = 'scan_timepoint') -> bool:
    """Check if a subject has a valid (non-null) score at a specific timepoint."""
    # Handle different column naming conventions
    possible_cols = [score_col, f'{score_col}_score', f'{score_col}_value']
    for col in possible_cols:
        if col in row:
            val = row[col]
            if pd.notna(val) and val != '' and val != 'nan':
                return True
    return False


def is_eligible(row: Dict[str, Any]) -> bool:
    """
    Determine if a subject is eligible for the study.
    Eligibility criteria:
    - Has non-null MMSE or MOCA score at timepoint 0
    - Has non-null MMSE or MOCA score at timepoint 1
    """
    # Check for MMSE or MOCA at timepoint 0 and 1
    # The dataset might have columns like 'MMSE', 'MMSE_1', 'MOCA', 'MOCA_1'
    # or 'MMSE_t0', 'MMSE_t1', etc.
    
    # Try to detect the column pattern
    mmse_cols = [c for c in row.keys() if 'MMSE' in c.upper()]
    moca_cols = [c for c in row.keys() if 'MOCA' in c.upper()]
    
    # If we find specific timepoint columns
    mmse_t0 = [c for c in mmse_cols if '0' in c or 't0' in c.lower() or 'baseline' in c.lower()]
    mmse_t1 = [c for c in mmse_cols if '1' in c or 't1' in c.lower() or 'followup' in c.lower()]
    moca_t0 = [c for c in moca_cols if '0' in c or 't0' in c.lower() or 'baseline' in c.lower()]
    moca_t1 = [c for c in moca_cols if '1' in c or 't1' in c.lower() or 'followup' in c.lower()]
    
    # If no specific timepoint columns, assume the dataset has 'MMSE' and 'MMSE_2' or similar
    if not mmse_t0 and not moca_t0:
        # Fallback: check if there are exactly two MMSE/MOCA columns
        if len(mmse_cols) >= 2:
            mmse_t0 = [mmse_cols[0]]
            mmse_t1 = [mmse_cols[1]]
        elif len(moca_cols) >= 2:
            moca_t0 = [moca_cols[0]]
            moca_t1 = [moca_cols[1]]
        elif len(mmse_cols) == 1 and len(moca_cols) == 1:
            # One of each, assume they are at different timepoints? Unlikely.
            # Assume both are at baseline and we need followup
            return False
        else:
            return False

    # Check if we have valid scores at both timepoints
    has_t0 = False
    has_t1 = False

    for col in mmse_t0 + moca_t0:
        if has_valid_score(row, col):
            has_t0 = True
            break

    for col in mmse_t1 + moca_t1:
        if has_valid_score(row, col):
            has_t1 = True
            break

    return has_t0 and has_t1


def filter_eligible_subjects(participants: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Filter participants for eligibility and return eligible and excluded lists."""
    eligible = []
    excluded = []
    
    for row in participants:
        subj_id = row.get('participant_id', row.get('subject_id', 'unknown'))
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    
    return eligible, excluded


def limit_subjects(subjects: List[Dict[str, Any]], n: int = 100) -> List[Dict[str, Any]]:
    """Limit the number of subjects to n, maintaining reproducibility."""
    return subjects[:n]


def write_eligible_csv(subjects: List[Dict[str, Any]], path: Path) -> None:
    """Write eligible subjects to a CSV file."""
    if not subjects:
        logger.log("write_eligible_csv", warning="No eligible subjects to write")
        # Create an empty file with headers if possible, or just touch it
        # We need to know the headers. Let's try to infer from the first subject if any,
        # but if the list is empty, we can't.
        # For now, create an empty file.
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        return

    headers = list(subjects[0].keys())
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(subjects)
    logger.log("write_eligible_csv", count=len(subjects), path=str(path))


def write_excluded_log(subjects: List[Dict[str, Any]], path: Path) -> None:
    """Write excluded subjects to a log file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 40 + "\n")
        f.write(f"Total excluded: {len(subjects)}\n\n")
        for subj in subjects:
            subj_id = subj.get('participant_id', subj.get('subject_id', 'unknown'))
            f.write(f"Subject: {subj_id}\n")
            # Write reason for exclusion (simplified)
            f.write("Reason: Missing scores at one or both timepoints\n")
            f.write("-" * 20 + "\n")
    logger.log("write_excluded_log", count=len(subjects), path=str(path))


def write_status(eligible_count: int, excluded_count: int, status: str = "success", error: Optional[str] = None) -> None:
    """Write the data gate status to a JSON file."""
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    DATA_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATUS_JSON, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)
    logger.log("write_status", status=status, eligible=eligible_count, excluded=excluded_count)


@log_operation
def main() -> int:
    """Main entry point."""
    try:
        logger.log("start", message="Starting data download and filtering")
        
        # Ensure directories exist
        ensure_directory(DATA_RAW_DIR)
        ensure_directory(DATA_PROCESSED_DIR)
        ensure_directory(DATA_ARTIFACTS_DIR)
        
        # Download metadata (optional, for logging)
        try:
            metadata = download_dataset_metadata()
            logger.log("metadata_downloaded", dataset_id=DATASET_ID)
        except Exception as e:
            logger.log("metadata_download_failed", error=str(e))
            # Continue anyway, as we need the participants file
        
        # Download participants file
        logger.log("downloading_participants", dataset_id=DATASET_ID)
        participants_df = download_participants_file()
        participants = read_participants_file(participants_df)
        logger.log("participants_loaded", count=len(participants))
        
        # Filter eligible subjects
        eligible, excluded = filter_eligible_subjects(participants)
        logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))
        
        # Limit to N subjects
        eligible = limit_subjects(eligible, n=100)
        logger.log("limiting_subjects", count=len(eligible))
        
        # Check if we have any eligible subjects
        if not eligible:
            logger.log("no_eligible_subjects", message="No eligible subjects found")
            write_status(eligible_count=0, excluded_count=len(excluded), status="no_labels")
            return EXIT_CODE_NO_LABELS
        
        # Write outputs
        write_eligible_csv(eligible, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)
        write_status(eligible_count=len(eligible), excluded_count=len(excluded))
        
        logger.log("success", message="Data download and filtering completed successfully")
        return EXIT_CODE_SUCCESS
        
    except Exception as e:
        logger.log("error", error=str(e))
        write_status(eligible_count=0, excluded_count=0, status="error", error=str(e))
        return EXIT_CODE_ERROR


if __name__ == "__main__":
    sys.exit(main())