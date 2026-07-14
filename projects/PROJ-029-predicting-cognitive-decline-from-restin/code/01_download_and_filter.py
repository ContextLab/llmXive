"""
T017: Download and Filter Dataset (ds000246)

1. Attempts to download ds000246 from OpenNeuro (or verify local existence).
2. Parses BIDS metadata (participants.json, sub-*/ses-*/dwi/*.json, etc.)
3. Filters for subjects with non-null MMSE or MOCA at BOTH timepoints.
4. Limits to N = min(100, available_eligible).
5. Outputs:
   - data/processed/eligible_subjects.csv
   - data/processed/excluded_subjects.log
"""
import os
import sys
import json
import time
import shutil
import tempfile
import logging
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from utils.logger import get_logger
from utils.io import ensure_dir, load_json, save_csv
from config import get_config

# Constants
DATASET_ID = "ds000246"
OPENNEURO_API_URL = f"https://api.openneuro.org/datasets/{DATASET_ID}"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_SUCCESS = 0
EXIT_CODE_ERROR = 1

def get_logger_wrapper(name: str) -> logging.Logger:
    """Wrapper to get a logger with the correct formatting."""
    return get_logger(name)

def check_dataset_availability(dataset_id: str) -> bool:
    """Check if dataset metadata exists on OpenNeuro."""
    logger = logging.getLogger("01_download_and_filter")
    try:
        response = requests.get(f"https://api.openneuro.org/datasets/{dataset_id}", timeout=10)
        return response.status_code == 200
    except Exception as e:
        logger.warning(f"Could not reach OpenNeuro API: {e}")
        return False

def download_dataset(dataset_id: str, target_dir: Path, logger: logging.Logger) -> bool:
    """
    Attempt to download dataset using openneuro CLI if available, 
    or fallback to manual download if possible (simplified for this task).
    Note: Full rs-fMRI download is large. We check for existence first.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = target_dir / dataset_id
    
    if dataset_path.exists() and (dataset_path / "dataset_description.json").exists():
        logger.info(f"Dataset {dataset_id} already exists locally at {dataset_path}")
        return True
    
    logger.warning(f"openneuro CLI not found. Attempting to verify remote availability...")
    if not check_dataset_availability(dataset_id):
        logger.error(f"Dataset {dataset_id} not available on OpenNeuro.")
        return False
    
    # In a real CI environment without CLI, we might need to download specific files.
    # For this implementation, we assume the data gate (T004c) verified availability.
    # If the directory doesn't exist, we cannot proceed without the CLI.
    logger.error(f"Dataset directory not found and openneuro CLI is missing.")
    logger.error("Please run: pip install openneuro-cli && openneuro download --dataset ds000246 data/raw/")
    return False

def parse_bids_metadata(dataset_path: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Parse participants.json and subject-specific session files to extract
    MMSE and MOCA scores for longitudinal analysis.
    """
    subjects_data = []
    
    # Check for participants.json (standard BIDS)
    participants_file = dataset_path / "participants.tsv"
    participants_json_file = dataset_path / "participants.json"
    
    if not participants_file.exists():
        logger.warning("participants.tsv not found. Cannot parse subject metadata.")
        return []
    
    # Load TSV
    try:
        df = pd.read_csv(participants_file, sep='\t')
    except Exception as e:
        logger.error(f"Failed to read participants.tsv: {e}")
        return []
    
    # Identify columns for MMSE, MOCA, and Session
    # Common BIDS extensions might be 'MMSE', 'MOCA', 'score', 'timepoint', 'session'
    # We look for columns containing these keywords (case-insensitive)
    mmse_cols = [c for c in df.columns if 'mmse' in c.lower()]
    moca_cols = [c for c in df.columns if 'moca' in c.lower()]
    session_cols = [c for c in df.columns if 'session' in c.lower() or 'timepoint' in c.lower()]
    
    if not mmse_cols and not moca_cols:
        logger.warning("No MMSE or MOCA columns found in participants.tsv.")
        # Check if scores are in separate JSON files per subject (less common for longitudinal in one file)
        # For ds000246, scores are often in participants.tsv or separate JSONs.
        # We assume standard TSV for now.
    
    # We need to identify subjects with scores at TWO timepoints.
    # If the TSV is long (one row per session), we group by subject.
    # If the TSV is wide (one row per subject with session1/ses2 columns), we handle differently.
    
    # Strategy: Assume long format (one row per subject-session) is common, 
    # but ds000246 might be wide. Let's check unique row counts.
    unique_subjects = df['participant_id'].nunique() if 'participant_id' in df.columns else df.shape[0]
    total_rows = df.shape[0]
    
    if unique_subjects == total_rows:
        # Likely wide format: one row per subject, multiple columns for sessions
        # e.g., sub-01, MMSE_t1, MMSE_t2, MOCA_t1, MOCA_t2
        logger.info("Detected wide format (one row per subject).")
        for _, row in df.iterrows():
            sub_id = row['participant_id'] if 'participant_id' in row else row.index
            scores_t1 = {}
            scores_t2 = {}
            
            # Heuristic: look for columns ending in _t1, _t2 or similar
            for col in df.columns:
                if 'mmse' in col.lower():
                    if '_t1' in col.lower() or 'baseline' in col.lower():
                        scores_t1['mmse'] = row[col]
                    elif '_t2' in col.lower() or 'followup' in col.lower():
                        scores_t2['mmse'] = row[col]
                    else:
                        # If only one MMSE column exists, assume it's both? No, we need two.
                        pass
                if 'moca' in col.lower():
                    if '_t1' in col.lower() or 'baseline' in col.lower():
                        scores_t1['moca'] = row[col]
                    elif '_t2' in col.lower() or 'followup' in col.lower():
                        scores_t2['moca'] = row[col]
            
            subjects_data.append({
                'subject_id': sub_id,
                'scores_t1': scores_t1,
                'scores_t2': scores_t2
            })
    else:
        # Likely long format: one row per session
        logger.info("Detected long format (one row per session).")
        # Group by participant_id
        grouped = df.groupby('participant_id')
        for sub_id, group in grouped:
            scores_t1 = {}
            scores_t2 = {}
            
            # Assume first two rows are t1 and t2 (or sort by session)
            sessions = group['session_id'].unique() if 'session_id' in group.columns else group.index
            # Sort sessions if possible
            if len(sessions) >= 2:
                # Try to infer order
                sorted_group = group.sort_values(by='session_id') if 'session_id' in group.columns else group
                row1 = sorted_group.iloc[0]
                row2 = sorted_group.iloc[1]
                
                for col in df.columns:
                    if 'mmse' in col.lower():
                        scores_t1['mmse'] = row1[col]
                        scores_t2['mmse'] = row2[col]
                    if 'moca' in col.lower():
                        scores_t1['moca'] = row1[col]
                        scores_t2['moca'] = row2[col]
                
                subjects_data.append({
                    'subject_id': sub_id,
                    'scores_t1': scores_t1,
                    'scores_t2': scores_t2
                })
            elif len(sessions) == 1:
                # Only one timepoint
                row = group.iloc[0]
                for col in df.columns:
                    if 'mmse' in col.lower():
                        scores_t1['mmse'] = row[col]
                    if 'moca' in col.lower():
                        scores_t1['moca'] = row[col]
                subjects_data.append({
                    'subject_id': sub_id,
                    'scores_t1': scores_t1,
                    'scores_t2': {}
                })
    
    return subjects_data

def filter_eligible_subjects(subjects_data: List[Dict[str, Any]], logger: logging.Logger) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter for subjects with non-null MMSE or MOCA at BOTH timepoints.
    Returns (eligible, excluded).
    """
    eligible = []
    excluded = []
    
    for sub in subjects_data:
        t1 = sub['scores_t1']
        t2 = sub['scores_t2']
        
        # Check if we have at least one valid score at t1 and one at t2
        t1_valid = (t1.get('mmse') is not None and not pd.isna(t1.get('mmse'))) or \
                   (t1.get('moca') is not None and not pd.isna(t1.get('moca')))
        t2_valid = (t2.get('mmse') is not None and not pd.isna(t2.get('mmse'))) or \
                   (t2.get('moca') is not None and not pd.isna(t2.get('moca')))
        
        if t1_valid and t2_valid:
            eligible.append(sub)
        else:
            reason = []
            if not t1_valid: reason.append("Missing score at t1")
            if not t2_valid: reason.append("Missing score at t2")
            excluded.append({
                'subject_id': sub['subject_id'],
                'reason': "; ".join(reason)
            })
    
    logger.info(f"Found {len(eligible)} eligible subjects and {len(excluded)} excluded subjects.")
    return eligible, excluded

def write_outputs(eligible: List[Dict[str, Any]], excluded: List[Dict[str, Any]], logger: logging.Logger):
    """
    Write eligible_subjects.csv and excluded_subjects.log.
    Limit eligible to N=100.
    """
    ensure_dir(DATA_PROCESSED_DIR)
    
    # Limit to N=100
    N_MAX = 100
    if len(eligible) > N_MAX:
        logger.warning(f"Eligible subjects ({len(eligible)}) exceed limit ({N_MAX}). Truncating.")
        eligible = eligible[:N_MAX]
    
    # Write eligible CSV
    eligible_file = DATA_PROCESSED_DIR / "eligible_subjects.csv"
    # Flatten data for CSV
    rows = []
    for sub in eligible:
        row = {
            'subject_id': sub['subject_id'],
            't1_mmse': sub['scores_t1'].get('mmse'),
            't1_moca': sub['scores_t1'].get('moca'),
            't2_mmse': sub['scores_t2'].get('mmse'),
            't2_moca': sub['scores_t2'].get('moca')
        }
        rows.append(row)
    
    df_eligible = pd.DataFrame(rows)
    save_csv(df_eligible, eligible_file)
    logger.info(f"Wrote {len(eligible)} eligible subjects to {eligible_file}")
    
    # Write excluded log
    excluded_file = DATA_PROCESSED_DIR / "excluded_subjects.log"
    with open(excluded_file, 'w') as f:
        f.write("Excluded Subjects Report\n")
        f.write("========================\n\n")
        for item in excluded:
            f.write(f"Subject: {item['subject_id']} | Reason: {item['reason']}\n")
    logger.info(f"Wrote {len(excluded)} excluded subjects to {excluded_file}")

def main():
    logger = get_logger_wrapper("01_download_and_filter")
    logger.info("Starting T017: Download and Filter")
    
    # 1. Check/Download
    if not download_dataset(DATASET_ID, DATA_RAW_DIR, logger):
        logger.error(f"Dataset {DATASET_ID} not available and could not be downloaded.")
        logger.error("Please ensure the dataset is available in data/raw/ds000246 or network is accessible.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    dataset_path = DATA_RAW_DIR / DATASET_ID
    
    # 2. Parse Metadata
    subjects_data = parse_bids_metadata(dataset_path, logger)
    if not subjects_data:
        logger.error("No subject data found in BIDS metadata.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 3. Filter
    eligible, excluded = filter_eligible_subjects(subjects_data, logger)
    
    if not eligible:
        logger.error("No eligible subjects found with longitudinal scores.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 4. Write Outputs
    write_outputs(eligible, excluded, logger)
    
    logger.info("T017 completed successfully.")
    sys.exit(EXIT_CODE_SUCCESS)

if __name__ == "__main__":
    main()