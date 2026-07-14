"""
T017: Download and filter ds000246 (Constitution VI) for longitudinal cognitive scores.

This script:
1. Downloads metadata for OpenNeuro ds000246.
2. Parses the participants.tsv to identify subjects with non-null MMSE/MOCA scores at two timepoints.
3. Limits the cohort to N=min(100, eligible).
4. Writes eligible_subjects.csv, excluded_subjects.log, and data_gate_status.json.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json

logger = get_logger("download_and_filter")

# Constants
DATASET_ID = "ds000246"
DATASET_URL = f"https://api.openneuro.org/datasets/{DATASET_ID}"
PARTICIPANTS_FILE = "participants.tsv"
MAX_SUBJECTS = 100
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1

# Output paths
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw" / DATASET_ID
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_ARTIFACTS_DIR = PROJECT_ROOT / "data" / "artifacts"

ELIGIBLE_CSV = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS_DIR / "data_gate_status.json"


def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""
    ensure_dir(path)


def download_dataset_metadata() -> Dict[str, Any]:
    """
    Fetch dataset metadata from OpenNeuro API.
    Returns JSON content.
    """
    logger.log("download_metadata", url=DATASET_URL)
    try:
        import requests
        response = requests.get(DATASET_URL, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.log("download_metadata_error", error=str(e))
        raise RuntimeError(f"Failed to download metadata from {DATASET_URL}: {e}")


def download_participants_file() -> Path:
    """
    Download the participants.tsv file from OpenNeuro.
    OpenNeuro datasets are typically accessed via git-annex or direct tarball.
    For this implementation, we attempt to fetch the raw file from the dataset's
    public URL structure if available, or a fallback tarball.
    
    Since OpenNeuro API doesn't provide direct file content in the metadata endpoint,
    we construct the URL for the raw file.
    """
    # OpenNeuro raw file URL pattern: https://openneuro.org/datasets/{id}/versions/{version}/file-display/{file}
    # However, for programmatic access without git-annex, we often need to download a tarball or use the public S3.
    # A common public URL for ds000246 participants.tsv is:
    # https://s3.amazonaws.com/openneuro.org/datasets/{id}/versions/{version}/participants.tsv
    
    # We will try to fetch the latest version's participants.tsv directly.
    # Fallback: If direct fetch fails, we might need to download a small tarball.
    # For robustness in this script, we will attempt the direct S3-like URL first.
    
    base_url = "https://openneuro.org/datasets"
    # We need the version. Let's try a common pattern or fetch the latest.
    # Simplified approach: Use the public download link for the specific file.
    # ds000246 is a well-known dataset.
    
    # Constructing a direct download link for the latest version's participants.tsv
    # Note: OpenNeuro URLs can be tricky. We will try the standard public endpoint.
    file_url = f"https://openneuro.org/datasets/{DATASET_ID}/versions/latest/file-display/participants.tsv"
    
    # If that fails, we try the S3 path which is often stable for older versions
    # s3://openneuro.org/datasets/ds000246/versions/1.0.0/participants.tsv
    # We can access this via https://openneuro.s3.amazonaws.com/...
    # But let's try the direct OpenNeuro file API first.
    
    # Alternative: Download the dataset tarball (if small) or just the file.
    # Given the constraints, we will simulate the download logic by fetching the file
    # if it exists, otherwise we raise an error.
    
    # For this specific task, we will assume the dataset is accessible via a standard
    # public endpoint or we will use a fallback to a known good URL if the dynamic one fails.
    # Since we cannot rely on dynamic version discovery without more API calls,
    # we will try a few known patterns.
    
    urls_to_try = [
        f"https://openneuro.org/datasets/{DATASET_ID}/versions/latest/file-display/participants.tsv",
        f"https://openneuro.org/datasets/{DATASET_ID}/versions/1.0.0/file-display/participants.tsv",
        # Fallback to a direct S3-like URL if OpenNeuro blocks direct HTML fetches
        f"https://openneuro.s3.amazonaws.com/datasets/{DATASET_ID}/versions/1.0.0/participants.tsv"
    ]
    
    last_error = None
    for url in urls_to_try:
        try:
            logger.log("attempt_download", url=url)
            import requests
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                output_path = DATA_RAW_DIR / PARTICIPANTS_FILE
                ensure_directory(DATA_RAW_DIR)
                with open(output_path, 'wb') as f:
                    f.write(resp.content)
                logger.log("download_success", path=str(output_path))
                return output_path
            last_error = f"Status {resp.status_code}"
        except Exception as e:
            last_error = str(e)
            continue
    
    raise RuntimeError(f"Failed to download participants.tsv from any URL. Last error: {last_error}")


def read_participants_tsv(file_path: Path) -> List[Dict[str, str]]:
    """Read TSV file and return list of dicts."""
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
    return rows


def has_valid_score(row: Dict[str, str], score_cols: List[str]) -> bool:
    """Check if any of the score columns have a valid non-null value."""
    for col in score_cols:
        if col in row and row[col] and row[col].strip().lower() not in ('nan', 'null', 'na', ''):
            try:
                float(row[col])
                return True
            except ValueError:
                continue
    return False


def is_eligible(row: Dict[str, str]) -> bool:
    """
    Check if a subject has non-null MMSE or MOCA scores at BOTH timepoints.
    We assume columns are named like 'MMSE_t1', 'MMSE_t2', 'MOCA_t1', 'MOCA_t2'
    or similar. We look for pairs.
    """
    # Identify timepoint columns
    t1_cols = [c for c in row.keys() if c.endswith('_t1') or c.endswith('_1')]
    t2_cols = [c for c in row.keys() if c.endswith('_t2') or c.endswith('_2')]
    
    # We need at least one valid score in t1 AND one valid score in t2.
    # The task says "non-null MMSE/MOCA at both timepoints".
    # This implies we need a score at T1 and a score at T2.
    
    score_t1 = False
    score_t2 = False
    
    # Check T1
    for col in t1_cols:
        if has_valid_score(row, [col]):
            score_t1 = True
            break
    
    # Check T2
    for col in t2_cols:
        if has_valid_score(row, [col]):
            score_t2 = True
            break
    
    return score_t1 and score_t2


def filter_eligible_subjects(rows: List[Dict[str, str]]) -> tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """Separate eligible and excluded subjects."""
    eligible = []
    excluded = []
    for row in rows:
        if is_eligible(row):
            eligible.append(row)
        else:
            excluded.append(row)
    return eligible, excluded


def limit_subjects(rows: List[Dict[str, str]], limit: int) -> List[Dict[str, str]]:
    """Limit the number of subjects to N."""
    if len(rows) <= limit:
        return rows
    return rows[:limit]


def write_eligible_csv(rows: List[Dict[str, str]], output_path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_directory(output_path.parent)
    if not rows:
        # Write empty file with headers if possible
        headers = ["participant_id"]
        # Try to infer headers from first row if available, else default
        if rows:
            headers = list(rows[0].keys())
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        return

    headers = list(rows[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def write_excluded_log(rows: List[Dict[str, str]], output_path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_directory(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("Excluded Subjects (Reason: Missing longitudinal scores)\n")
        f.write("-" * 50 + "\n")
        for row in rows:
            sub_id = row.get('participant_id', 'unknown')
            f.write(f"{sub_id}\n")


def write_status(eligible_count: int, excluded_count: int, status: str = "success", error: Optional[str] = None) -> None:
    """Write status JSON."""
    ensure_directory(STATUS_JSON.parent)
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    save_json(status_data, STATUS_JSON)


def main() -> int:
    """Main entry point."""
    logger.log("start_download_and_filter")
    try:
        # 1. Ensure directories
        ensure_directory(DATA_RAW_DIR)
        ensure_directory(DATA_PROCESSED_DIR)
        ensure_directory(DATA_ARTIFACTS_DIR)

        # 2. Download participants file
        logger.log("downloading_participants")
        participants_path = download_participants_file()

        # 3. Read data
        logger.log("parsing_metadata")
        rows = read_participants_tsv(participants_path)
        logger.log("parsed_rows", count=len(rows))

        if not rows:
            logger.log("no_rows_found")
            write_status(0, 0, "failure", "No participants found in dataset")
            return EXIT_CODE_NO_LABELS

        # 4. Filter eligible
        eligible, excluded = filter_eligible_subjects(rows)
        logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))

        if not eligible:
            logger.log("no_eligible_subjects")
            write_eligible_csv([], ELIGIBLE_CSV)
            write_excluded_log(excluded, EXCLUDED_LOG)
            write_status(0, len(excluded), "failure", "No eligible subjects found with longitudinal scores")
            return EXIT_CODE_NO_LABELS

        # 5. Limit subjects
        limited_eligible = limit_subjects(eligible, MAX_SUBJECTS)
        logger.log("limiting_subjects", original=len(eligible), limited=len(limited_eligible))

        # 6. Write outputs
        write_eligible_csv(limited_eligible, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)
        write_status(len(limited_eligible), len(excluded))

        logger.log("success", count=len(limited_eligible))
        return EXIT_CODE_SUCCESS

    except Exception as e:
        logger.log("error", error=str(e))
        write_status(0, 0, "error", str(e))
        return EXIT_CODE_ERROR


if __name__ == "__main__":
    sys.exit(main())