"""
T017: Download and Filter Dataset (US1)

Downloads ds000246 from OpenNeuro, parses BIDS metadata, filters for subjects
with non-null MMSE/MOCA scores at both timepoints, limits to N=100, and outputs
eligible_subjects.csv and excluded_subjects.log.
"""
import os
import sys
import json
import time
import shutil
import tempfile
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple, Set
import requests
import pandas as pd
from tqdm import tqdm

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_config, ensure_dir
from utils.logger import get_logger
from utils.io import save_csv, save_dataframe

# Constants
DATASET_ID = "ds000246"
OPENNEURO_BASE = "https://api.openneuro.org"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_DOWNLOAD_FAILED = 1
MAX_SUBJECTS = 100
RANDOM_SEED = 42

def get_logger_wrapper(name: str) -> logging.Logger:
    """Wrapper to get a logger configured for this module."""
    return get_logger(name)

def check_dataset_availability(dataset_id: str) -> bool:
    """Check if the dataset exists on OpenNeuro."""
    logger = get_logger("01_download_and_filter")
    url = f"{OPENNEURO_BASE}/crn/datasets/{dataset_id}"
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"Dataset {dataset_id} is available on OpenNeuro.")
            return True
        else:
            logger.error(f"Dataset {dataset_id} not found (HTTP {response.status_code}).")
            return False
    except requests.RequestException as e:
        logger.error(f"Failed to check dataset availability: {e}")
        return False

def download_dataset(dataset_id: str, output_dir: Path, max_retries: int = 3) -> bool:
    """
    Download dataset from OpenNeuro.
    Note: In a real environment, we would use `datalad` or `openneuro-cli`.
    Here we simulate the download structure or fetch a manifest if possible.
    For the purpose of this pipeline running in CI/limited env, we will attempt
    to fetch the dataset description and participants file if available via API,
    or simulate the existence if the real download is blocked by size/auth.
    
    However, per strict "Real Data Only" constraints:
    We attempt to use the OpenNeuro API to fetch the 'participants.tsv' and 'dataset_description.json'.
    If the full NIfTI download is required but too large for the environment,
    we proceed with the metadata available to demonstrate the filtering logic.
    """
    logger = get_logger("01_download_and_filter")
    logger.info(f"Attempting to download metadata for {dataset_id}...")
    
    # Ensure output directory exists
    ensure_dir(output_dir)
    
    # Try to fetch participants.tsv via API (OpenNeuro provides this)
    # API endpoint for files: https://api.openneuro.org/crn/datasets/{dataset}/files
    # But simpler to try direct download of participants.tsv if hosted
    # OpenNeuro S3 structure: https://s3.amazonaws.com/openneuro.org/{dataset}/participants.tsv
    
    participants_url = f"https://openneuro.org/datasets/{dataset_id}/versions/1.0.0/files/participants.tsv"
    # Alternative: try the generic API for the file
    # We will try to fetch the JSON metadata first to confirm existence
    
    # Since direct large downloads might fail in restricted environments, 
    # we attempt a lightweight fetch of the metadata which is the critical part for filtering.
    # If the full dataset is needed, the user must run `datalad install` manually.
    # For this script to be runnable and produce outputs, we check for the metadata file.
    
    # Fallback: Try to fetch from the public S3 bucket structure if API is rate limited
    # Note: ds000246 is a real dataset.
    base_s3 = f"https://openneuro.s3.amazonaws.com/{dataset_id}/"
    
    # We will attempt to download the participants.tsv which is small
    # If this fails, we cannot filter.
    try:
        # OpenNeuro v3 API structure for files is complex. 
        # We will use a direct fetch of the TSV if possible, or simulate the data loading
        # from a cached version if the network is blocked.
        
        # Attempt 1: Direct URL (often works for TSV)
        # Constructing a likely URL for the TSV
        # OpenNeuro often hosts files at: https://openneuro.org/datasets/{id}/files
        # But for raw TSV, we might need to scrape or use the API.
        
        # Let's try the API to get the file list and download the specific file
        api_url = f"{OPENNEURO_BASE}/crn/datasets/{dataset_id}/snapshots/latest"
        resp = requests.get(api_url, timeout=30)
        if resp.status_code == 200:
            snapshot = resp.json()
            # We need the participants.tsv. It's usually in the root.
            # We will assume the environment has `datalad` or `openneuro-cli` installed 
            # for the full download, but for this script to run and produce the CSV,
            # we need the participants data.
            
            # Since we cannot guarantee a 50GB download in this script, 
            # we will check if the data directory already has the metadata.
            # If not, we try to fetch the TSV specifically.
            
            # Try to fetch participants.tsv directly from the dataset's public URL
            # ds000246 is Constitution VI.
            # We will try to download the TSV from the OpenNeuro S3 bucket directly.
            s3_tsv_url = f"https://openneuro.s3.amazonaws.com/{dataset_id}/participants.tsv"
            tsv_resp = requests.get(s3_tsv_url, timeout=30)
            
            if tsv_resp.status_code == 200:
                participants_file = output_dir / "participants.tsv"
                with open(participants_file, 'wb') as f:
                    f.write(tsv_resp.content)
                logger.info(f"Downloaded participants.tsv to {participants_file}")
                return True
            else:
                logger.warning(f"Could not fetch participants.tsv from S3 (HTTP {tsv_resp.status_code}).")
        else:
            logger.warning(f"Could not fetch dataset snapshot (HTTP {resp.status_code}).")
    except Exception as e:
        logger.warning(f"Failed to download metadata automatically: {e}")
    
    # If we are here, we couldn't download. 
    # CRITICAL: The task requires REAL data. If we cannot download, we must fail.
    # However, if the file exists locally (from a previous run or manual setup), use it.
    participants_file = output_dir / "participants.tsv"
    if participants_file.exists():
        logger.info(f"Using existing participants.tsv at {participants_file}")
        return True
    
    logger.error("Failed to download dataset metadata and no local copy found.")
    return False

def parse_bids_metadata(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse BIDS metadata to extract subject IDs and cognitive scores (MMSE/MOCA).
    Returns a list of dictionaries with subject info.
    """
    logger = get_logger("01_download_and_filter")
    subjects_data = []
    
    participants_file = data_dir / "participants.tsv"
    if not participants_file.exists():
        logger.error(f"participants.tsv not found in {data_dir}")
        return subjects_data
    
    try:
        df = pd.read_csv(participants_file, sep='\t')
        logger.info(f"Loaded participants.tsv with {len(df)} rows. Columns: {list(df.columns)}")
        
        # Identify columns for MMSE/MOCA and Timepoints
        # Common patterns: 'MMSE', 'MOCA', 'timepoint', 'visit'
        # We look for columns containing 'MMSE' or 'MOCA'
        score_cols = [col for col in df.columns if 'MMSE' in col.upper() or 'MOCA' in col.upper()]
        timepoint_cols = [col for col in df.columns if 'time' in col.lower() or 'visit' in col.lower() or 'wave' in col.lower()]
        
        if not score_cols:
            logger.warning("No MMSE or MOCA columns found in participants.tsv.")
            # Fallback: maybe they are in JSON sidecars? For now, assume TSV is the source.
            return subjects_data
        
        # We need to handle longitudinal data. 
        # The TSV might have one row per subject with multiple timepoints, 
        # or one row per subject-timepoint.
        # We assume one row per subject-timepoint for simplicity if 'timepoint' exists.
        
        # If the data is wide (one row per subject, multiple columns for timepoints),
        # we need to melt it.
        
        # Strategy: 
        # 1. Check if 'session' or 'timepoint' column exists.
        # 2. If so, each row is a timepoint.
        # 3. If not, we might have to parse column names like 'MMSE_t1', 'MMSE_t2'.
        
        session_col = None
        if 'session' in df.columns:
            session_col = 'session'
        elif 'timepoint' in df.columns:
            session_col = 'timepoint'
        elif 'visit' in df.columns:
            session_col = 'visit'
        
        if session_col:
            # Long format: one row per subject-session
            for _, row in df.iterrows():
                subject_id = row.get('participant_id', row.get('subject_id', 'unknown'))
                # Find score for this row
                score_val = None
                score_col_used = None
                for col in score_cols:
                    if not pd.isna(row[col]):
                        score_val = row[col]
                        score_col_used = col
                        break
                
                if score_val is not None:
                    subjects_data.append({
                        'subject_id': str(subject_id),
                        'timepoint': row[session_col],
                        'score': score_val,
                        'score_col': score_col_used
                    })
        else:
            # Wide format: one row per subject, columns like MMSE_1, MMSE_2
            # We try to detect patterns
            time_markers = ['_1', '_2', '_t1', '_t2', '_baseline', '_followup']
            # Simple heuristic: look for score columns with suffixes
            score_by_time = {}
            for col in score_cols:
                # Try to extract time marker
                for marker in time_markers:
                    if col.endswith(marker):
                        time_label = marker.strip('_')
                        if time_label not in score_by_time:
                            score_by_time[time_label] = []
                        score_by_time[time_label].append(col)
                        break
                
                # If no marker, assume baseline
                if col not in [c for sublist in score_by_time.values() for c in sublist]:
                     if 'baseline' not in score_by_time:
                         score_by_time['baseline'] = []
                     score_by_time['baseline'].append(col)

            for _, row in df.iterrows():
                subject_id = row.get('participant_id', row.get('subject_id', 'unknown'))
                for time_label, cols in score_by_time.items():
                    for col in cols:
                        val = row.get(col)
                        if not pd.isna(val):
                            subjects_data.append({
                                'subject_id': str(subject_id),
                                'timepoint': time_label,
                                'score': val,
                                'score_col': col
                            })
                            break # Take first valid score for this timepoint
    
    except Exception as e:
        logger.error(f"Error parsing participants.tsv: {e}")
    
    return subjects_data

def filter_eligible_subjects(subjects_data: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
    """
    Filter for subjects with non-null MMSE/MOCA at BOTH timepoints.
    Returns (eligible_subject_ids, excluded_subject_ids).
    """
    logger = get_logger("01_download_and_filter")
    
    # Group by subject
    subject_scores = {}
    for entry in subjects_data:
        sid = entry['subject_id']
        if sid not in subject_scores:
            subject_scores[sid] = {}
        # Use timepoint as key, store score
        tp = entry['timepoint']
        if tp not in subject_scores[sid]:
            subject_scores[sid][tp] = []
        subject_scores[sid][tp].append(entry['score'])
    
    eligible = []
    excluded = []
    
    for sid, timepoints in subject_scores.items():
        # Check if at least 2 timepoints have data
        valid_timepoints = [tp for tp, scores in timepoints.items() if len(scores) > 0]
        
        if len(valid_timepoints) >= 2:
            eligible.append(sid)
        else:
            excluded.append(sid)
            logger.debug(f"Excluded {sid}: Only {len(valid_timepoints)} timepoints with scores.")
    
    logger.info(f"Found {len(eligible)} eligible subjects (>=2 timepoints).")
    logger.info(f"Excluded {len(excluded)} subjects.")
    
    return eligible, excluded

def write_outputs(eligible: List[str], excluded: List[str], output_dir: Path):
    """
    Write eligible_subjects.csv and excluded_subjects.log.
    """
    logger = get_logger("01_download_and_filter")
    ensure_dir(output_dir)
    
    # Write eligible_subjects.csv
    eligible_file = output_dir / "eligible_subjects.csv"
    df_eligible = pd.DataFrame({'subject_id': eligible})
    save_dataframe(df_eligible, eligible_file)
    logger.info(f"Wrote {len(eligible)} eligible subjects to {eligible_file}")
    
    # Write excluded_subjects.log
    excluded_file = output_dir / "excluded_subjects.log"
    with open(excluded_file, 'w') as f:
        f.write("# Excluded Subjects Log\n")
        f.write("# Reason: Missing MMSE/MOCA scores at one or both timepoints\n")
        for sid in excluded:
            f.write(f"{sid}\n")
    logger.info(f"Wrote {len(excluded)} excluded subjects to {excluded_file}")

def main():
    logger = get_logger("01_download_and_filter")
    logger.info("Starting T017: Download and Filter")
    
    config = get_config()
    random.seed(config.get('random_seed', 42))
    
    # 1. Check availability
    if not check_dataset_availability(DATASET_ID):
        logger.error("Dataset not available. Exiting.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 2. Download
    if not download_dataset(DATASET_ID, DATA_RAW_DIR):
        logger.error("Download failed. Exiting.")
        sys.exit(EXIT_CODE_DOWNLOAD_FAILED)
    
    # 3. Parse Metadata
    subjects_data = parse_bids_metadata(DATA_RAW_DIR)
    if not subjects_data:
        logger.error("No subject data found in metadata.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 4. Filter
    eligible, excluded = filter_eligible_subjects(subjects_data)
    
    if len(eligible) == 0:
        logger.error("No eligible subjects found (need >=2 timepoints).")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 5. Limit to N
    if len(eligible) > MAX_SUBJECTS:
        # Shuffle and take first N
        import random
        random.shuffle(eligible)
        eligible = eligible[:MAX_SUBJECTS]
        logger.info(f"Limited to {MAX_SUBJECTS} subjects.")
    
    # 6. Write Outputs
    write_outputs(eligible, excluded, DATA_PROCESSED_DIR)
    
    logger.info("T017 completed successfully.")
    sys.exit(EXIT_CODE_SUCCESS)

if __name__ == "__main__":
    main()