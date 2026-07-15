from __future__ import annotations

import csv
import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://api.openneuro.org"
MAX_SUBJECTS = 100
RANDOM_SEED = 42

# Output paths relative to project root
DATA_PROCESSED = Path("data/processed")
DATA_ARTIFACTS = Path("data/artifacts")
DATA_RAW = Path("data/raw")
ELIGIBLE_CSV = DATA_PROCESSED / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS / "data_gate_status.json"
PARTICIPANTS_TSV = DATA_RAW / DATASET_ID / "participants.tsv"

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)


def download_dataset_metadata() -> Dict[str, Any]:
    """Download dataset metadata from OpenNeuro."""
    url = f"{OPENNEURO_BASE}/datasets/{DATASET_ID}/versions/latest"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.log("download_metadata_error", error=str(e))
        raise RuntimeError(f"Failed to download dataset metadata: {e}") from e


def download_participants_file() -> Path:
    """Download participants.tsv from OpenNeuro."""
    ensure_directory(DATA_RAW / DATASET_ID)
    url = f"{OPENNEURO_BASE}/datasets/{DATASET_ID}/versions/latest/files/participants.tsv"
    output_path = PARTICIPANTS_TSV

    try:
        logger.log("start_download_participants", url=url, output=str(output_path))
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            f.write(response.content)
        logger.log("download_participants_success", size=len(response.content))
        return output_path
    except requests.exceptions.RequestException as e:
        logger.log("download_participants_error", error=str(e))
        raise RuntimeError(f"Failed to download participants.tsv: {e}") from e


def read_participants_file(path: Path) -> List[Dict[str, Any]]:
    """Read participants.tsv and return list of subject records."""
    if not path.exists():
        raise FileNotFoundError(f"Participants file not found: {path}")

    records = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            records.append(row)
    return records


def has_valid_score(record: Dict[str, Any]) -> bool:
    """Check if record has non-null MMSE or MOCA at both timepoints."""
    # Expected columns: participant_id, MMSE_T1, MMSE_T2, MOCA_T1, MOCA_T2, etc.
    # We need at least one score type available at both timepoints
    mmse_t1 = record.get("MMSE_T1")
    mmse_t2 = record.get("MMSE_T2")
    moca_t1 = record.get("MOCA_T1")
    moca_t2 = record.get("MOCA_T2")

    # Check for non-null values (string "null", empty string, or None)
    def is_valid(val):
        if val is None:
            return False
        val_str = str(val).strip().lower()
        if val_str in ("", "nan", "null", "none", "."):
            return False
        try:
            float(val_str)
            return True
        except ValueError:
            return False

    # Eligible if MMSE available at both times OR MOCA available at both times
    mmse_valid = is_valid(mmse_t1) and is_valid(mmse_t2)
    moca_valid = is_valid(moca_t1) and is_valid(moca_t2)

    return mmse_valid or moca_valid


def is_eligible(record: Dict[str, Any]) -> bool:
    """Determine if a subject is eligible for the study."""
    # Must have a participant_id
    if "participant_id" not in record or not record["participant_id"]:
        return False

    # Must have valid scores at both timepoints
    return has_valid_score(record)


def filter_eligible_subjects(records: List[Dict[str, Any]]) -> tuple[List[Dict], List[Dict]]:
    """Filter records into eligible and excluded lists."""
    eligible = []
    excluded = []

    for record in records:
        pid = record.get("participant_id", "unknown")
        if is_eligible(record):
            eligible.append(record)
        else:
            excluded.append(record)

    return eligible, excluded


def limit_subjects(eligible: List[Dict], max_n: int = MAX_SUBJECTS) -> List[Dict]:
    """Limit the number of subjects to max_n, using a deterministic seed."""
    if len(eligible) <= max_n:
        return eligible

    # Deterministic shuffle based on participant_id to ensure reproducibility
    # Sort by ID first to ensure consistent ordering before slicing
    sorted_eligible = sorted(eligible, key=lambda x: x.get("participant_id", ""))
    # Take first N after sorting (simple deterministic limit)
    return sorted_eligible[:max_n]


def write_eligible_csv(eligible: List[Dict], path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_directory(path.parent)
    if not eligible:
        # Write empty file with headers if possible
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=eligible[0].keys() if eligible else ["participant_id"])
            writer.writeheader()
        return

    fieldnames = list(eligible[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eligible)


def write_excluded_log(excluded: List[Dict], path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_directory(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        for record in excluded:
            pid = record.get("participant_id", "unknown")
            # Log reason: missing scores
            reason = "Missing valid MMSE/MOCA at one or both timepoints"
            f.write(f"{pid}: {reason}\n")


def write_status(status: str, eligible_count: int, excluded_count: int, error: Optional[str] = None) -> None:
    """Write status JSON file."""
    ensure_directory(STATUS_JSON.parent)
    data = {
        "status": status,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    if error:
        data["error"] = error

    with open(STATUS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


@log_operation("download_and_filter_main")
def main() -> int:
    """Main entry point for data download and filtering."""
    logger.log("start_operation", dataset=DATASET_ID, max_subjects=MAX_SUBJECTS)

    try:
        # 1. Download participants file
        participants_path = download_participants_file()

        # 2. Read records
        records = read_participants_file(participants_path)
        logger.log("read_participants", count=len(records))

        # 3. Filter eligible subjects
        eligible, excluded = filter_eligible_subjects(records)
        logger.log("filter_results", eligible=len(eligible), excluded=len(excluded))

        # 4. Limit subjects
        final_eligible = limit_subjects(eligible, MAX_SUBJECTS)
        logger.log("limit_results", final_count=len(final_eligible))

        # 5. Fail if zero eligible
        if len(final_eligible) == 0:
            write_status("error", 0, len(excluded), "No eligible subjects found")
            logger.log("no_eligible_subjects")
            return 2  # EXIT_CODE_NO_LABELS

        # 6. Write outputs
        write_eligible_csv(final_eligible, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)
        write_status("success", len(final_eligible), len(excluded))

        logger.log("operation_complete", eligible_file=str(ELIGIBLE_CSV), log_file=str(EXCLUDED_LOG))
        return 0

    except Exception as e:
        logger.log("operation_failed", error=str(e))
        write_status("error", 0, 0, str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())