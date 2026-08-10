"""
T017: Download ds000246, parse BIDS metadata, filter for longitudinal scores.
Outputs: data/processed/eligible_subjects.csv, data/processed/excluded_subjects.log,
         data/artifacts/data_gate_status.json
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# Local imports
from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
BASE_URL = "https://api.openneuro.org/datasets"
EXIT_CODE_NO_ELIGIBLE = 3
MAX_SUBJECTS = 100

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)


@log_operation
def download_dataset_metadata(dataset_id: str) -> Optional[Dict[str, Any]]:
    """
    Download dataset metadata from OpenNeuro.
    Returns dict if successful, None otherwise.
    """
    url = f"{BASE_URL}/{dataset_id}/versions/latest"
    logger.log("fetching_metadata", url=url)
    try:
        import requests
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.log("fetch_metadata_failed", error=str(e))
        return None


@log_operation
def download_participants_file(dataset_id: str, output_path: Path) -> bool:
    """
    Download participants.tsv from OpenNeuro.
    Returns True if successful, False otherwise.
    """
    url = f"{BASE_URL}/{dataset_id}/versions/latest/files/participants.tsv"
    logger.log("fetching_participants", url=url)
    try:
        import requests
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        logger.log("participants_downloaded", path=str(output_path))
        return True
    except Exception as e:
        logger.log("fetch_participants_failed", error=str(e))
        return False


@log_operation
def read_participants_file(path: Path) -> List[Dict[str, Any]]:
    """
    Read participants.tsv and return list of dicts.
    """
    if not path.exists():
        logger.log("file_missing", path=str(path))
        return []
    
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
    logger.log("participants_read", count=len(rows))
    return rows


@log_operation
def has_valid_score(row: Dict[str, Any]) -> bool:
    """
    Check if row has non-null MMSE or MOCA at both timepoints.
    Expected columns: participant_id, MMSE_T1, MMSE_T2, MOCA_T1, MOCA_T2 (or similar)
    We check for any column containing 'MMSE' or 'MOCA' with valid numeric values.
    """
    # Look for timepoint columns
    mmse_t1 = row.get('MMSE_T1') or row.get('MMSE_t1') or row.get('mmse_t1')
    mmse_t2 = row.get('MMSE_T2') or row.get('MMSE_t2') or row.get('mmse_t2')
    moca_t1 = row.get('MOCA_T1') or row.get('MOCA_t1') or row.get('moca_t1')
    moca_t2 = row.get('MOCA_T2') or row.get('MOCA_t2') or row.get('moca_t2')

    # Check if we have at least one valid score at both timepoints
    # We require either MMSE or MOCA at T1, and either MMSE or MOCA at T2
    t1_valid = False
    t2_valid = False

    if mmse_t1 and mmse_t1.strip() != '':
        try:
            float(mmse_t1)
            t1_valid = True
        except ValueError:
            pass
    
    if mmse_t2 and mmse_t2.strip() != '':
        try:
            float(mmse_t2)
            t2_valid = True
        except ValueError:
            pass

    if moca_t1 and moca_t1.strip() != '':
        try:
            float(moca_t1)
            t1_valid = True
        except ValueError:
            pass

    if moca_t2 and moca_t2.strip() != '':
        try:
            float(moca_t2)
            t2_valid = True
        except ValueError:
            pass

    return t1_valid and t2_valid


@log_operation
def is_eligible(row: Dict[str, Any]) -> bool:
    """
    Determine if a subject is eligible (has longitudinal scores).
    """
    return has_valid_score(row)


@log_operation
def filter_eligible_subjects(participants: List[Dict[str, Any]]) -> tuple[List[Dict], List[Dict]]:
    """
    Filter participants for those with valid longitudinal scores.
    Returns (eligible, excluded) lists.
    """
    eligible = []
    excluded = []
    for row in participants:
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))
    return eligible, excluded


@log_operation
def limit_subjects(subjects: List[Dict], limit: int) -> List[Dict]:
    """
    Limit the number of subjects to the specified maximum.
    """
    if len(subjects) <= limit:
        return subjects
    result = subjects[:limit]
    logger.log("subjects_limited", count=len(result), original=len(subjects))
    return result


@log_operation
def write_eligible_csv(subjects: List[Dict], output_path: Path) -> None:
    """
    Write eligible subjects to CSV.
    """
    ensure_directory(output_path.parent)
    if not subjects:
        # Write empty file with headers if no subjects
        headers = list(subjects[0].keys()) if subjects else ['participant_id']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    headers = list(subjects[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(subjects)
    logger.log("eligible_csv_written", path=str(output_path), count=len(subjects))


@log_operation
def write_excluded_log(subjects: List[Dict], output_path: Path) -> None:
    """
    Write excluded subjects to log file.
    """
    ensure_directory(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 50 + "\n\n")
        for subject in subjects:
            f.write(f"Subject: {subject.get('participant_id', 'N/A')}\n")
            f.write(f"Reason: Missing longitudinal scores\n")
            f.write("-" * 30 + "\n")
    logger.log("excluded_log_written", path=str(output_path), count=len(subjects))


@log_operation
def write_status(eligible_count: int, excluded_count: int, error: Optional[str] = None, output_path: Path = Path("data/artifacts/data_gate_status.json")) -> None:
    """
    Write status JSON file.
    """
    ensure_directory(output_path.parent)
    status = {
        "status": "error" if error else "success",
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)
    logger.log("status_written", path=str(output_path))


def main():
    """
    Main entry point for T017.
    """
    from datetime import datetime  # Local import to avoid circular if needed

    logger.log("main_start", dataset=DATASET_ID)

    # Paths
    raw_dir = Path("data/raw") / DATASET_ID
    processed_dir = Path("data/processed")
    artifacts_dir = Path("data/artifacts")

    participants_path = raw_dir / "participants.tsv"
    eligible_csv_path = processed_dir / "eligible_subjects.csv"
    excluded_log_path = processed_dir / "excluded_subjects.log"
    status_path = artifacts_dir / "data_gate_status.json"

    # Step 1: Check dataset availability (metadata)
    metadata = download_dataset_metadata(DATASET_ID)
    if not metadata:
        logger.log("dataset_unavailable", dataset=DATASET_ID)
        write_status(0, 0, error=f"Dataset {DATASET_ID} not available", output_path=status_path)
        sys.exit(1)

    # Step 2: Download participants file
    if not download_participants_file(DATASET_ID, participants_path):
        logger.log("participants_download_failed", dataset=DATASET_ID)
        write_status(0, 0, error=f"Failed to download participants for {DATASET_ID}", output_path=status_path)
        sys.exit(1)

    # Step 3: Read participants
    participants = read_participants_file(participants_path)
    if not participants:
        logger.log("no_participants_found")
        write_status(0, 0, error="No participants found in dataset", output_path=status_path)
        sys.exit(1)

    # Step 4: Filter eligible subjects
    eligible, excluded = filter_eligible_subjects(participants)

    # Step 5: Limit subjects
    eligible = limit_subjects(eligible, MAX_SUBJECTS)

    # Step 6: Write outputs
    write_eligible_csv(eligible, eligible_csv_path)
    write_excluded_log(excluded, excluded_log_path)
    
    if len(eligible) == 0:
        error_msg = "No eligible subjects found after filtering"
        logger.log("no_eligible_subjects")
        write_status(0, len(excluded), error=error_msg, output_path=status_path)
        sys.exit(EXIT_CODE_NO_ELIGIBLE)

    write_status(len(eligible), len(excluded), output_path=status_path)
    logger.log("main_success", eligible=len(eligible), excluded=len(excluded))
    return 0


if __name__ == "__main__":
    sys.exit(main())