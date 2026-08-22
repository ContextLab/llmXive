"""
code/01_download_and_filter.py (Part 2)
Implements mandatory logging of excluded subjects for T017b.
Extends T017a logic to ensure `data/processed/excluded_subjects.log` is generated.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Import shared utilities from the project
from utils.logger import get_logger, log_operation, LogEntry
from utils.io import ensure_dir, save_json, save_csv, load_json, load_csv

# Constants
EXIT_CODE_NO_ELIGIBLE = 3
EXIT_CODE_SUCCESS = 0
DATASET_ID = "ds000246"
RANDOM_SEED = 42

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw" / DATASET_ID
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS = PROJECT_ROOT / "data" / "artifacts"

# Output files
ELIGIBLE_SUBJECTS_CSV = DATA_PROCESSED / "eligible_subjects.csv"
EXCLUDED_SUBJECTS_LOG = DATA_PROCESSED / "excluded_subjects.log"
DATA_GATE_STATUS_JSON = DATA_ARTIFACTS / "data_gate_status.json"

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    path.mkdir(parents=True, exist_ok=True)


def download_dataset_metadata() -> Tuple[Path, bool]:
    """
    Download dataset metadata (participants.tsv) from OpenNeuro ds000246.
    Returns (path_to_participants_tsv, success_flag).
    """
    # In a real execution, this would fetch from OpenNeuro.
    # For this implementation, we assume the file is expected at DATA_RAW / "participants.tsv"
    # or we attempt a minimal fetch if the environment allows.
    # Given the constraints, we simulate the check on the expected file location.
    
    participants_path = DATA_RAW / "participants.tsv"
    
    if not participants_path.exists():
        # Attempt to download if not present (simplified logic for the runner)
        # In a real scenario, we would use requests or openneuro-cli here.
        # Since we cannot guarantee network access in this specific snippet context,
        # we check existence. If missing, we log and return False.
        logger.log("download_dataset_metadata", status="failed", reason="participants.tsv not found")
        return participants_path, False
    
    logger.log("download_dataset_metadata", status="success", path=str(participants_path))
    return participants_path, True


def read_participants_file(participants_path: Path) -> List[Dict[str, Any]]:
    """
    Read the participants.tsv file and return a list of dictionaries.
    """
    if not participants_path.exists():
        return []
    
    rows = []
    with open(participants_path, 'r', encoding='utf-8') as f:
        # Assuming TSV format as per BIDS
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
    return rows


def has_valid_score(row: Dict[str, Any], score_col: str) -> bool:
    """Check if a specific score column has a valid numeric value."""
    val = row.get(score_col, "")
    if val is None or val == "":
        return False
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def is_eligible(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Determine if a subject is eligible based on longitudinal scores.
    Returns (is_eligible, list_of_exclusion_reasons).
    """
    reasons = []
    subject_id = row.get("participant_id", "unknown")
    
    # Check for MMSE or MOCA at baseline and follow-up
    # Assuming column names like 'MMSE_baseline', 'MMSE_followup', etc.
    # We adapt to common BIDS naming if exact names vary, but strict spec implies specific columns.
    # Based on tasks.md: "non-null MMSE/MOCA at both timepoints"
    
    # Check Baseline
    mmse_base = has_valid_score(row, 'MMSE_baseline')
    moca_base = has_valid_score(row, 'MOCA_baseline')
    if not (mmse_base or moca_base):
        reasons.append("Missing MMSE/MOCA at baseline")
    
    # Check Follow-up
    mmse_follow = has_valid_score(row, 'MMSE_followup')
    moca_follow = has_valid_score(row, 'MOCA_followup')
    if not (mmse_follow or moca_follow):
        reasons.append("Missing MMSE/MOCA at follow-up")
    
    return len(reasons) == 0, reasons


def filter_eligible_subjects(rows: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Tuple[str, List[str]]]]:
    """
    Filter rows for eligible subjects.
    Returns (eligible_rows, excluded_list) where excluded_list is [(subject_id, reasons), ...]
    """
    eligible = []
    excluded = []
    
    for row in rows:
        is_elig, reasons = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            excluded.append((row.get("participant_id", "unknown"), reasons))
    
    return eligible, excluded


def limit_subjects(eligible: List[Dict[str, Any]], max_limit: int = 100) -> List[Dict[str, Any]]:
    """
    Limit the number of eligible subjects to a maximum threshold.
    """
    if len(eligible) <= max_limit:
        return eligible
    return eligible[:max_limit]


def write_eligible_csv(eligible: List[Dict[str, Any]], output_path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_dir(output_path.parent)
    if not eligible:
        # Write header only if empty
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["participant_id"])
            writer.writeheader()
        return

    # Determine fieldnames from the first row
    fieldnames = list(eligible[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(eligible)


def write_excluded_log(excluded: List[Tuple[str, List[str]]], output_path: Path) -> None:
    """
    Write the excluded subjects log.
    Format: subject_id, reason1, reason2, ...
    MUST be created even if empty (header only).
    """
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("subject_id,exclusion_reasons\n")
        for subject_id, reasons in excluded:
            # Join multiple reasons with a semicolon
            reason_str = "; ".join(reasons)
            f.write(f"{subject_id},{reason_str}\n")


def write_status(eligible_count: int, total_count: int, excluded_count: int, status: str, output_path: Path) -> None:
    """Write the data gate status JSON."""
    ensure_dir(output_path.parent)
    status_data = {
        "dataset": DATASET_ID,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_subjects_scanned": total_count,
        "eligible_subjects": eligible_count,
        "excluded_subjects": excluded_count,
        "status": status,
        "random_seed": RANDOM_SEED
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2)


def main() -> int:
    """Main entry point for data download and filtering."""
    logger.log("main", operation="start")
    
    # 1. Download/Verify Metadata
    participants_path, success = download_dataset_metadata()
    if not success:
        write_status(0, 0, 0, "download_failed", DATA_GATE_STATUS_JSON)
        logger.log("main", status="failed", reason="Metadata download failed")
        return EXIT_CODE_NO_ELIGIBLE
    
    # 2. Read Data
    rows = read_participants_file(participants_path)
    total_count = len(rows)
    
    if total_count == 0:
        write_status(0, 0, 0, "no_data", DATA_GATE_STATUS_JSON)
        logger.log("main", status="failed", reason="No participants found")
        return EXIT_CODE_NO_ELIGIBLE
    
    # 3. Filter Eligible
    eligible, excluded = filter_eligible_subjects(rows)
    eligible_count = len(eligible)
    excluded_count = len(excluded)
    
    # 4. Limit Sample (T017a requirement)
    eligible = limit_subjects(eligible, max_limit=100)
    final_eligible_count = len(eligible)
    
    # 5. Write Outputs
    # T017a: Write eligible subjects
    write_eligible_csv(eligible, ELIGIBLE_SUBJECTS_CSV)
    
    # T017b: Write excluded log (MANDATORY)
    write_excluded_log(excluded, EXCLUDED_SUBJECTS_LOG)
    
    # Write Status
    if final_eligible_count == 0:
        write_status(0, total_count, excluded_count, "no_eligible_subjects", DATA_GATE_STATUS_JSON)
        logger.log("main", status="failed", reason="No eligible subjects after filtering")
        return EXIT_CODE_NO_ELIGIBLE
    
    write_status(final_eligible_count, total_count, excluded_count, "success", DATA_GATE_STATUS_JSON)
    logger.log("main", status="success", eligible_count=final_eligible_count)
    
    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())