"""
T017b: Filter subjects with non-null MMSE/MOCA at both timepoints.
Output: data/processed/eligible_subjects.csv, data/processed/excluded_subjects.log, data/artifacts/data_gate_status.json
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import from existing API surface
from utils.logger import get_logger, log_operation

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"
DATASET_ID = "ds000246"
PARTICIPANTS_FILE = DATA_RAW_DIR / DATASET_ID / "participants.tsv"
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_SUBJECTS_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_FILE = DATA_ARTIFACTS_DIR / "data_gate_status.json"

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def download_dataset_metadata() -> bool:
    """
    Download dataset metadata (participants.tsv) from OpenNeuro.
    This function is a placeholder for T017a logic which should have already run.
    For T017b, we assume the file exists or try to fetch it if missing.
    """
    if PARTICIPANTS_FILE.exists():
        logger.log("download_dataset_metadata", status="found", path=str(PARTICIPANTS_FILE))
        return True

    # Attempt to download if missing (fallback for T017a failure)
    # In a real scenario, this would use requests or the OpenNeuro API
    # Since we cannot guarantee network access in all environments, we check existence first.
    # If it doesn't exist, we fail loudly as per requirements.
    logger.log("download_dataset_metadata", status="missing", path=str(PARTICIPANTS_FILE))
    return False


def download_participants_file() -> bool:
    """Wrapper for downloading participants file."""
    return download_dataset_metadata()


def read_participants_file() -> Optional[Dict[str, Any]]:
    """Read the participants.tsv file and return as a dictionary."""
    if not PARTICIPANTS_FILE.exists():
        return None

    data = {}
    try:
        with open(PARTICIPANTS_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                subject_id = row.get("participant_id", "").strip()
                if subject_id:
                    data[subject_id] = row
    except Exception as e:
        logger.log("read_participants_file", error=str(e))
        return None
    return data


def has_valid_score(row: Dict[str, Any], score_col: str, timepoint_col: str) -> bool:
    """Check if a specific score column and timepoint exist and are non-null."""
    val = row.get(score_col, "")
    if not val or val.lower() in ["", "nan", "null", "none", "n/a"]:
        return False
    try:
        float(val)
        return True
    except ValueError:
        return False


def is_eligible(row: Dict[str, Any]) -> bool:
    """
    Check if a subject is eligible:
    - Has non-null MMSE or MOCA at BOTH timepoints (t1, t2).
    """
    # Define expected columns based on typical BIDS longitudinal structure
    # The spec mentions "longitudinal MMSE/MOCA scores".
    # We assume columns like 'MMSE_t1', 'MMSE_t2' or 'MOCA_t1', 'MOCA_t2' exist.
    # If the dataset uses different naming, this logic might need adjustment,
    # but we stick to the spec's requirement for longitudinal scores.

    mmse_cols = ["MMSE_t1", "MMSE_t2", "mmse_t1", "mmse_t2"]
    moca_cols = ["MOCA_t1", "MOCA_t2", "moca_t1", "moca_t2"]

    # Check for MMSE availability at both timepoints
    mmse_valid = False
    for t1_col in mmse_cols:
        for t2_col in mmse_cols:
            if t1_col != t2_col and t1_col.endswith("t1") and t2_col.endswith("t2"):
                if has_valid_score(row, t1_col, "t1") and has_valid_score(row, t2_col, "t2"):
                    mmse_valid = True
                    break
        if mmse_valid: break

    # Check for MOCA availability at both timepoints
    moca_valid = False
    for t1_col in moca_cols:
        for t2_col in moca_cols:
            if t1_col != t2_col and t1_col.endswith("t1") and t2_col.endswith("t2"):
                if has_valid_score(row, t1_col, "t1") and has_valid_score(row, t2_col, "t2"):
                    moca_valid = True
                    break
        if moca_valid: break

    return mmse_valid or moca_valid


def filter_eligible_subjects(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Filter subjects based on eligibility criteria."""
    eligible = []
    excluded = []

    for subject_id, row in data.items():
        if is_eligible(row):
            eligible.append({"subject_id": subject_id, **row})
        else:
            excluded.append({"subject_id": subject_id, **row})

    return eligible, excluded


def limit_subjects(eligible: List[Dict[str, Any]], max_subjects: Optional[int] = None) -> List[Dict[str, Any]]:
    """Limit the number of subjects if specified."""
    if max_subjects and len(eligible) > max_subjects:
        return eligible[:max_subjects]
    return eligible


def write_eligible_csv(eligible: List[Dict[str, Any]], filepath: Path) -> None:
    """Write eligible subjects to CSV."""
    if not eligible:
        # Create empty file with headers if needed, or just an empty file
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            f.write("")
        return

    # Determine headers from the first row
    headers = list(eligible[0].keys())
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(eligible)


def write_excluded_log(excluded: List[Dict[str, Any]], filepath: Path) -> None:
    """Write excluded subjects to log."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 40 + "\n")
        for sub in excluded:
            f.write(f"Subject: {sub.get('subject_id', 'N/A')}\n")
            f.write(f"Reason: Missing longitudinal scores (MMSE/MOCA)\n")
            f.write("-" * 20 + "\n")


def write_status(eligible_count: int, excluded_count: int, status: str = "success", error: Optional[str] = None) -> None:
    """Write status JSON."""
    ensure_directory(DATA_ARTIFACTS_DIR)
    status_data = {
        "status": status,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "dataset": DATASET_ID
    }
    if error:
        status_data["error"] = error

    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, indent=2)


@log_operation
def main() -> int:
    """Main execution flow for T017b."""
    logger.log("main_start", message="Starting T017b: Filter eligible subjects")

    # 1. Ensure participants file exists (dependency on T017a)
    if not download_participants_file():
        logger.log("error", message="Participants file not found. T017a may have failed.")
        write_status(0, 0, "error", "Participants file missing")
        print("Error: Participants file not found. Ensure T017a has run successfully.")
        return 1

    # 2. Read participants
    data = read_participants_file()
    if not data:
        logger.log("error", message="Failed to read participants file.")
        write_status(0, 0, "error", "Failed to read participants file")
        print("Error: Failed to read participants file.")
        return 1

    logger.log("read_participants", count=len(data))

    # 3. Filter eligible subjects
    eligible, excluded = filter_eligible_subjects(data)
    logger.log("filter_eligible", eligible_count=len(eligible), excluded_count=len(excluded))

    # 4. Limit subjects (optional, for runtime constraints if needed)
    # For now, we take all eligible subjects.
    eligible = limit_subjects(eligible)

    # 5. Write outputs
    ensure_directory(DATA_PROCESSED_DIR)
    write_eligible_csv(eligible, ELIGIBLE_SUBJECTS_FILE)
    write_excluded_log(excluded, EXCLUDED_SUBJECTS_LOG)

    # 6. Check exit condition
    if not eligible:
        logger.log("no_eligible_subjects", message="No eligible subjects found.")
        write_status(0, len(excluded), "no_eligible", "No eligible subjects found")
        print("No eligible subjects found. Exiting with code 2.")
        return 2

    # 7. Write success status
    write_status(len(eligible), len(excluded), "success")
    logger.log("main_end", message="T017b completed successfully.", eligible_count=len(eligible))
    print(f"Successfully filtered {len(eligible)} eligible subjects.")
    return 0


if __name__ == "__main__":
    sys.exit(main())