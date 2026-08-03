"""
T017: Download ds000246, parse BIDS metadata, filter for subjects with
non-null MMSE/MOCA at both timepoints, limit to N=min(100, available_eligible).
Output: data/processed/eligible_subjects.csv, data/processed/excluded_subjects.log,
data/artifacts/data_gate_status.json.
Exit code: 3 if zero eligible subjects found.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
from tqdm import tqdm

# Import from existing API surface
from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
BASE_URL = "https://api.openneuro.org/datasets"
PARTICIPANTS_FILE = "participants.tsv"
MAX_ELIGIBLE = 100
EXIT_CODE_NO_ELIGIBLE = 3
EXIT_CODE_SUCCESS = 0

# Output paths
DATA_PROCESSED = Path("data/processed")
DATA_ARTIFACTS = Path("data/artifacts")
DATA_RAW = Path("data/raw")

ELIGIBLE_CSV = DATA_PROCESSED / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS / "data_gate_status.json"
RAW_DIR = DATA_RAW / DATASET_ID


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


@log_operation
def download_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """
    Download dataset metadata from OpenNeuro API.
    Returns metadata dict or raises on failure.
    """
    url = f"{BASE_URL}/{dataset_id}/versions/latest"
    logger = get_logger("download_dataset_metadata")
    logger.log("fetching_metadata", url=url)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.log("fetch_metadata_failed", error=str(e))
        raise RuntimeError(f"Failed to fetch dataset metadata: {e}") from e


@log_operation
def download_participants_file(dataset_id: str, output_path: Path) -> Path:
    """
    Download participants.tsv from OpenNeuro.
    OpenNeuro file API: https://openneuro.org/datasets/ds000246/versions/latest/file-download/participants.tsv
    We use the direct file download endpoint.
    """
    # OpenNeuro file download URL pattern
    file_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest/file-download/participants.tsv"
    logger = get_logger("download_participants_file")
    logger.log("downloading_participants", url=file_url)

    ensure_directory(output_path.parent)

    try:
        # Stream download to handle large files
        with requests.get(file_url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            with open(output_path, 'wb') as f, tqdm(
                desc=output_path.name,
                total=total_size,
                unit='B',
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        return output_path
    except requests.exceptions.RequestException as e:
        logger.log("download_participants_failed", error=str(e))
        raise RuntimeError(f"Failed to download participants.tsv: {e}") from e


@log_operation
def read_participants_file(file_path: Path) -> List[Dict[str, Any]]:
    """
    Read participants.tsv and return list of dicts.
    Handles TSV format with potential missing values.
    """
    logger = get_logger("read_participants_file")
    logger.log("reading_participants", path=str(file_path))

    if not file_path.exists():
        raise FileNotFoundError(f"Participants file not found: {file_path}")

    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)

    logger.log("read_participants_count", count=len(rows))
    return rows


@log_operation
def has_valid_score(row: Dict[str, Any], score_col: str) -> bool:
    """
    Check if a score column has a valid (non-null, numeric) value.
    Handles 'n/a', 'NA', empty strings, and non-numeric values.
    """
    val = row.get(score_col, "")
    if val is None or str(val).strip() == "" or str(val).lower() in ("n/a", "na", "nan", "null"):
        return False
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


@log_operation
def is_eligible(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if a subject is eligible:
    - Has non-null MMSE or MOCA at timepoint 1 (baseline)
    - Has non-null MMSE or MOCA at timepoint 2 (follow-up)
    - Timepoint columns are typically: mmse, mmse_2, moca, moca_2
    or similar naming conventions. We check for common patterns.
    """
    # Common column naming patterns for longitudinal scores
    # Pattern 1: mmse, mmse_followup or mmse_2
    # Pattern 2: moca, moca_followup or moca_2
    # We'll check for any combination that has both timepoints

    # Define possible column names for timepoint 1 and 2
    t1_cols = ["mmse", "moca", "mmse_baseline", "moca_baseline", "mmse_1", "moca_1"]
    t2_cols = ["mmse_2", "moca_2", "mmse_followup", "moca_followup", "mmse_2nd", "moca_2nd"]

    # Check for MMSE at both timepoints
    mmse_t1 = None
    mmse_t2 = None
    for col in t1_cols:
        if col in row and has_valid_score(row, col):
            mmse_t1 = col
            break
    for col in t2_cols:
        if col in row and has_valid_score(row, col):
            mmse_t2 = col
            break

    # Check for MOCA at both timepoints
    moca_t1 = None
    moca_t2 = None
    for col in t1_cols:
        if col in row and has_valid_score(row, col):
            moca_t1 = col
            break
    for col in t2_cols:
        if col in row and has_valid_score(row, col):
            moca_t2 = col
            break

    # Eligible if has either MMSE or MOCA at both timepoints
    if (mmse_t1 and mmse_t2) or (moca_t1 and moca_t2):
        return True, "has_longitudinal_scores"

    # Determine reason for exclusion
    if not mmse_t1 and not moca_t1:
        return False, "missing_baseline_scores"
    if not mmse_t2 and not moca_t2:
        return False, "missing_followup_scores"

    return False, "unknown_exclusion"


@log_operation
def filter_eligible_subjects(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Tuple[str, str]]]:
    """
    Filter rows for eligible subjects and return (eligible, excluded).
    Excluded is a list of (subject_id, reason) tuples.
    """
    logger = get_logger("filter_eligible_subjects")
    eligible = []
    excluded = []

    for row in rows:
        subject_id = row.get("participant_id", row.get("subject", "unknown"))
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            excluded.append((subject_id, reason))

    logger.log("filtering_complete", eligible_count=len(eligible), excluded_count=len(excluded))
    return eligible, excluded


@log_operation
def limit_subjects(eligible: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    """
    Limit the number of eligible subjects to the specified limit.
    Returns the first N subjects (deterministic order).
    """
    logger = get_logger("limit_subjects")
    if len(eligible) <= limit:
        logger.log("limit_not_reached", count=len(eligible))
        return eligible
    limited = eligible[:limit]
    logger.log("limit_applied", original=len(eligible), limited_to=limit)
    return limited


@log_operation
def write_eligible_csv(eligible: List[Dict[str, Any]], output_path: Path) -> None:
    """Write eligible subjects to CSV file."""
    ensure_directory(output_path.parent)
    logger = get_logger("write_eligible_csv")
    logger.log("writing_eligible_csv", path=str(output_path), count=len(eligible))

    if not eligible:
        logger.log("warning_no_eligible", message="No eligible subjects to write")
        # Still create an empty file with headers
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header from first row keys if available, otherwise default
            if eligible:
                writer.writerow(eligible[0].keys())
            else:
                writer.writerow(["participant_id", "status"])
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=eligible[0].keys())
        writer.writeheader()
        writer.writerows(eligible)


@log_operation
def write_excluded_log(excluded: List[Tuple[str, str]], output_path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_directory(output_path.parent)
    logger = get_logger("write_excluded_log")
    logger.log("writing_excluded_log", path=str(output_path), count=len(excluded))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Total excluded: {len(excluded)}\n\n")
        for subject_id, reason in excluded:
            f.write(f"{subject_id}: {reason}\n")


@log_operation
def write_status(status: str, error: Optional[str], eligible_count: int, excluded_count: int, output_path: Path) -> None:
    """Write status JSON file."""
    ensure_directory(output_path.parent)
    logger = get_logger("write_status")
    logger.log("writing_status", path=str(output_path), status=status)

    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)


@log_operation
def main() -> int:
    """
    Main entry point for T017.
    Returns EXIT_CODE_SUCCESS or EXIT_CODE_NO_ELIGIBLE.
    """
    logger = get_logger("download_and_filter_main")
    logger.log("starting_task", task_id="T017")

    try:
        # Step 1: Ensure directories exist
        ensure_directory(DATA_PROCESSED)
        ensure_directory(DATA_ARTIFACTS)
        ensure_directory(DATA_RAW)
        ensure_directory(RAW_DIR)

        # Step 2: Download dataset metadata (verify availability)
        logger.log("step_download_metadata", dataset_id=DATASET_ID)
        metadata = download_dataset_metadata(DATASET_ID)
        logger.log("metadata_fetched", version=metadata.get("latestVersion", "unknown"))

        # Step 3: Download participants.tsv
        participants_path = RAW_DIR / PARTICIPANTS_FILE
        logger.log("step_download_participants", path=str(participants_path))
        download_participants_file(DATASET_ID, participants_path)

        # Step 4: Read participants file
        logger.log("step_read_participants")
        rows = read_participants_file(participants_path)
        logger.log("participants_read", count=len(rows))

        # Step 5: Filter eligible subjects
        logger.log("step_filter_eligible")
        eligible, excluded = filter_eligible_subjects(rows)
        logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))

        # Step 6: Limit subjects
        limited_eligible = limit_subjects(eligible, MAX_ELIGIBLE)
        logger.log("limiting_complete", final_count=len(limited_eligible))

        # Step 7: Write outputs
        logger.log("step_write_outputs")
        write_eligible_csv(limited_eligible, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)

        # Step 8: Write status
        if len(limited_eligible) == 0:
            status_msg = "no_eligible_subjects"
            error_msg = "No subjects with longitudinal MMSE/MOCA scores found in ds000246"
            exit_code = EXIT_CODE_NO_ELIGIBLE
        else:
            status_msg = "success"
            error_msg = None
            exit_code = EXIT_CODE_SUCCESS

        write_status(status_msg, error_msg, len(limited_eligible), len(excluded), STATUS_JSON)

        logger.log("task_complete", status=status_msg, eligible_count=len(limited_eligible))
        return exit_code

    except Exception as e:
        logger.log("task_failed", error=str(e))
        # Write error status
        write_status("error", str(e), 0, 0, STATUS_JSON)
        return 1


if __name__ == "__main__":
    sys.exit(main())
