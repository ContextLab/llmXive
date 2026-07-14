"""
T017: Download ds000246, parse BIDS metadata, filter for longitudinal MMSE/MOCA,
limit to N=100, and output eligible/excluded lists and status JSON.

This script does NOT fabricate data. It attempts to fetch metadata from OpenNeuro.
If the dataset is unavailable or the environment lacks network access, it fails
with a clear error (Exit Code 1) rather than generating fake rows.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project utilities (as per API surface)
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json, save_text

# Constants
DATASET_ID = "ds000246"
BASE_URL = "https://api.openneuro.org"
MAX_ELIGIBLE = 100
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_SUCCESS = 0
EXIT_CODE_FAILURE = 1

# Paths (relative to project root)
DATA_RAW_DIR = Path("data/raw") / DATASET_ID
DATA_PROCESSED_DIR = Path("data/processed")
DATA_ARTIFACTS_DIR = Path("data/artifacts")

ELIGIBLE_CSV = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS_DIR / "data_gate_status.json"

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    ensure_dir(str(path))


def download_dataset_metadata() -> Optional[Dict[str, Any]]:
    """
    Fetch dataset metadata from OpenNeuro API.
    Returns the parsed JSON or None if fetch fails.
    """
    url = f"{BASE_URL}/ds/{DATASET_ID}/dataset/dataset_description"
    logger.log("fetch_metadata", url=url)
    try:
        # Note: In a real CI environment without network, this will fail.
        # We use urllib.request to avoid external dependencies if possible,
        # but requests is listed in requirements.txt.
        try:
            import requests
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.log("fetch_failed", status=resp.status_code)
                return None
        except ImportError:
            import urllib.request
            import json as stdlib_json
            with urllib.request.urlopen(url, timeout=30) as f:
                data = f.read()
                return stdlib_json.loads(data)
    except Exception as e:
        logger.log("fetch_error", error=str(e))
        return None


def download_participants_file() -> Optional[Path]:
    """
    Download the participants.tsv file from OpenNeuro.
    Returns the path to the downloaded file or None.
    """
    ensure_directory(DATA_RAW_DIR)
    url = f"https://openneuro.org/datasets/{DATASET_ID}/file-display/{DATASET_ID}:participants.tsv"
    # OpenNeuro often serves files via a specific CDN or direct link.
    # If the direct link fails, we might need to scrape the file list.
    # For robustness, we try a direct fetch first.
    output_path = DATA_RAW_DIR / "participants.tsv"
    
    logger.log("fetch_participants", url=url, output=str(output_path))
    
    try:
        import requests
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(resp.content)
            return output_path
        else:
            # Fallback: try the git-annex style link or a different format
            # OpenNeuro often has a JSON index.
            logger.log("fetch_participants_failed", status=resp.status_code)
            return None
    except ImportError:
        try:
            import urllib.request
            urllib.request.urlretrieve(url, str(output_path))
            if output_path.exists():
                return output_path
        except Exception:
            pass
        return None
    except Exception as e:
        logger.log("fetch_participants_error", error=str(e))
        return None


def read_participants_tsv(path: Path) -> List[Dict[str, str]]:
    """Read a TSV file into a list of dictionaries."""
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        return list(reader)


def has_valid_score(row: Dict[str, str], score_col: str) -> bool:
    """Check if a score column exists and is not null/empty."""
    val = row.get(score_col, "")
    if val is None or val.strip() == "":
        return False
    try:
        float(val)
        return True
    except ValueError:
        return False


def is_eligible(row: Dict[str, str]) -> Tuple[bool, str]:
    """
    Determine if a subject is eligible.
    Eligibility: Has non-null MMSE or MOCA at BOTH timepoints.
    Assumes columns like 'MMSE_t1', 'MMSE_t2', 'MOCA_t1', 'MOCA_t2'.
    Returns (is_eligible, reason).
    """
    # Check for MMSE at both timepoints
    has_mmse = has_valid_score(row, 'MMSE_t1') and has_valid_score(row, 'MMSE_t2')
    # Check for MOCA at both timepoints
    has_moca = has_valid_score(row, 'MOCA_t1') and has_valid_score(row, 'MOCA_t2')
    
    if has_mmse or has_moca:
        return True, "longitudinal_score_available"
    
    reasons = []
    if not has_mmse and not has_moca:
        reasons.append("no_longitudinal_cognitive_scores")
    elif not (has_valid_score(row, 'MMSE_t1') and has_valid_score(row, 'MMSE_t2')):
        reasons.append("incomplete_mmse")
    elif not (has_valid_score(row, 'MOCA_t1') and has_valid_score(row, 'MOCA_t2')):
        reasons.append("incomplete_moca")
        
    return False, "; ".join(reasons) if reasons else "unknown"


def filter_eligible_subjects(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Separate eligible and excluded subjects."""
    eligible = []
    excluded = []
    for row in rows:
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row)
        else:
            row['exclusion_reason'] = reason
            excluded.append(row)
    return eligible, excluded


def limit_subjects(subjects: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    """Limit the number of subjects to N."""
    if len(subjects) <= limit:
        return subjects
    return subjects[:limit]


def write_eligible_csv(subjects: List[Dict[str, str]], path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_directory(path.parent)
    if not subjects:
        # Write empty file with headers if we can infer them, or just touch it
        with open(path, 'w', newline='', encoding='utf-8') as f:
            f.write("subject_id\n") # Minimal header
        return

    fieldnames = list(subjects[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(subjects)


def write_excluded_log(subjects: List[Dict[str, str]], path: Path) -> None:
    """Write excluded subjects to a log file."""
    ensure_directory(path.parent)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# Excluded Subjects Log - {len(subjects)} subjects\n")
        f.write("# Format: subject_id | reason\n")
        for sub in subjects:
            sub_id = sub.get('participant_id', sub.get('subject_id', 'unknown'))
            reason = sub.get('exclusion_reason', 'unknown')
            f.write(f"{sub_id} | {reason}\n")


def write_status(status: Dict[str, Any], path: Path) -> None:
    """Write the status JSON file."""
    ensure_directory(path.parent)
    save_json(status, str(path))


def main() -> int:
    """Main entry point."""
    logger.log("start_task", task_id="T017")
    
    # 1. Attempt to download metadata (optional but good for verification)
    metadata = download_dataset_metadata()
    if metadata:
        logger.log("metadata_fetched", id=metadata.get('id', DATASET_ID))
    else:
        logger.log("metadata_fetch_failed", note="Proceeding without metadata")

    # 2. Download participants.tsv
    participants_path = download_participants_file()
    if not participants_path:
        logger.log("fatal_error", msg="Could not download participants.tsv from OpenNeuro")
        # In a real environment, this might be a network issue.
        # We cannot fabricate data.
        status = {
            "dataset": DATASET_ID,
            "total_subjects": 0,
            "eligible_subjects": 0,
            "excluded_subjects": 0,
            "status": "failed",
            "exit_code": EXIT_CODE_FAILURE,
            "error": "Download failed: participants.tsv not found"
        }
        write_status(status, STATUS_JSON)
        return EXIT_CODE_FAILURE

    # 3. Parse TSV
    rows = read_participants_tsv(participants_path)
    total_subjects = len(rows)
    logger.log("parsed_participants", count=total_subjects)

    if total_subjects == 0:
        logger.log("fatal_error", msg="No subjects found in participants.tsv")
        status = {
            "dataset": DATASET_ID,
            "total_subjects": 0,
            "eligible_subjects": 0,
            "excluded_subjects": 0,
            "status": "failed",
            "exit_code": EXIT_CODE_FAILURE,
            "error": "Empty participants.tsv"
        }
        write_status(status, STATUS_JSON)
        return EXIT_CODE_FAILURE

    # 4. Filter
    eligible, excluded = filter_eligible_subjects(rows)
    logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))

    # 5. Limit
    limited_eligible = limit_subjects(eligible, MAX_ELIGIBLE)
    if len(limited_eligible) < len(eligible):
        logger.log("limit_applied", original=len(eligible), limited=len(limited_eligible))

    # 6. Check for zero eligible
    if len(limited_eligible) == 0:
        logger.log("fatal_error", msg="Zero eligible subjects found")
        status = {
            "dataset": DATASET_ID,
            "total_subjects": total_subjects,
            "eligible_subjects": 0,
            "excluded_subjects": len(excluded),
            "status": "failed",
            "exit_code": EXIT_CODE_NO_LABELS,
            "error": "No eligible subjects with longitudinal scores"
        }
        write_status(status, STATUS_JSON)
        write_eligible_csv([], ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)
        return EXIT_CODE_NO_LABELS

    # 7. Write outputs
    write_eligible_csv(limited_eligible, ELIGIBLE_CSV)
    write_excluded_log(excluded, EXCLUDED_LOG)

    status = {
        "dataset": DATASET_ID,
        "total_subjects": total_subjects,
        "eligible_subjects": len(limited_eligible),
        "excluded_subjects": len(excluded),
        "status": "success",
        "exit_code": EXIT_CODE_SUCCESS
    }
    write_status(status, STATUS_JSON)

    logger.log("task_complete", status="success")
    return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main())
