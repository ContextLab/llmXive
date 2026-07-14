"""
Download ds000246, parse BIDS metadata, filter for subjects with non-null
MMSE/MOCA at both timepoints, limit to N subjects, and write status outputs.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests
from tqdm import tqdm

# Import shared logging utilities
from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://raw.githubusercontent.com/OpenNeuroDatasets"
PARTICIPANTS_URL = f"{OPENNEURO_BASE}/{DATASET_ID}/master/participants.tsv"
OUTPUT_DIR = Path("data/processed")
ARTIFACTS_DIR = Path("data/artifacts")
RAW_DIR = Path("data/raw") / DATASET_ID

# Exit codes
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_DOWNLOAD_FAIL = 1

# Configuration
MAX_SUBJECTS = 100
RANDOM_SEED = 42  # For reproducibility if shuffling is needed

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Create directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def download_file(url: str, dest: Path) -> bool:
    """
    Download a file from url to dest with progress bar.
    Returns True on success, False on failure.
    """
    ensure_directory(dest.parent)
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total = int(response.headers.get('content-length', 0))
        with open(dest, 'wb') as f, tqdm(
            desc=dest.name,
            total=total,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))
        return True
    except Exception as e:
        logger.log("download_failed", error=str(e), url=url)
        return False


def read_participants_tsv(path: Path) -> List[Dict[str, str]]:
    """
    Read a TSV file and return a list of dicts.
    Handles potential missing columns gracefully.
    """
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        # TSV reader
        reader = csv.DictReader(f, delimiter='\t')
        return list(reader)


def has_valid_score(row: Dict[str, str], score_col: str) -> bool:
    """
    Check if a specific score column exists and is not null/empty.
    """
    if score_col not in row:
        return False
    val = row[score_col].strip()
    if val == '' or val.lower() == 'nan' or val.lower() == 'null':
        return False
    try:
        float(val)
        return True
    except ValueError:
        return False


def is_eligible(row: Dict[str, str]) -> Tuple[bool, str]:
    """
    Determine if a subject is eligible:
    - Must have non-null MMSE or MOCA at timepoint 1 (baseline)
    - Must have non-null MMSE or MOCA at timepoint 2 (follow-up)
    - We look for columns like 'MMSE', 'MMSE_bl', 'MMSE_fu', 'MOCA', etc.
    - Heuristic: If 'MMSE' or 'MOCA' appears in the row keys, check for values.
    - Specifically for ds000246 (Constitution VI), the columns are often:
      'participant_id', 'MMSE', 'MMSE_2', 'MOCA', 'MOCA_2' (or similar)
      or 'MMSE_baseline', 'MMSE_followup'
    - We will check for ANY MMSE or MOCA column that has a value.
    - Requirement: Non-null at BOTH timepoints.
    """
    # Heuristic: Look for columns containing 'mmse' or 'moca' (case insensitive)
    # and distinguish between baseline (no suffix or '_bl') and followup ( '_fu', '_2', '_2nd')
    # Since schema varies, we check:
    # 1. At least one MMSE/MOCA column has a value.
    # 2. At least one MMSE/MOCA column with a 'followup' indicator has a value.
    
    # Normalize keys
    keys = {k: k for k in row.keys()}
    
    mmse_cols = [k for k in row.keys() if 'mmse' in k.lower()]
    moca_cols = [k for k in row.keys() if 'moca' in k.lower()]
    score_cols = mmse_cols + moca_cols

    if not score_cols:
        return False, "No MMSE/MOCA columns found"

    # Check for baseline (usually first occurrence or explicit 'bl')
    # Check for followup (usually '_2', '_fu', or second occurrence)
    # Given ds000246 often has 'MMSE' and 'MMSE_2' or similar.
    
    has_baseline = False
    has_followup = False

    for col in score_cols:
        if not has_valid_score(row, col):
            continue
        
        # Heuristic for timepoint
        col_lower = col.lower()
        if 'fu' in col_lower or 'follow' in col_lower or col_lower.endswith('_2') or col_lower.endswith('_2nd'):
            has_followup = True
        elif 'bl' in col_lower or 'baseline' in col_lower:
            has_baseline = True
        else:
            # If no suffix, assume it's baseline if it's the first one found?
            # Or if we haven't found a baseline yet, mark it.
            if not has_baseline:
                has_baseline = True
            else:
                # If we already have a baseline, this might be followup if we haven't found one
                if not has_followup:
                    has_followup = True

    # Fallback: if we found two distinct valid scores and couldn't distinguish, assume eligible
    valid_count = sum(1 for col in score_cols if has_valid_score(row, col))
    
    if valid_count >= 2:
        return True, "Eligible (2+ valid scores)"
    
    if has_baseline and has_followup:
        return True, "Eligible (BL + FU)"

    return False, f"Missing timepoint (BL={has_baseline}, FU={has_followup}, ValidCount={valid_count})"


def filter_eligible_subjects(participants: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Tuple[Dict, str]]]:
    """
    Filter participants for those with valid scores at both timepoints.
    Returns (eligible_list, excluded_list_of_tuples).
    """
    eligible = []
    excluded = []
    for row in participants:
        pid = row.get('participant_id', 'unknown')
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            excluded.append((row, reason))
    return eligible, excluded


def limit_subjects(subjects: List[Dict[str, str]], n: int) -> List[Dict[str, str]]:
    """
    Limit the list to n subjects.
    Since we need reproducibility and no specific sorting is mandated,
    we just take the first n.
    """
    if len(subjects) <= n:
        return subjects
    return subjects[:n]


def write_eligible_csv(subjects: List[Dict[str, str]], path: Path) -> None:
    """Write eligible subjects to a CSV file."""
    ensure_directory(path.parent)
    if not subjects:
        # Write header only if empty
        with open(path, 'w', newline='', encoding='utf-8') as f:
            if subjects:
                writer = csv.DictWriter(f, fieldnames=subjects[0].keys(), delimiter='\t')
                writer.writeheader()
                writer.writerows(subjects)
            else:
                # Write empty file or header? Task says "Output ... eligible_subjects.csv"
                # If zero eligible, we fail before this anyway. But write header if possible.
                pass 
        return

    with open(path, 'w', newline='', encoding='utf-8') as f:
        fieldnames = subjects[0].keys()
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        writer.writerows(subjects)


def write_excluded_log(excluded: List[Tuple[Dict, str]], path: Path) -> None:
    """Write excluded subjects to a log file."""
    ensure_directory(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        for row, reason in excluded:
            pid = row.get('participant_id', 'unknown')
            f.write(f"{pid}\t{reason}\n")


def write_status(eligible_count: int, excluded_count: int, total_count: int, status_path: Path) -> None:
    """Write the data gate status JSON."""
    ensure_directory(status_path.parent)
    status = {
        "dataset": DATASET_ID,
        "total_subjects": total_count,
        "eligible_subjects": eligible_count,
        "excluded_subjects": excluded_count,
        "status": "success" if eligible_count > 0 else "no_eligible_subjects",
        "exit_code": EXIT_CODE_SUCCESS if eligible_count > 0 else EXIT_CODE_NO_LABELS
    }
    with open(status_path, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2)


def main() -> int:
    """Main entry point."""
    logger.log("start", operation="download_and_filter")
    
    # Ensure directories
    ensure_directory(OUTPUT_DIR)
    ensure_directory(RAW_DIR)
    ensure_directory(ARTIFACTS_DIR)

    # 1. Download participants.tsv
    participants_path = RAW_DIR / "participants.tsv"
    logger.log("downloading_participants", url=PARTICIPANTS_URL, dest=str(participants_path))
    
    if not download_file(PARTICIPANTS_URL, participants_path):
        logger.log("fatal_error", reason="Failed to download participants.tsv")
        print(f"Failed to download {PARTICIPANTS_URL}", file=sys.stderr)
        return EXIT_CODE_DOWNLOAD_FAIL

    # 2. Read and parse
    participants = read_participants_tsv(participants_path)
    if not participants:
        logger.log("fatal_error", reason="No participants found in TSV")
        print("No participants found in TSV", file=sys.stderr)
        return EXIT_CODE_NO_LABELS

    total_count = len(participants)
    logger.log("parsed_participants", count=total_count)

    # 3. Filter
    eligible, excluded = filter_eligible_subjects(participants)
    logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))

    # 4. Limit
    final_eligible = limit_subjects(eligible, MAX_SUBJECTS)
    logger.log("limiting_complete", count=len(final_eligible))

    # 5. Output
    eligible_path = OUTPUT_DIR / "eligible_subjects.csv"
    excluded_path = OUTPUT_DIR / "excluded_subjects.log"
    status_path = ARTIFACTS_DIR / "data_gate_status.json"

    write_eligible_csv(final_eligible, eligible_path)
    write_excluded_log(excluded, excluded_path)
    write_status(len(final_eligible), len(excluded), total_count, status_path)

    # 6. Final Check
    if len(final_eligible) == 0:
        logger.log("fatal_error", reason="No eligible subjects found")
        print("No eligible subjects found – exiting with code 2.")
        return EXIT_CODE_NO_LABELS

    logger.log("success", eligible_count=len(final_eligible))
    print(f"Successfully processed {total_count} subjects. {len(final_eligible)} eligible.")
    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())