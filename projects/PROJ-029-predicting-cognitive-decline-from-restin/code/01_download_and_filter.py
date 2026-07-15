from __future__ import annotations

import csv
import json
import os
import sys
import time
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import pandas as pd
from tqdm import tqdm

# Import from existing API surface
from utils.io import ensure_dir, save_json, save_csv
from utils.logger import get_logger, log_operation

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://api.openneuro.org"
PARTICIPANTS_FILE = "participants.tsv"
MAX_SUBJECTS = 100
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_ERROR = 1

# Output paths (relative to project root)
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
DATA_ARTIFACTS_DIR = Path("data/artifacts")
ELIGIBLE_CSV = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS_DIR / "data_gate_status.json"

logger = get_logger("download_and_filter")

def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""
    ensure_dir(path)


def download_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """
    Download dataset metadata from OpenNeuro API.
    Returns metadata dict.
    """
    url = f"{OPENNEURO_BASE}/datasets/{dataset_id}"
    logger.log("download_metadata", url=url)
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.log("download_metadata_error", error=str(e))
        raise


def download_participants_file(dataset_id: str, output_path: Path) -> Path:
    """
    Download participants.tsv from OpenNeuro dataset.
    Returns path to downloaded file.
    """
    # OpenNeuro data download endpoint
    # Format: https://openneuro.org/datasets/{id}/versions/latest/file-download/{filename}
    # But API is complex; simpler to use git-annex or direct tarball if available.
    # For this implementation, we attempt to fetch via a known public tarball structure
    # or fallback to a direct participants.tsv fetch if accessible.
    
    # Strategy: Use the public file download URL pattern for participants.tsv
    # OpenNeuro public data is often accessible via:
    # https://openneuro.org/datasets/{id}/versions/{version}/file-download/participants.tsv
    # However, version is dynamic. We'll try to get the latest version from metadata first.
    
    try:
        metadata = download_dataset_metadata(dataset_id)
        # Attempt to find a direct link or use a standard pattern
        # OpenNeuro API v3 often provides a 'files' endpoint, but for simplicity:
        # We will try the direct public URL pattern which often works for participants.tsv
        base_url = f"https://openneuro.org/datasets/{dataset_id}/versions/latest"
        file_url = f"{base_url}/file-download/participants.tsv"
        
        # If the above fails, try the direct raw data link if known
        # Many OpenNeuro datasets have a direct link structure:
        # https://datasets.openneuro.org/datasets/{id}/versions/{version}/files/participants.tsv
        # We'll attempt a robust fetch loop.
        
        urls_to_try = [
            file_url,
            f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/file-download/participants.tsv",
            f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.1/file-download/participants.tsv",
            # Fallback: try to download the whole dataset manifest? No, too heavy.
            # We will assume the dataset is available and try the most common path.
        ]
        
        last_error = None
        for url in urls_to_try:
            try:
                logger.log("attempt_download", url=url)
                resp = requests.get(url, stream=True, timeout=60)
                if resp.status_code == 200:
                    ensure_directory(output_path.parent)
                    with open(output_path, 'wb') as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            f.write(chunk)
                    logger.log("download_success", path=str(output_path))
                    return output_path
                else:
                    last_error = f"Status {resp.status_code}"
            except Exception as e:
                last_error = str(e)
                continue

        raise RuntimeError(f"Failed to download participants.tsv after trying multiple URLs. Last error: {last_error}")
        
    except Exception as e:
        logger.log("download_participants_error", error=str(e))
        raise

def download_participants_file(dataset_id: str, output_path: Path) -> Path:
    """Download participants.tsv from OpenNeuro."""
    # OpenNeuro dataset download URL pattern for specific files
    # Using the git-annex style URL or direct download if available
    # For ds000246, we try the direct file URL structure
    base_url = f"https://datasets.openneuro.org/datasets/{dataset_id}/version-1.0.0"
    file_url = f"{base_url}/{PARTICIPANTS_FILE}"
    
    # Fallback: try the latest version
    if not requests.head(file_url).ok:
        # Try to find the latest version
        meta = download_dataset_metadata(dataset_id)
        version = meta.get("latestSnapshot", {}).get("id", "1.0.0")
        base_url = f"https://datasets.openneuro.org/datasets/{dataset_id}/version-{version}"
        file_url = f"{base_url}/{PARTICIPANTS_FILE}"

def read_participants_tsv(file_path: Path) -> pd.DataFrame:
    """Read participants.tsv into a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"Participants file not found: {file_path}")
    try:
        df = pd.read_csv(file_path, sep='\t')
        return df
    except Exception as e:
        logger.log("read_participants_error", error=str(e))
        raise

def read_participants_tsv(file_path: Path) -> pd.DataFrame:
    """Read participants.tsv into a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"Participants file not found: {file_path}")
    return pd.read_csv(file_path, sep='\t')

def has_valid_score(row: pd.Series) -> bool:
    """
    Check if a row has valid MMSE or MOCA scores at both timepoints.
    We expect columns like 'MMSE_baseline', 'MMSE_followup', 'MOCA_baseline', 'MOCA_followup'
    or generic 'score_t1', 'score_t2'.
    Based on ds000246 (Constitution VI), we look for common naming conventions.
    """
    # Normalize column names to lowercase for checking
    cols = [c.lower() for c in row.index]
    
    # Define potential column names for scores
    # We need at least two timepoints.
    # Common patterns: mmse_baseline, mmse_followup, moca_baseline, moca_followup
    # Or: score_1, score_2, timepoint_1, timepoint_2
    
    # Strategy: Look for any column containing 'mmse' or 'moca' and check if there are at least 2 non-null values.
    score_cols = [c for c in row.index if 'mmse' in c.lower() or 'moca' in c.lower()]
    
    if len(score_cols) < 2:
        return False
    val = row[score_col]
    if pd.isna(val):
        return False
    try:
        float_val = float(val)
        return not pd.isna(float_val)
    except (ValueError, TypeError):
        return False

def is_eligible(row: pd.Series) -> bool:
    """
    Check if subject is eligible:
    - Has non-null MMSE or MOCA at timepoint 1 (baseline)
    - Has non-null MMSE or MOCA at timepoint 2 (follow-up)
    
    # Check if at least two of these columns have non-null numeric values
    valid_count = 0
    for col in score_cols:
        val = row[col]
        if pd.notna(val):
            try:
                float(val)
                valid_count += 1
            except (ValueError, TypeError):
                pass
    
    return valid_count >= 2


def is_eligible(row: pd.Series) -> Tuple[bool, str]:
    """
    Determine if a subject is eligible.
    Returns (is_eligible, reason).
    """
    # Check for subject ID
    if 'subject_id' not in row.index and 'participant_id' not in row.index:
        return False, "Missing subject ID"
    
    # Check for valid scores
    if not has_valid_score(row):
        return False, "Missing longitudinal cognitive scores (MMSE/MOCA)"
    
    return True, "Eligible"


def filter_eligible_subjects(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter subjects based on eligibility criteria.
    Returns (eligible_list, excluded_list).
    """
    eligible = []
    excluded = []
    
    for _, row in df.iterrows():
        is_elig, reason = is_eligible(row)
        if is_elig:
            eligible.append(row.to_dict())
        else:
            excluded.append({
                "subject_id": row.get("subject_id", row.get("participant_id", "unknown")),
                "reason": reason
            })
    
    return eligible, excluded


def limit_subjects(subjects: List[Dict[str, Any]], limit: int = MAX_SUBJECTS) -> List[Dict[str, Any]]:
    """Limit the number of subjects to the specified maximum."""
    return subjects[:limit]


def write_eligible_csv(subjects: List[Dict[str, Any]], output_path: Path) -> None:
    """Write eligible subjects to CSV."""
    if not subjects:
        # Write header only if empty to indicate no data
        ensure_dir(output_path)
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["subject_id"])
            writer.writeheader()
        return

    ensure_dir(output_path)
    # Determine all unique keys to ensure consistent columns
    all_keys = set()
    for s in subjects:
        all_keys.update(s.keys())
    # Ensure subject_id is first
    fieldnames = ["subject_id"] + [k for k in sorted(all_keys) if k != "subject_id"]
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(subjects)
    logger.log("write_eligible_csv", path=str(output_path), count=len(subjects))

def limit_subjects(eligible: List[Dict], n: int) -> List[Dict]:
    """Limit to n subjects."""
    return eligible[:n]

def write_excluded_log(excluded: List[Dict[str, Any]], output_path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_dir(output_path)
    with open(output_path, 'w') as f:
        for entry in excluded:
            f.write(f"{entry['subject_id']}: {entry['reason']}\n")
    logger.log("write_excluded_log", path=str(output_path), count=len(excluded))

def write_excluded_log(excluded: List[Dict], output_path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_directory(output_path.parent)
    with open(output_path, 'w') as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Reason: Missing longitudinal scores (MMSE/MOCA at both timepoints)\n\n")
        
        for entry in excluded:
            f.write(f"{entry['subject_id']}: {entry['reason']}\n")

def write_status(eligible_count: int, excluded_count: int, status: str, error: Optional[str] = None) -> None:
    """Write status JSON."""
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "excluded_count": excluded_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    ensure_dir(STATUS_JSON)
    save_json(status_data, str(STATUS_JSON))
    logger.log("write_status", path=str(STATUS_JSON), data=status_data)


@log_operation
def main() -> int:
    """Main entry point."""
    logger.log("main_start")
    
    try:
        # 1. Ensure directories
        ensure_directory(DATA_RAW_DIR)
        ensure_directory(DATA_PROCESSED_DIR)
        ensure_directory(DATA_ARTIFACTS_DIR)
        
        # 2. Download participants file
        participants_path = DATA_RAW_DIR / DATASET_ID / PARTICIPANTS_FILE
        logger.log("downloading_participants", path=str(participants_path))
        download_participants_file(DATASET_ID, participants_path)
        
        # 3. Read data
        df = read_participants_tsv(participants_path)
        logger.log("participants_loaded", rows=len(df), columns=list(df.columns))
        
        # 4. Filter
        eligible, excluded = filter_eligible_subjects(df)
        logger.log("filtering_complete", eligible=len(eligible), excluded=len(excluded))
        
        # 5. Limit
        eligible = limit_subjects(eligible, MAX_SUBJECTS)
        logger.log("limiting_complete", count=len(eligible))
        
        # 6. Write outputs
        write_eligible_csv(eligible, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)
        
        # 7. Status
        if len(eligible) == 0:
            write_status(0, len(excluded), "error", "No eligible subjects found")
            logger.log("main_end_error")
            return EXIT_CODE_NO_LABELS
        
        write_status(len(eligible), len(excluded), "success")
        logger.log("main_end_success")
        return EXIT_CODE_SUCCESS
        
    except Exception as e:
        logger.log("main_error", error=str(e))
        write_status(0, 0, "error", str(e))
        return EXIT_CODE_ERROR

if __name__ == "__main__":
    sys.exit(main())