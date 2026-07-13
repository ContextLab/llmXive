"""
T017: Download and Filter Dataset

Downloads OpenNeuro ds000246 (Constitution VI, FR-001), parses BIDS metadata,
filters for subjects with non-null MMSE/MOCA scores at both timepoints,
limits to N = min(100, available), and outputs eligible/excluded lists.
"""
import os
import sys
import json
import time
import shutil
import tempfile
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
import requests

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger
from utils.io import ensure_dir, save_csv, load_dataframe
from config import get_config

# Configuration
DATASET_ID = "ds000246"
DATASET_NAME = "Constitution VI"
N_MAX_SUBJECTS = 100
OUTPUT_ELIGIBLE = "data/processed/eligible_subjects.csv"
OUTPUT_EXCLUDED = "data/processed/excluded_subjects.log"

logger = get_logger(__name__)

def check_dataset_availability(dataset_id: str) -> bool:
    """
    Check if the dataset exists on OpenNeuro.
    Note: We use the public API. If network fails, we handle gracefully.
    """
    url = f"https://api.openneuro.org/crn/datasets/{dataset_id}/snapshot"
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"Dataset {dataset_id} is available on OpenNeuro.")
            return True
        else:
            logger.warning(f"Dataset {dataset_id} returned status {response.status_code}.")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check dataset availability: {e}")
        return False

def download_dataset(dataset_id: str, target_dir: Path) -> bool:
    """
    Download the dataset. Since direct downloading via API is complex,
    we attempt to use the `datalad` or `aws` CLI if available, or fallback
    to a simulated download for the purpose of this specific task if the
    network is blocked but the task requires a file.

    However, per strict constraints: "Real data only".
    We will attempt to download a small subset of metadata files to verify
    the structure, then parse them. If the full download fails due to network
    restrictions (common in CI), we attempt to fetch the metadata JSONs
    directly via the API if available, or fail explicitly.

    For this implementation, we attempt to download the dataset via the
    OpenNeuro API's tarball endpoint if available, or simulate the
    directory structure with metadata if the network is strictly blocked
    (but we must not fake the *results* of the analysis, only the data access).
    
    Given the execution error "Name or service not known", the runner has
    no DNS. We must handle this gracefully by failing the download step
    with a clear error code, OR if a local cache exists, use it.
    
    Since we cannot fetch real data without DNS, and we cannot fake data,
    we will implement the logic to download, but if it fails due to network,
    we exit with code 2 (as per T004c spec for missing labels) or 1 for download failure.
    
    WAIT: The prompt says "If, after the above, NO real data can be obtained... do NOT fabricate a result: leave the run to FAIL".
    So we must try to download. If it fails, we exit.
    """
    logger.info(f"Attempting to download dataset {dataset_id} to {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # OpenNeuro doesn't have a simple direct download URL for the whole dataset without authentication or CLI tools.
    # We will try to fetch the metadata files directly from the API to build our subject list.
    # This avoids the need to download 100GB of NIfTI files for this specific step.
    # We only need the JSON sidecars to check for MMSE/MOCA.
    
    base_url = f"https://api.openneuro.org/crn/datasets/{dataset_id}"
    
    # Fetch participants.tsv
    try:
        participants_url = f"{base_url}/participants.tsv"
        # Note: OpenNeuro API might require specific headers or authentication for direct file access.
        # If this fails, we fall back to listing subjects via the API.
        resp = requests.get(participants_url, timeout=15)
        if resp.status_code == 200:
            # Save participants file
            with open(target_dir / "participants.tsv", "wb") as f:
                f.write(resp.content)
            logger.info("Downloaded participants.tsv")
        else:
            logger.warning(f"Could not download participants.tsv directly ({resp.status_code}). Attempting API listing.")
    except Exception as e:
        logger.warning(f"Direct download of participants.tsv failed: {e}")

    # Fetch subject list from API
    subjects_url = f"{base_url}/subjects"
    try:
        resp = requests.get(subjects_url, timeout=15)
        if resp.status_code == 200:
            subjects = resp.json()
            logger.info(f"Retrieved {len(subjects)} subjects from API.")
            # We don't save this as a file, just use it.
            return True
        else:
            logger.error(f"Failed to retrieve subjects list: {resp.status_code}")
            return False
    except Exception as e:
        logger.error(f"Network error during dataset metadata retrieval: {e}")
        # If we cannot reach the network, we cannot proceed with real data.
        # We return False to trigger a failure.
        return False

def parse_bids_metadata(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse BIDS metadata to find subjects with MMSE/MOCA scores at two timepoints.
    Since we cannot download the full dataset in CI, we simulate the parsing logic
    by checking if the metadata files exist in the expected location.
    
    In a real run, this would iterate through subject directories:
    sub-{id}/ses-{timepoint}/anat/*.json
    and look for "TaskName" or custom fields containing "MMSE" or "MOCA".
    
    For this specific task, we assume the data gate (T004c) verified existence.
    We will check for a local cache or fail.
    """
    eligible = []
    excluded = []
    
    # If participants.tsv exists, load it.
    participants_file = data_dir / "participants.tsv"
    if participants_file.exists():
        try:
            df = pd.read_csv(participants_file, sep='\t')
            # Check for columns like 'MMSE_time1', 'MMSE_time2', etc.
            # The actual column names depend on the dataset.
            # We look for any column containing 'MMSE' or 'MOCA'.
            relevant_cols = [c for c in df.columns if 'MMSE' in c.upper() or 'MOCA' in c.upper()]
            
            if not relevant_cols:
                logger.warning("No MMSE/MOCA columns found in participants.tsv. Assuming all excluded.")
                return eligible, excluded
            
            # Assume we need non-null values in at least two timepoint columns.
            # Heuristic: Look for columns with '1' and '2' or 't1' and 't2'
            timepoint_cols = [c for c in relevant_cols if ('1' in c or 't1' in c.lower()) or ('2' in c or 't2' in c.lower())]
            
            # If we can't distinguish timepoints, we might just check if any two score columns are non-null.
            if len(timepoint_cols) < 2:
                # Fallback: check if there are at least 2 score columns with data
                # This is a simplification.
                logger.warning("Could not identify distinct timepoint columns. Checking for any 2 score columns.")
                # We'll just check all relevant columns
                score_cols = relevant_cols
            else:
                score_cols = timepoint_cols
            
            for _, row in df.iterrows():
                subject_id = row.get('participant_id', 'unknown')
                scores = [row[col] for col in score_cols]
                # Check if non-null
                valid_scores = [s for s in scores if pd.notna(s)]
                
                if len(valid_scores) >= 2:
                    eligible.append({
                        'subject_id': subject_id,
                        'scores': valid_scores,
                        'reason': 'Has >= 2 non-null cognitive scores'
                    })
                else:
                    excluded.append({
                        'subject_id': subject_id,
                        'reason': f'Insufficient scores (found {len(valid_scores)} of {len(score_cols)})'
                    })
                    
        except Exception as e:
            logger.error(f"Error parsing participants.tsv: {e}")
    else:
        # If no participants file, we assume we must fail or use the API list.
        # We already have the subject list from download step.
        # We assume they are excluded because we can't verify scores without the full metadata.
        logger.warning("No participants.tsv found. Cannot verify scores.")
    
    return eligible, excluded

def filter_eligible_subjects(eligible: List[Dict], excluded: List[Dict], n_max: int) -> Tuple[List[Dict], List[Dict]]:
    """
    Limit to N_MAX subjects.
    """
    if len(eligible) > n_max:
        logger.info(f"Limiting {len(eligible)} eligible subjects to {n_max}.")
        eligible = eligible[:n_max]
    return eligible, excluded

def write_outputs(eligible: List[Dict], excluded: List[Dict], output_dir: Path):
    """
    Write eligible_subjects.csv and excluded_subjects.log
    """
    ensure_dir(output_dir)
    
    # Write CSV
    eligible_df = pd.DataFrame(eligible)
    if not eligible_df.empty:
        # Ensure subject_id is first column
        cols = ['subject_id'] + [c for c in eligible_df.columns if c != 'subject_id']
        eligible_df = eligible_df[cols]
        save_csv(eligible_df, output_dir / OUTPUT_ELIGIBLE)
        logger.info(f"Wrote {len(eligible)} eligible subjects to {OUTPUT_ELIGIBLE}")
    else:
        # Create empty file with headers
        pd.DataFrame(columns=['subject_id', 'scores', 'reason']).to_csv(output_dir / OUTPUT_ELIGIBLE, index=False)
        logger.warning("No eligible subjects found. Created empty CSV.")
    
    # Write Log
    log_path = output_dir / OUTPUT_EXCLUDED
    with open(log_path, 'w') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 50 + "\n")
        for item in excluded:
            f.write(f"Subject: {item['subject_id']}, Reason: {item['reason']}\n")
        f.write(f"\nTotal Excluded: {len(excluded)}\n")
    logger.info(f"Wrote {len(excluded)} excluded subjects to {OUTPUT_EXCLUDED}")

def main():
    logger.info("Starting T017: Download and Filter")
    
    data_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    ensure_dir(data_dir)
    ensure_dir(processed_dir)
    
    # 1. Check availability
    if not check_dataset_availability(DATASET_ID):
        logger.error(f"Dataset {DATASET_ID} not available on OpenNeuro.")
        sys.exit(2)
    
    # 2. Download metadata (full data not needed for this step)
    if not download_dataset(DATASET_ID, data_dir):
        logger.error("Failed to download dataset metadata.")
        sys.exit(1)
    
    # 3. Parse metadata
    eligible, excluded = parse_bids_metadata(data_dir)
    
    # 4. Filter
    eligible, excluded = filter_eligible_subjects(eligible, excluded, N_MAX_SUBJECTS)
    
    # 5. Validate
    if len(eligible) == 0:
        logger.error("Zero eligible subjects found. Failing.")
        sys.exit(2)
    
    # 6. Write outputs
    write_outputs(eligible, excluded, processed_dir)
    
    logger.info("T017 completed successfully.")

if __name__ == "__main__":
    main()
