"""
T017: Download ds000246, parse BIDS metadata, filter for subjects with
non-null MMSE/MOCA at both timepoints, limit to N=100, and output artifacts.

This script implements the data ingestion and filtering logic for User Story 1.
It downloads the participants.tsv from OpenNeuro, filters subjects based on
cognitive scores at two timepoints, and generates the required CSV, log, and
JSON status files.
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
from urllib.parse import urljoin

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, log_operation

# Constants
EXIT_CODE_NO_ELIGIBLE = 2
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://datasets.openneuro.org/datasets"
DATA_RAW_DIR = Path("data/raw") / DATASET_ID
DATA_PROCESSED_DIR = Path("data/processed")
DATA_ARTIFACTS_DIR = Path("data/artifacts")

PARTICIPANTS_URL = f"{OPENNEURO_BASE}/{DATASET_ID}/participants.tsv"

# Configuration
MAX_ELIGIBLE_SUBJECTS = 100
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_DOWNLOAD_ERROR = 3

# Ensure directories exist
ensure_directory(DATA_RAW_DIR)
ensure_directory(DATA_PROCESSED_DIR)
ensure_directory(DATA_ARTIFACTS_DIR)

logger = get_logger("download_and_filter")

def ensure_directory(path: Path) -> None:
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest_path: Path) -> bool:
    """
    Download a file from URL with progress bar and retry logic.
    Returns True if successful, False otherwise.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            logger.log("download_start", url=url, attempt=attempt + 1)
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024
            
            with open(dest_path, 'wb') as f, tqdm(
                total=total_size,
                unit='B',
                unit_scale=True,
                desc=dest_path.name
            ) as pbar:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
            
            logger.log("download_success", path=str(dest_path), size=dest_path.stat().st_size)
            return True
        except requests.RequestException as e:
            logger.log("download_error", url=url, error=str(e), attempt=attempt + 1)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                logger.log("download_failed_permanent", url=url, error=str(e))
                return False
    return False

def read_participants_tsv(path: Path) -> List[Dict[str, Any]]:
    """
    Read the participants.tsv file and return a list of dictionaries.
    Handles TSV format with headers.
    """
    if not path.exists():
        logger.log("file_not_found", path=str(path))
        return []
    
    data = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                data.append(row)
        logger.log("participants_read", count=len(data), path=str(path))
    except Exception as e:
        logger.log("read_error", path=str(path), error=str(e))
        return []
    
    return data

def has_valid_score(row: Dict[str, Any], score_col: str) -> bool:
    """
    Check if a specific score column has a valid non-null numeric value.
    Handles 'n/a', 'NA', empty strings, and None.
    """
    val = row.get(score_col, "")
    if val is None or val == "" or val.lower() in ["n/a", "na", "nan", "null"]:
        return False
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False

def is_eligible(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if a subject is eligible based on longitudinal cognitive scores.
    
    Eligibility criteria:
    - Must have non-null MMSE or MOCA score at timepoint 1 (e.g., 'MMSE_bl', 'MOCA_bl')
    - Must have non-null MMSE or MOCA score at timepoint 2 (e.g., 'MMSE_fu', 'MOCA_fu')
    
    Returns (is_eligible, reason)
    """
    # Define possible column names for baseline and follow-up
    # The dataset ds000246 (Constitution VI) typically uses specific naming
    # We check for common patterns: _bl (baseline) and _fu (follow-up) or _2
    score_cols_bl = [c for c in row.keys() if 'MMSE' in c.upper() or 'MOCA' in c.upper()]
    
    # Heuristic: identify baseline vs follow-up based on suffix
    bl_cols = [c for c in score_cols_bl if 'bl' in c.lower() or c.lower().endswith('_1') or c.lower().endswith('_base')]
    fu_cols = [c for c in score_cols_bl if 'fu' in c.lower() or c.lower().endswith('_2') or 'follow' in c.lower()]
    
    # If specific suffixes aren't found, try to infer from count (first two occurrences)
    if not bl_cols and not fu_cols:
        # Sort columns to find first two score columns as baseline and follow-up
        score_cols_sorted = sorted(score_cols_bl)
        if len(score_cols_sorted) >= 2:
            bl_cols = [score_cols_sorted[0]]
            fu_cols = [score_cols_sorted[1]]
        elif len(score_cols_sorted) == 1:
            # Only one timepoint available, not eligible for longitudinal
            return False, "Only one timepoint found"
        else:
            return False, "No cognitive scores found"
    
    # Check if at least one valid score exists at baseline
    has_bl = any(has_valid_score(row, c) for c in bl_cols)
    has_fu = any(has_valid_score(row, c) for c in fu_cols)
    
    if not has_bl:
        return False, f"No valid baseline score in {bl_cols}"
    if not has_fu:
        return False, f"No valid follow-up score in {fu_cols}"
        
    return True, "Has valid scores at both timepoints"

def filter_eligible_subjects(participants: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter subjects who have valid cognitive scores at both timepoints.
    Returns (eligible_list, excluded_list).
    """
    eligible = []
    excluded = []
    
    for row in participants:
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            excluded.append({"row": row, "reason": reason})
    
    logger.log("filtering_complete", eligible_count=len(eligible), excluded_count=len(excluded))
    return eligible, excluded

def limit_subjects(eligible: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    """
    Limit the number of eligible subjects to n.
    Returns the first n subjects.
    """
    if len(eligible) <= n:
        return eligible
    limited = eligible[:n]
    logger.log("limiting_subjects", original=len(eligible), limit=n, final=len(limited))
    return limited

def write_eligible_csv(eligible: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write eligible subjects to a CSV file.
    """
    if not eligible:
        logger.log("no_eligible_to_write", path=str(output_path))
        # Write empty file with headers if possible, or just create it
        output_path.touch()
        return

    # Determine headers from the first row
    headers = list(eligible[0].keys())
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(eligible)
    
    logger.log("eligible_csv_written", path=str(output_path), count=len(eligible))

def write_excluded_log(excluded: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write excluded subjects and reasons to a log file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Total Excluded: {len(excluded)}\n\n")
        for item in excluded:
            row = item.get("row", {})
            reason = item.get("reason", "Unknown")
            subject_id = row.get("participant_id", "Unknown")
            f.write(f"Subject: {subject_id}\n")
            f.write(f"Reason: {reason}\n")
            f.write("-" * 40 + "\n")
    
    logger.log("excluded_log_written", path=str(output_path), count=len(excluded))

def write_status(status_data: Dict[str, Any], output_path: Path) -> None:
    """
    Write the data gate status to a JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(status_data, f, indent=2, default=str)
    logger.log("status_json_written", path=str(output_path))

def main() -> int:
    """
    Main entry point for the download and filter script.
    """
    logger.log("main_start", dataset=DATASET_ID)
    
    participants_path = DATA_RAW_DIR / "participants.tsv"
    eligible_csv_path = DATA_PROCESSED_DIR / "eligible_subjects.csv"
    excluded_log_path = DATA_PROCESSED_DIR / "excluded_subjects.log"
    status_json_path = DATA_ARTIFACTS_DIR / "data_gate_status.json"
    
    # Step 1: Download participants.tsv
    if not participants_path.exists():
        logger.log("downloading_participants", url=PARTICIPANTS_URL)
        success = download_file(PARTICIPANTS_URL, participants_path)
        if not success:
            logger.log("download_failed", url=PARTICIPANTS_URL)
            status = {
                "dataset": DATASET_ID,
                "total_subjects": 0,
                "eligible_subjects": 0,
                "excluded_subjects": 0,
                "status": "download_failed",
                "exit_code": EXIT_CODE_DOWNLOAD_ERROR
            }
            write_status(status, status_json_path)
            return EXIT_CODE_DOWNLOAD_ERROR
    else:
        logger.log("participants_already_exists", path=str(participants_path))

    # Step 2: Read participants
    participants = read_participants_tsv(participants_path)
    
    if not participants:
        logger.log("no_participants_found")
        status = {
            "dataset": DATASET_ID,
            "total_subjects": 0,
            "eligible_subjects": 0,
            "excluded_subjects": 0,
            "status": "no_participants",
            "exit_code": EXIT_CODE_NO_LABELS
        }
        write_status(status, status_json_path)
        return EXIT_CODE_NO_LABELS

    total_subjects = len(participants)
    logger.log("participants_loaded", count=total_subjects)

    # Step 3: Filter eligible subjects
    eligible, excluded = filter_eligible_subjects(participants)
    eligible_count = len(eligible)
    excluded_count = len(excluded)

    if eligible_count == 0:
        logger.log("no_eligible_subjects")
        status = {
            "dataset": DATASET_ID,
            "total_subjects": total_subjects,
            "eligible_subjects": 0,
            "excluded_subjects": excluded_count,
            "status": "no_eligible_subjects",
            "exit_code": EXIT_CODE_NO_LABELS
        }
        write_eligible_csv([], eligible_csv_path)
        write_excluded_log(excluded, excluded_log_path)
        write_status(status, status_json_path)
        return EXIT_CODE_NO_LABELS

    # Step 4: Limit subjects
    limited_eligible = limit_subjects(eligible, MAX_ELIGIBLE_SUBJECTS)
    final_count = len(limited_eligible)

    # Step 5: Write outputs
    write_eligible_csv(limited_eligible, eligible_csv_path)
    write_excluded_log(excluded, excluded_log_path)

    status = {
        "dataset": DATASET_ID,
        "total_subjects": total_subjects,
        "eligible_subjects": final_count,
        "excluded_subjects": excluded_count,
        "status": "success",
        "exit_code": EXIT_CODE_SUCCESS,
        "limit_applied": MAX_ELIGIBLE_SUBJECTS if final_count == MAX_ELIGIBLE_SUBJECTS else False
    }
    write_status(status, status_json_path)

    logger.log("main_success", eligible_count=final_count, status=status)
    return EXIT_CODE_SUCCESS

if __name__ == "__main__":
    sys.exit(main())
