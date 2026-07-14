"""
T017: Download and Filter ds000246 (Constitution VI, FR-001)

This script downloads the OpenNeuro dataset ds000246, parses BIDS metadata
(specifically participants.tsv), filters for subjects with non-null MMSE/MOCA
scores at both timepoints, limits the cohort to N=100, and outputs the
eligible subject list, exclusion log, and status JSON.

It relies on the real data downloaded by T004c (code/00_data_gate.py) or
attempts to download it if not present.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import shared utilities from the project structure
# Note: We assume the project root is the parent of 'code'
# We add the code directory to path to allow relative imports if needed,
# but standard imports from utils should work if run as python code/01_...
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger, log_operation
from utils.io import save_json, ensure_dir

# Configuration
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://openneuro.org/datasets"
# We will attempt to fetch the participants.tsv directly or from a local copy
# If local copy exists (from T004c), use it. Otherwise, try to download.
RAW_DATA_DIR = Path("data/raw") / DATASET_ID
PARTICIPANTS_FILE = RAW_DATA_DIR / "participants.tsv"

OUTPUT_ELIGIBLE = Path("data/processed/eligible_subjects.csv")
OUTPUT_EXCLUDED = Path("data/processed/excluded_subjects.log")
OUTPUT_STATUS = Path("data/artifacts/data_gate_status.json")

MAX_SUBJECTS = 100
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_ELIGIBLE = 2
EXIT_CODE_IO_ERROR = 3

logger = get_logger("download_and_filter")

def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""
    path.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest: Path, retries: int = 3) -> bool:
    """Download a file with retries."""
    ensure_directory(dest.parent)
    for attempt in range(retries):
        try:
            logger.log("download_file", url=str(url), attempt=attempt)
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            with open(dest, 'wb') as f:
                f.write(response.content)
            logger.log("download_file_success", path=str(dest))
            return True
        except Exception as e:
            logger.log("download_file_error", error=str(e), attempt=attempt)
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
            else:
                return False
    return False

def download_dataset_metadata(dataset_id: str) -> bool:
    """
    Attempt to download the participants.tsv for the dataset.
    OpenNeuro provides a direct download link structure.
    """
    # Construct the likely URL for participants.tsv in the latest version
    # OpenNeuro usually serves files via git-annex or direct links.
    # A common pattern for direct download of a specific file is:
    # https://openneuro.org/datasets/{id}/versions/{version}/file-display/{path}
    # However, for robustness, we check if the file exists locally first (T004c).
    # If not, we try a known public mirror or the OpenNeuro API.
    # For this implementation, we assume T004c should have handled the initial fetch.
    # If not present, we try to fetch it from the OpenNeuro CDN.
    
    # Fallback URL pattern for OpenNeuro files (often requires the version)
    # Since we don't know the version, we try the generic "latest" or list files.
    # Given the constraints, we will assume the file must be present from T004c
    # or we try to fetch a known stable URL if available.
    
    # Let's try to fetch the dataset description to get version, then the file.
    api_url = f"https://api.openneuro.org/datasets/{dataset_id}"
    try:
        resp = requests.get(api_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            # Try to find the latest version
            versions = data.get('versions', [])
            if versions:
                latest_version = versions[0].get('id')
                # Construct file URL
                # OpenNeuro file download URL pattern:
                # https://openneuro.org/datasets/{id}/versions/{version}/file-display/participants.tsv
                file_url = f"https://openneuro.org/datasets/{dataset_id}/versions/{latest_version}/file-display/participants.tsv"
                return download_file(file_url, PARTICIPANTS_FILE)
    except Exception as e:
        logger.log("api_lookup_failed", error=str(e))
    
    # If API fails, return False to indicate we rely on local file
    return False

def read_participants_tsv(path: Path) -> List[Dict[str, Any]]:
    """Read the BIDS participants.tsv file."""
    if not path.exists():
        logger.log("participants_file_missing", path=str(path))
        return []
    
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        # BIDS participants.tsv is tab-separated
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
    return rows

def has_valid_score(row: Dict[str, Any], score_col: str) -> bool:
    """Check if a score column exists and is not null/empty."""
    if score_col not in row:
        return False
    val = row[score_col]
    if val is None or val == '' or val == 'n/a' or val == 'NA' or val == 'NaN':
        return False
    try:
        float(val)
        return True
    except ValueError:
        return False

def is_eligible(row: Dict) -> Tuple[bool, str]:
    """
    Check eligibility:
    - Must have non-null MMSE or MOCA at timepoint 1 (baseline)
    - Must have non-null MMSE or MOCA at timepoint 2 (follow-up)
    - We look for columns like 'MMSE', 'MMSE_2', 'MOCA', 'MOCA_2' or similar.
    - Based on ds000246 (Constitution VI), columns might be 'MMSE', 'MMSE_followup' or similar.
    - We will assume standard naming: 'MMSE', 'MMSE_2' OR 'MOCA', 'MOCA_2'.
    - If neither pair is fully available, subject is excluded.
    """
    # Heuristic: Look for any MMSE or MOCA columns
    # We need at least one pair (baseline, followup)
    mmse_cols = [k for k in row.keys() if 'MMSE' in k.upper()]
    moca_cols = [k for k in row.keys() if 'MOCA' in k.upper()]
    
    # We need to find a baseline and a followup.
    # Assumption: Columns are named consistently, e.g., MMSE, MMSE_2
    # or MMSE_baseline, MMSE_followup.
    # We'll try to match pairs.
    
    def has_pair(cols):
        if len(cols) < 2:
            return False
        # Simple heuristic: first is baseline, second is followup
        # Check if both are valid
        if has_valid_score(row, cols[0]) and has_valid_score(row, cols[1]):
            return True
        # Try all permutations? No, assume order.
        return False

    # Check MMSE
    if has_pair(mmse_cols):
        return True
    # Check MOCA
    if has_pair(moca_cols):
        return True
    
    return False

def filter_eligible_subjects(rows: List[Dict[str, Any]]) -> tuple[List[Dict], List[Dict]]:
    """Separate eligible and excluded subjects."""
    eligible = []
    excluded = []
    for row in rows:
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    return eligible, excluded

def limit_subjects(eligible: List[Dict], n: int) -> List[Dict]:
    """Limit the number of subjects to n."""
    if len(eligible) <= n:
        return eligible
    # Sort by participant_id to ensure reproducibility
    eligible_sorted = sorted(eligible, key=lambda x: x.get('participant_id', ''))
    return eligible_sorted[:n]

def write_eligible_csv(subjects: List[Dict], path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_dir(path)
    if not subjects:
        # Write empty file with headers? Or just empty.
        # BIDS style: write headers if possible, else empty.
        with open(path, 'w', newline='', encoding='utf-8') as f:
            f.write("")
        return

    fieldnames = list(subjects[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(subjects)

def write_excluded_log(subjects: List[Dict], path: Path) -> None:
    """Write excluded subjects to log."""
    ensure_dir(path)
    with open(path, 'w', encoding='utf-8') as f:
        f.write("Excluded Subjects (Missing longitudinal MMSE/MOCA)\n")
        f.write("=" * 50 + "\n")
        for sub in subjects:
            pid = sub.get('participant_id', 'unknown')
            f.write(f"Subject: {pid}\n")
            # Log reason
            f.write(f"  Reason: Missing valid MMSE/MOCA pair\n")
            f.write(f"  Data: {sub}\n")
            f.write("-" * 20 + "\n")

def write_status(status: Dict, path: Path) -> None:
    """Write status JSON."""
    ensure_dir(path)
    save_json(status, path)

def main() -> int:
    """Main entry point."""
    logger.log("main_start", dataset=DATASET_ID)
    
    # 1. Ensure raw data directory exists
    ensure_directory(RAW_DATA_DIR)
    
    # 2. Download metadata if not present
    if not PARTICIPANTS_FILE.exists():
        logger.log("downloading_metadata", source="OpenNeuro")
        success = download_dataset_metadata(DATASET_ID)
        if not success:
            logger.log("error", message="Failed to download metadata and local file missing.")
            # Fail loudly
            return EXIT_CODE_IO_ERROR
    
    # 3. Read participants
    rows = read_participants_tsv(PARTICIPANTS_FILE)
    if not rows:
        logger.log("error", message="No participants found in TSV.")
        return EXIT_CODE_IO_ERROR
    
    logger.log("participants_loaded", count=len(rows))
    
    # 4. Filter
    eligible, excluded = filter_eligible_subjects(rows)
    logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))
    
    # 5. Limit
    limited = limit_subjects(eligible, MAX_SUBJECTS)
    logger.log("limiting_complete", count=len(limited))
    
    if len(limited) == 0:
        logger.log("error", message="No eligible subjects found.")
        # Write empty outputs
        write_eligible_csv([], OUTPUT_ELIGIBLE)
        write_excluded_log(excluded, OUTPUT_EXCLUDED)
        write_status({
            "dataset": DATASET_ID,
            "total_subjects": len(rows),
            "eligible_subjects": 0,
            "excluded_subjects": len(excluded),
            "status": "failed_no_eligible",
            "exit_code": EXIT_CODE_NO_ELIGIBLE
        }, OUTPUT_STATUS)
        return EXIT_CODE_NO_ELIGIBLE
    
    # 6. Write outputs
    write_eligible_csv(limited, OUTPUT_ELIGIBLE)
    write_excluded_log(excluded, OUTPUT_EXCLUDED)
    
    status = {
        "dataset": DATASET_ID,
        "total_subjects": len(rows),
        "eligible_subjects": len(limited),
        "excluded_subjects": len(excluded),
        "status": "success",
        "exit_code": EXIT_CODE_SUCCESS
    }
    write_status(status, OUTPUT_STATUS)
    
    logger.log("main_success", output_file=str(OUTPUT_ELIGIBLE))
    return EXIT_CODE_SUCCESS

if __name__ == "__main__":
    sys.exit(main())