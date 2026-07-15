"""
T017: Download ds000246, parse BIDS metadata, filter for longitudinal scores,
and output eligible subjects.

Outputs:
  - data/processed/eligible_subjects.csv
  - data/processed/excluded_subjects.log
  - data/artifacts/data_gate_status.json
  - data/raw/ds000246/participants.tsv (raw source)
"""
from __future__ import annotations

import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import pandas as pd
from utils.logger import get_logger, log_operation
from utils.io import save_json, ensure_dir

# Constants
DATASET_ID = "ds000246"
OPENNEURO_API = "https://api.openneuro.org"
PARTICIPANTS_FILE = "participants.tsv"
MAX_SUBJECTS = 100
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_ERROR = 1

logger = get_logger("download_and_filter")

def ensure_directory(path: Path) -> None:
    """Ensure directory exists."""
    ensure_dir(path)

def download_dataset_metadata(dataset_id: str) -> Dict[str, Any]:
    """Download dataset metadata from OpenNeuro."""
    url = f"{OPENNEURO_API}/datasets/{dataset_id}"
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise RuntimeError(f"Failed to fetch dataset metadata: {e}")

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

    ensure_directory(output_path.parent)
    
    try:
        response = requests.get(file_url, timeout=60)
        response.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(response.content)
        return output_path
    except Exception as e:
        raise RuntimeError(f"Failed to download participants.tsv: {e}")

def read_participants_tsv(file_path: Path) -> pd.DataFrame:
    """Read participants.tsv into a DataFrame."""
    if not file_path.exists():
        raise FileNotFoundError(f"Participants file not found: {file_path}")
    return pd.read_csv(file_path, sep='\t')

def has_valid_score(row: pd.Series, score_col: str) -> bool:
    """Check if a score column has a valid non-null numeric value."""
    if score_col not in row.index:
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
    
    Column naming convention in ds000246:
    - MMSE at time 1: 'MMSE' or 'MMSE_1'
    - MMSE at time 2: 'MMSE_2'
    - MOCA at time 1: 'MOCA' or 'MOCA_1'
    - MOCA at time 2: 'MOCA_2'
    
    We check for presence of any valid score at both timepoints.
    """
    # Define possible column names for each timepoint
    t1_cols = ['MMSE', 'MMSE_1', 'MOCA', 'MOCA_1']
    t2_cols = ['MMSE_2', 'MOCA_2']
    
    # Check for at least one valid score at time 1
    t1_valid = any(has_valid_score(row, col) for col in t1_cols if col in row.index)
    
    # Check for at least one valid score at time 2
    t2_valid = any(has_valid_score(row, col) for col in t2_cols if col in row.index)
    
    return t1_valid and t2_valid

def filter_eligible_subjects(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Filter dataframe for eligible subjects."""
    eligible = []
    excluded = []
    
    for _, row in df.iterrows():
        subject_id = row.get('participant_id', row.get('subject_id', 'unknown'))
        if is_eligible(row):
            # Extract scores for the record
            scores = {}
            for col in df.columns:
                if col.startswith(('MMSE', 'MOCA')) and not pd.isna(row[col]):
                    scores[col] = float(row[col])
            eligible.append({
                'subject_id': subject_id,
                'scores': scores,
                'row_data': row.to_dict()
            })
        else:
            excluded.append({
                'subject_id': subject_id,
                'reason': 'Missing longitudinal scores (MMSE/MOCA at both timepoints)'
            })
    
    return eligible, excluded

def limit_subjects(eligible: List[Dict], n: int) -> List[Dict]:
    """Limit to n subjects."""
    return eligible[:n]

def write_eligible_csv(eligible: List[Dict], output_path: Path) -> None:
    """Write eligible subjects to CSV."""
    ensure_directory(output_path.parent)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        # Header
        writer.writerow(['subject_id', 'mmse_baseline', 'mmse_followup', 'moca_baseline', 'moca_followup'])
        
        for entry in eligible:
            row_data = entry['row_data']
            # Try to extract specific scores
            mmse_1 = row_data.get('MMSE', row_data.get('MMSE_1', ''))
            mmse_2 = row_data.get('MMSE_2', '')
            moca_1 = row_data.get('MOCA', row_data.get('MOCA_1', ''))
            moca_2 = row_data.get('MOCA_2', '')
            
            # Clean values
            mmse_1 = '' if pd.isna(mmse_1) else mmse_1
            mmse_2 = '' if pd.isna(mmse_2) else mmse_2
            moca_1 = '' if pd.isna(moca_1) else moca_1
            moca_2 = '' if pd.isna(moca_2) else moca_2
            
            writer.writerow([
                entry['subject_id'],
                mmse_1,
                mmse_2,
                moca_1,
                moca_2
            ])

def write_excluded_log(excluded: List[Dict], output_path: Path) -> None:
    """Write excluded subjects to log file."""
    ensure_directory(output_path.parent)
    with open(output_path, 'w') as f:
        f.write("# Excluded Subjects Log\n")
        f.write(f"# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Reason: Missing longitudinal scores (MMSE/MOCA at both timepoints)\n\n")
        
        for entry in excluded:
            f.write(f"{entry['subject_id']}: {entry['reason']}\n")

def write_status(eligible_count: int, total_count: int, status: str, error: Optional[str] = None) -> None:
    """Write status JSON to artifacts."""
    status_data = {
        "status": status,
        "error": error,
        "eligible_count": eligible_count,
        "total_count": total_count,
        "timestamp": time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    output_path = Path("data/artifacts/data_gate_status.json")
    ensure_dir(output_path.parent)
    save_json(status_data, output_path)

@log_operation("download_and_filter_main")
def main() -> int:
    """Main entry point."""
    try:
        logger.info("Starting download and filter process")
        
        # Paths
        raw_dir = Path("data/raw") / DATASET_ID
        processed_dir = Path("data/processed")
        participants_path = raw_dir / PARTICIPANTS_FILE
        eligible_path = processed_dir / "eligible_subjects.csv"
        excluded_path = processed_dir / "excluded_subjects.log"
        
        # Step 1: Download metadata
        logger.info(f"Fetching metadata for {DATASET_ID}")
        metadata = download_dataset_metadata(DATASET_ID)
        logger.info(f"Dataset found: {metadata.get('id', 'unknown')}")
        
        # Step 2: Download participants.tsv
        logger.info("Downloading participants.tsv")
        download_participants_file(DATASET_ID, participants_path)
        
        # Step 3: Read and parse
        logger.info("Reading participants.tsv")
        df = read_participants_tsv(participants_path)
        total_subjects = len(df)
        logger.info(f"Found {total_subjects} subjects")
        
        # Step 4: Filter eligible
        logger.info("Filtering for eligible subjects")
        eligible, excluded = filter_eligible_subjects(df)
        eligible_count = len(eligible)
        
        if eligible_count == 0:
            logger.error("No eligible subjects found")
            write_status(0, total_subjects, "error", "No eligible subjects found")
            return EXIT_CODE_NO_LABELS
        
        # Step 5: Limit
        final_eligible = limit_subjects(eligible, MAX_SUBJECTS)
        final_count = len(final_eligible)
        logger.info(f"Selected {final_count} subjects (limit: {MAX_SUBJECTS})")
        
        # Step 6: Write outputs
        logger.info(f"Writing eligible subjects to {eligible_path}")
        write_eligible_csv(final_eligible, eligible_path)
        
        logger.info(f"Writing excluded log to {excluded_path}")
        write_excluded_log(excluded, excluded_path)
        
        # Step 7: Write status
        write_status(final_count, total_subjects, "success")
        
        logger.info("Process completed successfully")
        return EXIT_CODE_SUCCESS
        
    except Exception as e:
        logger.error(f"Process failed: {e}")
        write_status(0, 0, "error", str(e))
        return EXIT_CODE_ERROR

if __name__ == "__main__":
    sys.exit(main())
