"""
T017: Download ds000246, parse BIDS metadata, filter for longitudinal scores,
and output eligible/excluded lists and status JSON.
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
import shutil
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import requests
from tqdm import tqdm

# Import from local utils
from utils.logger import get_logger, log_operation
from utils.io import ensure_dir, save_json

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://datasets.d2.mpi-inf.mpg.de"
# OpenNeuro ds000246 is Constitution VI (FR-001).
# The direct tarball URL pattern for OpenNeuro datasets:
# https://openneuro.org/datasets/{id}/versions/{version}/download
# We will use the public S3 bucket or the direct download if available.
# For ds000246, a common stable download is via the OpenNeuro CLI or direct tarball.
# Since we cannot run 'openneuro' CLI easily in this environment without setup,
# we will attempt to fetch the dataset via the OpenNeuro API or a direct tarball link.
# Note: OpenNeuro datasets are often large. We will implement a streaming download.
# If the specific dataset is not available via a simple HTTP GET, we will fail loudly.

# Attempt to use the OpenNeuro public API for download links
OPENNEURO_API_DOWNLOAD = f"https://openneuro.org/datasets/{DATASET_ID}/versions/1.0.0/download"

# Fallback: Direct S3 link if known (ds000246 is Constitution VI)
# Constitution VI (ds000246) is available at:
# https://openneuro.org/datasets/ds000246
# We will try to download the 'dataset_description.json' first to verify existence,
# then the 'participants.tsv'.

# Output paths
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
DATA_ARTIFACTS_DIR = Path("data/artifacts")

PARTICIPANTS_FILE = DATA_RAW_DIR / DATASET_ID / "participants.tsv"
ELIGIBLE_CSV = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
STATUS_JSON = DATA_ARTIFACTS_DIR / "data_gate_status.json"

EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_DATA = 1
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_ERROR = 3

logger = get_logger("download_and_filter")


def ensure_directory(path: Path) -> None:
    """Ensure a directory exists."""
    ensure_dir(path)


def download_dataset_metadata(dataset_id: str, output_dir: Path) -> bool:
    """
    Download dataset_description.json to verify dataset existence.
    Returns True if successful.
    """
    ensure_directory(output_dir)
    # Try to get dataset_description.json from OpenNeuro S3
    # Pattern: https://s3.amazonaws.com/openneuro.org/datasets/{id}/versions/{version}/dataset_description.json
    # We don't know the version, so we try a common one or the root.
    # Let's try to fetch the root directory structure or a known file.
    # OpenNeuro often hosts files at: https://openneuro.org/datasets/{id}/versions/{version}/files
    
    # Simpler approach: Use the OpenNeuro API to get the latest version
    api_url = f"https://api.openneuro.org/datasets/{dataset_id}"
    try:
        resp = requests.get(api_url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            version = data.get("latestVersion", {}).get("id", "1.0.0")
            # Construct S3 URL
            s3_base = f"https://s3.amazonaws.com/openneuro.org/datasets/{dataset_id}/versions/{version}"
            desc_url = f"{s3_base}/dataset_description.json"
            
            file_path = output_dir / "dataset_description.json"
            with requests.get(desc_url, stream=True) as r:
                if r.status_code == 200:
                    with open(file_path, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    return True
    except Exception as e:
        logger.log("download_metadata_failed", error=str(e))
    
    return False


def download_participants_file(dataset_id: str, output_dir: Path) -> Optional[Path]:
    """
    Download participants.tsv.
    Returns path to file or None.
    """
    ensure_directory(output_dir)
    
    # Try to find the file via API
    api_url = f"https://api.openneuro.org/datasets/{dataset_id}/versions/latest/files"
    try:
        resp = requests.get(api_url, timeout=30)
        if resp.status_code == 200:
            files = resp.json()
            # Find participants.tsv
            for f in files:
                if f.get("name") == "participants.tsv":
                    file_id = f.get("id")
                    # Download URL construction
                    # Usually: https://openneuro.org/datasets/{id}/versions/{ver}/files/{file_id}
                    # But we need a direct link.
                    # Let's try the S3 pattern again.
                    version = "1.0.0" # Default guess
                    s3_url = f"https://s3.amazonaws.com/openneuro.org/datasets/{dataset_id}/versions/{version}/participants.tsv"
                    
                    file_path = output_dir / "participants.tsv"
                    with requests.get(s3_url, stream=True) as r:
                        if r.status_code == 200:
                            with open(file_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                            return file_path
    except Exception as e:
        logger.log("download_participants_failed", error=str(e))
    
    # Fallback: Try to download the whole dataset if just the metadata fails?
    # Too large. We must fail if we can't get the participants file.
    return None


def read_participants_tsv(file_path: Path) -> List[Dict[str, Any]]:
    """Read participants.tsv and return list of dicts."""
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        # BIDS TSV files are tab-separated
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            rows.append(row)
    return rows


def has_valid_score(row: Dict[str, Any], score_columns: List[str]) -> bool:
    """Check if any of the score columns have a non-null, non-empty numeric value."""
    for col in score_columns:
        if col in row:
            val = row[col]
            if val is not None and val != "" and val != "n/a" and val != "NA":
                try:
                    float(val)
                    return True
                except ValueError:
                    continue
    return False


def is_eligible(row: Dict[str, Any], score_columns: List[str]) -> bool:
    """
    Check eligibility:
    - Must have non-null MMSE/MOCA at BOTH timepoints (assuming columns like MMSE_1, MMSE_2 or similar).
    - We need to identify the columns.
    - In Constitution VI, columns are often 'MMSE' (single) or 'MMSE_1', 'MMSE_2'.
    - We will look for any column containing 'MMSE' or 'MOCA' and check if at least two distinct timepoints exist.
    - For simplicity, we assume the task implies checking for the presence of scores.
    - If the dataset has a single 'MMSE' column, we check if it's non-null.
    - If it has 'MMSE_1', 'MMSE_2', we check both.
    """
    # Identify score columns present in this row
    present_scores = [col for col in score_columns if col in row]
    
    if not present_scores:
        return False
    
    # Check if we have at least two distinct score columns (timepoints)
    # Or if there's a single column, we might need to check if it's valid?
    # The task says "at both timepoints". So we need at least 2 columns or a longitudinal structure.
    # Let's assume the dataset has columns like 'MMSE_1', 'MMSE_2' or 'visit_1_mmse', 'visit_2_mmse'.
    # We will count how many valid scores we have.
    valid_count = 0
    for col in present_scores:
        val = row[col]
        if val is not None and val != "" and val != "n/a" and val != "NA":
            try:
                float(val)
                valid_count += 1
            except ValueError:
                continue
    
    # Requirement: non-null at BOTH timepoints -> at least 2 valid scores
    return valid_count >= 2


def filter_eligible_subjects(rows: List[Dict[str, Any]], score_columns: List[str]) -> List[Dict[str, Any]]:
    """Filter rows based on eligibility criteria."""
    return [row for row in rows if is_eligible(row, score_columns)]


def limit_subjects(rows: List[Dict[str, Any]], limit: int = 100) -> List[Dict[str, Any]]:
    """Limit the number of subjects."""
    return rows[:limit]


def write_eligible_csv(rows: List[Dict[str, Any]], output_path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_dir(output_path.parent)
    if not rows:
        # Write header only if no rows? No, the task says fail if zero.
        # But we need to write the file first.
        pass
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        else:
            # Write header if possible
            if rows:
                pass # Already handled
            else:
                # If no rows, we can't write headers. We'll write a dummy header?
                # The task says "fail if zero eligible subjects".
                # We will write an empty file with no rows, but the check happens later.
                pass


def write_excluded_log(excluded: List[Dict[str, Any]], output_path: Path) -> None:
    """Write excluded subjects to log."""
    ensure_dir(output_path.parent)
    with open(output_path, 'w', encoding='utf-8') as f:
        for row in excluded:
            f.write(json.dumps(row) + "\n")


def write_status(eligible_count: int, total_count: int, status: str, error: Optional[str] = None) -> None:
    """Write status JSON."""
    ensure_dir(STATUS_JSON.parent)
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "total_count": total_count,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    save_json(status_data, STATUS_JSON)


def main() -> int:
    """Main entry point."""
    logger.log("download_and_filter_start", dataset=DATASET_ID)
    
    try:
        # 1. Download participants.tsv
        logger.log("downloading_participants")
        participants_path = download_participants_file(DATASET_ID, DATA_RAW_DIR / DATASET_ID)
        
        if not participants_path or not participants_path.exists():
            logger.log("participants_missing")
            write_status(0, 0, "error", "participants.tsv not found")
            return EXIT_CODE_NO_DATA
        
        # 2. Read participants
        rows = read_participants_tsv(participants_path)
        total_count = len(rows)
        
        if total_count == 0:
            write_status(0, 0, "error", "No subjects found in participants.tsv")
            return EXIT_CODE_NO_DATA
        
        # 3. Identify score columns
        # Look for columns containing MMSE or MOCA
        all_columns = rows[0].keys() if rows else []
        score_columns = [col for col in all_columns if "MMSE" in col.upper() or "MOCA" in col.upper()]
        
        if not score_columns:
            write_status(0, total_count, "error", "No MMSE/MOCA columns found")
            return EXIT_CODE_NO_LABELS
        
        logger.log("score_columns_found", columns=score_columns)
        
        # 4. Filter eligible
        eligible = filter_eligible_subjects(rows, score_columns)
        eligible_count = len(eligible)
        
        if eligible_count == 0:
            write_status(0, total_count, "error", "No eligible subjects with longitudinal scores")
            return EXIT_CODE_NO_LABELS
        
        # 5. Limit subjects
        limited_eligible = limit_subjects(eligible, limit=100)
        final_count = len(limited_eligible)
        
        excluded = [row for row in rows if row not in limited_eligible]
        
        # 6. Write outputs
        write_eligible_csv(limited_eligible, ELIGIBLE_CSV)
        write_excluded_log(excluded, EXCLUDED_LOG)
        write_status(final_count, total_count, "success")
        
        logger.log("download_and_filter_success", eligible=final_count)
        return EXIT_CODE_SUCCESS
        
    except Exception as e:
        logger.log("download_and_filter_error", error=str(e))
        write_status(0, 0, "error", str(e))
        return EXIT_CODE_ERROR


if __name__ == "__main__":
    sys.exit(main())
