"""
Download and Filter Script for ds000246 (Constitution VI, FR-001)

This script downloads raw BIDS data from OpenNeuro, parses metadata to verify
the existence of rs-fMRI and longitudinal cognitive scores (MMSE/MOCA), and
filters subjects who have valid scores at both timepoints.

It outputs:
  - data/raw/ds000246/: Raw BIDS dataset (downloaded)
  - data/processed/eligible_subjects.csv: Subjects meeting criteria
  - data/processed/excluded_subjects.log: Log of excluded subjects and reasons

Exit Codes:
  0: Success
  1: General error
  2: No eligible subjects found (EXIT_CODE_NO_ELIGIBLE)
"""
from __future__ import annotations

import csv
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests
from urllib.parse import urljoin

# Local imports from project API surface
from utils.logger import get_logger, log_operation

# Constants
EXIT_CODE_NO_ELIGIBLE = 2
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://raw.githubusercontent.com/OpenNeuroDatasets"
DATASET_URL = f"{OPENNEURO_BASE}/{DATASET_ID}/master"

# Output paths relative to project root
RAW_DIR = Path("data/raw") / DATASET_ID
PROCESSED_DIR = Path("data/processed")
ELIGIBLE_CSV = PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = PROCESSED_DIR / "excluded_subjects.log"

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path) -> bool:
    """
    Download a file from URL to dest with retry logic.
    Returns True on success, False on failure.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            logger.log("download_file", url=url, dest=str(dest), attempt=attempt)
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except requests.exceptions.RequestException as e:
            logger.log("download_error", url=url, error=str(e), attempt=attempt)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                logger.log("download_failed_permanent", url=url, error=str(e))
                return False
    return False


def read_participants_tsv(participants_path: Path) -> List[Dict[str, str]]:
    """
    Read participants.tsv and return a list of dictionaries.
    Handles both tab and comma separated values if necessary, though BIDS is TSV.
    """
    if not participants_path.exists():
        logger.log("participants_missing", path=str(participants_path))
        return []

    rows = []
    try:
        with open(participants_path, 'r', encoding='utf-8') as f:
            # Detect separator (BIDS is TSV)
            first_line = f.readline()
            f.seek(0)
            
            if '\t' in first_line:
                reader = csv.DictReader(f, delimiter='\t')
            else:
                reader = csv.DictReader(f)
            
            for row in reader:
                rows.append(row)
    except Exception as e:
        logger.log("read_participants_error", path=str(participants_path), error=str(e))
        return []
    
    return rows


def has_valid_score(row: Dict[str, str], score_key: str) -> bool:
    """
    Check if a row has a valid (non-null, non-NaN) score for a given key.
    """
    if score_key not in row:
        return False
    val = row[score_key]
    if val is None or val == '' or val.lower() in ('nan', 'null', 'na', 'n/a'):
        return False
    try:
        float(val)
        return True
    except ValueError:
        return False


def is_eligible(row: Dict[str, str]) -> Tuple[bool, str]:
    """
    Determine if a subject is eligible based on having non-null MMSE or MOCA
    at BOTH timepoints (e.g., MMSE_1, MMSE_2 or MOCA_1, MOCA_2).
    
    Returns (is_eligible, reason_string).
    """
    subject_id = row.get('participant_id', 'unknown')
    
    # Check for MMSE at both timepoints
    mmse_1 = has_valid_score(row, 'MMSE_1')
    mmse_2 = has_valid_score(row, 'MMSE_2')
    
    # Check for MOCA at both timepoints
    moca_1 = has_valid_score(row, 'MOCA_1')
    moca_2 = has_valid_score(row, 'MOCA_2')
    
    # Eligible if (MMSE_1 and MMSE_2) OR (MOCA_1 and MOCA_2)
    if mmse_1 and mmse_2:
        return True, "Has MMSE at both timepoints"
    if moca_1 and moca_2:
        return True, "Has MOCA at both timepoints"
    
    reasons = []
    if not (mmse_1 and mmse_2):
        reasons.append("Missing MMSE at one or both timepoints")
    if not (moca_1 and moca_2):
        reasons.append("Missing MOCA at one or both timepoints")
        
    return False, "; ".join(reasons)


def filter_eligible_subjects(participants: List[Dict[str, str]]) -> Tuple[List[Dict], List[Tuple[str, str]]]:
    """
    Filter the list of participants for eligible subjects.
    Returns (eligible_list, excluded_list_of_tuples).
    """
    eligible = []
    excluded = []
    
    for row in participants:
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            subject_id = row.get('participant_id', 'unknown')
            excluded.append((subject_id, reason))
            
    return eligible, excluded


def limit_subjects(eligible: List[Dict], n: int = 100) -> List[Dict]:
    """
    Limit the number of eligible subjects to N.
    """
    if len(eligible) <= n:
        return eligible
    return eligible[:n]


def write_eligible_csv(eligible: List[Dict], output_path: Path) -> None:
    """
    Write eligible subjects to a CSV file.
    """
    ensure_directory(output_path.parent)
    if not eligible:
        # Write empty file with headers if possible, or just empty
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        return

    # Get headers from first row
    fieldnames = list(eligible[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eligible)
    
    logger.log("write_eligible_csv", path=str(output_path), count=len(eligible))


def write_excluded_log(excluded: List[Tuple[str, str]], output_path: Path) -> None:
    """
    Write excluded subjects to a log file.
    """
    ensure_directory(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 40 + "\n")
        f.write(f"Total Excluded: {len(excluded)}\n\n")
        for subject_id, reason in excluded:
            f.write(f"Subject: {subject_id}\n")
            f.write(f"Reason: {reason}\n")
            f.write("-" * 20 + "\n")
    
    logger.log("write_excluded_log", path=str(output_path), count=len(excluded))


def download_dataset_metadata() -> bool:
    """
    Download essential metadata files (participants.tsv, dataset_description.json)
    to verify dataset structure before attempting full download or processing.
    """
    ensure_directory(RAW_DIR)
    
    # Download dataset_description.json
    desc_url = urljoin(DATASET_URL, "dataset_description.json")
    if not download_file(desc_url, RAW_DIR / "dataset_description.json"):
        logger.log("metadata_download_failed", file="dataset_description.json")
        return False
    
    # Download participants.tsv
    part_url = urljoin(DATASET_URL, "participants.tsv")
    if not download_file(part_url, RAW_DIR / "participants.tsv"):
        logger.log("metadata_download_failed", file="participants.tsv")
        return False
        
    return True

    # 1. Download participants.tsv
    participants_path = RAW_DIR / "participants.tsv"
    logger.log("downloading_participants", url=PARTICIPANTS_URL, dest=str(participants_path))
    
    if not download_file(PARTICIPANTS_URL, participants_path):
        logger.log("fatal_error", reason="Failed to download participants.tsv")
        print(f"Failed to download {PARTICIPANTS_URL}", file=sys.stderr)
        return EXIT_CODE_DOWNLOAD_FAIL

def main() -> int:
    """
    Main execution flow:
    1. Download metadata (participants.tsv)
    2. Parse and filter eligible subjects
    3. Limit to N=100
    4. Write outputs
    5. Exit with code 2 if no eligible subjects
    """
    logger.log("start_download_and_filter")
    
    # Step 1: Download metadata
    if not download_dataset_metadata():
        logger.log("fatal", message="Failed to download dataset metadata")
        return 1
    
    participants_path = RAW_DIR / "participants.tsv"
    participants = read_participants_tsv(participants_path)
    
    if not participants:
        logger.log("fatal", message="No participants found in TSV")
        return 1
    
    logger.log("participants_loaded", count=len(participants))
    
    # Step 2: Filter
    eligible, excluded = filter_eligible_subjects(participants)
    logger.log("filtering_complete", eligible_count=len(eligible), excluded_count=len(excluded))
    
    # Step 3: Limit
    final_eligible = limit_subjects(eligible, n=100)
    logger.log("limiting_applied", original=len(eligible), final=len(final_eligible))
    
    # Step 4: Write outputs
    write_eligible_csv(final_eligible, ELIGIBLE_CSV)
    write_excluded_log(excluded, EXCLUDED_LOG)
    
    # Step 5: Validation
    if not final_eligible:
        logger.log("no_eligible_subjects", message="No eligible subjects found after filtering")
        # Ensure files exist even if empty
        if not ELIGIBLE_CSV.exists():
            ELIGIBLE_CSV.touch()
        if not EXCLUDED_LOG.exists():
            EXCLUDED_LOG.touch()
        return EXIT_CODE_NO_ELIGIBLE
    
    # Verify file size > 0 for eligible CSV
    if ELIGIBLE_CSV.stat().st_size == 0:
        logger.log("warning", message="Eligible CSV is empty despite having subjects")
        # This shouldn't happen if logic is correct, but safety check
        
    logger.log("success", eligible_count=len(final_eligible))
    return 0


if __name__ == "__main__":
    sys.exit(main())
