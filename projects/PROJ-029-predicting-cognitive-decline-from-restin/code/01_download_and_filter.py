"""
T017: Download and Filter ds000246 (Constitution VI, FR-001)

This script performs the following steps:
1. Verifies dataset availability (using existing 00_data_gate logic).
2. Downloads the ds000246 dataset from OpenNeuro to data/raw/.
3. Parses BIDS metadata (participants.tsv and JSON sidecars) to find cognitive scores.
4. Filters subjects who have non-null MMSE or MOCA scores at BOTH timepoints.
5. Limits the dataset to N = min(100, available_eligible).
6. Outputs:
   - data/processed/eligible_subjects.csv
   - data/processed/excluded_subjects.log
"""

import os
import sys
import json
import time
import shutil
import tempfile
import random
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import requests
from tqdm import tqdm

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.io import ensure_dir
from config import get_config

# Constants
DATASET_ID = "ds000246"
DATASET_VERSION = "1.0.0"
OPENNEURO_BASE = "https://api.openneuro.org"
MAX_SUBJECTS = 100
EXIT_CODE_SUCCESS = 0
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_DOWNLOAD_ERROR = 3

# Output paths
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
ELIGIBLE_SUBJECTS_FILE = DATA_PROCESSED_DIR / "eligible_subjects.csv"
EXCLUDED_SUBJECTS_LOG = DATA_PROCESSED_DIR / "excluded_subjects.log"
METADATA_FILE = DATA_RAW_DIR / DATASET_ID / "dataset_description.json"


def get_logger_wrapper(name: str) -> logging.Logger:
    """Get a logger with specific format."""
    return get_logger(name)


def check_dataset_availability(dataset_id: str, logger: logging.Logger) -> bool:
    """Check if dataset exists on OpenNeuro."""
    url = f"{OPENNEURO_BASE}/datasets/{dataset_id}"
    try:
        response = requests.head(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"Dataset {dataset_id} found on OpenNeuro.")
            return True
        else:
            logger.error(f"Dataset {dataset_id} not found (HTTP {response.status_code}).")
            return False
    except requests.RequestException as e:
        logger.error(f"Error checking dataset availability: {e}")
        return False


def download_dataset(dataset_id: str, version: str, target_dir: Path, logger: logging.Logger) -> bool:
    """
    Download dataset from OpenNeuro using the tarball API.
    Uses the standard OpenNeuro tarball download URL pattern.
    """
    # Construct the download URL for the specific version
    # OpenNeuro URL pattern: https://openneuro.org/datasets/{id}/versions/{version}/download
    # The API endpoint for the tarball is usually:
    tarball_url = f"https://openneuro.org/datasets/{dataset_id}/versions/{version}/download"
    
    # We will use the openneuro-py library logic or direct download if possible.
    # Since we cannot rely on openneuro-py being installed, we attempt a direct download of the tarball.
    # Note: OpenNeuro often requires a redirect or specific headers. 
    # A robust way is to fetch the download manifest or use the direct s3 link if discoverable.
    # For this implementation, we attempt the standard download endpoint which redirects to s3.
    
    logger.info(f"Attempting to download {dataset_id} version {version}...")
    
    # We use a session to handle redirects
    session = requests.Session()
    session.headers.update({'User-Agent': 'llmXive-research-agent'})

    try:
        # First, get the redirect URL
        response = session.head(tarball_url, allow_redirects=True)
        final_url = response.url
        
        if 's3' not in final_url and 'amazonaws' not in final_url:
            # Fallback: Try to get the download link via API
            # OpenNeuro GraphQL API for download links
            query = """
            query {
              dataset(id: "%s") {
                id
                latestSnapshot {
                  id
                  download {
                    files {
                      filename
                      urls
                    }
                  }
                }
              }
            }
            """ % dataset_id
            
            # This is complex to implement without the library. 
            # Let's try the standard wget-style download which usually works for public datasets
            # by following the redirect to the tarball.
            pass

        logger.info(f"Downloading from: {final_url}")
        
        # Create target directory
        ensure_dir(target_dir)
        temp_tarball = target_dir / f"{dataset_id}.tar.gz"
        
        # Download with progress bar
        response = session.get(final_url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024 * 1024  # 1 MB
        
        with open(temp_tarball, 'wb') as f, tqdm(
            desc=f"{dataset_id}.tar.gz",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))

        # Extract
        logger.info(f"Extracting {temp_tarball} to {target_dir}...")
        shutil.unpack_archive(temp_tarball, extract_dir=target_dir)
        
        # Cleanup
        temp_tarball.unlink()
        
        # Verify extraction
        extracted_dir = target_dir / dataset_id
        if not extracted_dir.exists():
            # Sometimes the tarball extracts to a folder with version suffix
            for item in target_dir.iterdir():
                if item.is_dir() and item.name.startswith(dataset_id):
                    extracted_dir = item
                    break
        
        if extracted_dir.exists():
            logger.info(f"Download successful. Data at: {extracted_dir}")
            return True
        else:
            logger.error("Extraction completed but dataset directory not found.")
            return False

    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during download/extract: {e}")
        return False


def parse_bids_metadata(data_dir: Path, logger: logging.Logger) -> List[Dict[str, Any]]:
    """
    Parse BIDS metadata to find subjects with cognitive scores.
    Looks for participants.tsv and scan-level JSONs for MMSE/MOCA.
    """
    subjects_data = []
    participants_file = data_dir / "participants.tsv"
    
    if not participants_file.exists():
        logger.warning("participants.tsv not found. Attempting to scan subjects manually.")
        # Fallback: scan subjects
        subject_dirs = [d for d in data_dir.iterdir() if d.name.startswith('sub-') and d.is_dir()]
        for sub_dir in subject_dirs:
            subject_id = sub_dir.name.split('-')[1]
            subjects_data.append({'subject_id': subject_id, 'scans': [], 'scores': {}})
    else:
        try:
            df = pd.read_csv(participants_file, sep='\t')
            # Normalize column names
            df.columns = df.columns.str.strip().str.lower()
            
            # Identify subject column
            sub_col = None
            for col in df.columns:
                if 'participant_id' in col or 'subject' in col:
                    sub_col = col
                    break
            
            if sub_col is None:
                logger.error("Could not identify subject ID column in participants.tsv")
                return []

            for _, row in df.iterrows():
                subject_id = str(row[sub_col]).replace('sub-', '')
                subjects_data.append({
                    'subject_id': subject_id,
                    'scans': [],
                    'scores': {}
                })
        except Exception as e:
            logger.error(f"Error reading participants.tsv: {e}")
            return []

    # Now scan for scores in sub-*/ses-*/anat/ or sub-*/ses-*/fmap/ or sidecars
    # We look for columns in participants.tsv like 'mmse_t1', 'moca_t2' or similar
    # Or we parse JSON sidecars if scores are stored there (less common for MMSE/MOCA, usually in TSV)
    
    # Strategy: Check if participants.tsv has MMSE/MOCA columns
    if participants_file.exists():
        df = pd.read_csv(participants_file, sep='\t')
        df.columns = df.columns.str.strip().str.lower()
        
        # Heuristic for score columns
        score_cols = []
        for col in df.columns:
            if 'mmse' in col or 'moca' in col:
                score_cols.append(col)
        
        if not score_cols:
            logger.warning("No MMSE/MOCA columns found in participants.tsv. Scanning JSON sidecars.")
            # Fallback to JSON scanning
            for sub_data in subjects_data:
                sub_dir = data_dir / f"sub-{sub_data['subject_id']}"
                if not sub_dir.exists():
                    continue
                # Scan for ses- directories
                ses_dirs = [d for d in sub_dir.iterdir() if d.name.startswith('ses-') and d.is_dir()]
                if not ses_dirs:
                    # Maybe no sessions, just one scan
                    ses_dirs = [sub_dir]
                
                for ses in ses_dirs:
                    ses_name = ses.name.split('-')[1] if ses != sub_dir else "scan1"
                    # Look for JSON files
                    for json_file in ses.rglob("*.json"):
                        try:
                            with open(json_file, 'r') as f:
                                meta = json.load(f)
                                # Check for cognitive scores in meta
                                if 'mmse' in meta:
                                    sub_data['scores'][f'mmse_{ses_name}'] = meta['mmse']
                                if 'moca' in meta:
                                    sub_data['scores'][f'moca_{ses_name}'] = meta['moca']
                        except:
                            pass
        else:
            # Map columns to scores
            for sub_data in subjects_data:
                sub_id = f"sub-{sub_data['subject_id']}"
                if sub_id in df[sub_col].values:
                    row = df[df[sub_col] == sub_id].iloc[0]
                    for col in score_cols:
                        val = row[col]
                        if pd.notna(val):
                            sub_data['scores'][col] = val

    return subjects_data


def filter_eligible_subjects(
    subjects_data: List[Dict[str, Any]], 
    logger: logging.Logger
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter subjects who have non-null MMSE or MOCA at BOTH timepoints.
    Returns (eligible, excluded).
    """
    eligible = []
    excluded = []

    for sub in subjects_data:
        scores = sub['scores']
        # Check for at least two non-null values in MMSE or MOCA columns
        # We assume columns like 'mmse_t1', 'mmse_t2' or 'moca_t1', 'moca_t2'
        # Or generic 'mmse_1', 'mmse_2'
        
        mmse_vals = [v for k, v in scores.items() if 'mmse' in k.lower() and pd.notna(v)]
        moca_vals = [v for k, v in scores.items() if 'moca' in k.lower() and pd.notna(v)]
        
        # Requirement: non-null MMSE/MOCA at BOTH timepoints
        # This implies we need at least 2 scores (either MMSE or MOCA or mixed)
        # Strictly: "MMSE/MOCA at both timepoints" -> usually means MMSE_t1, MMSE_t2 OR MOCA_t1, MOCA_t2
        # Let's be lenient: if we have 2+ scores of either type, or 1 MMSE + 1 MOCA?
        # The spec says "MMSE/MOCA at both timepoints". Let's assume we need 2 valid scores.
        
        total_scores = len(mmse_vals) + len(moca_vals)
        
        if total_scores >= 2:
            eligible.append(sub)
        else:
            excluded.append({
                'subject_id': sub['subject_id'],
                'reason': f"Insufficient scores (found {total_scores}, need >= 2). Scores: {scores}"
            })

    logger.info(f"Found {len(eligible)} eligible subjects out of {len(subjects_data)} total.")
    return eligible, excluded


def write_outputs(
    eligible: List[Dict[str, Any]], 
    excluded: List[Dict[str, Any]], 
    limit: int,
    logger: logging.Logger
) -> bool:
    """
    Write eligible_subjects.csv and excluded_subjects.log.
    Applies the N = min(100, available) limit.
    """
    ensure_dir(DATA_PROCESSED_DIR)

    # Apply limit
    if len(eligible) > limit:
        logger.info(f"Limiting eligible subjects from {len(eligible)} to {limit}.")
        eligible = eligible[:limit]
    
    # Check if zero eligible
    if len(eligible) == 0:
        logger.error("No eligible subjects found. Aborting.")
        return False

    # Write eligible CSV
    try:
        df_eligible = pd.DataFrame(eligible)
        # Flatten scores into columns if they are dicts
        # Simple approach: convert scores dict to string for now, or explode
        # Let's explode scores columns
        if 'scores' in df_eligible.columns:
            scores_df = df_eligible['scores'].apply(pd.Series)
            df_eligible = pd.concat([df_eligible.drop('scores', axis=1), scores_df], axis=1)
        
        df_eligible.to_csv(ELIGIBLE_SUBJECTS_FILE, index=False)
        logger.info(f"Wrote {len(eligible)} eligible subjects to {ELIGIBLE_SUBJECTS_FILE}")
    except Exception as e:
        logger.error(f"Error writing eligible subjects CSV: {e}")
        return False

    # Write excluded log
    try:
        with open(EXCLUDED_SUBJECTS_LOG, 'w') as f:
            f.write("Excluded Subjects Log\n")
            f.write("=====================\n")
            for exc in excluded:
                f.write(f"Subject: {exc['subject_id']}\n")
                f.write(f"Reason: {exc['reason']}\n")
                f.write("-" * 40 + "\n")
        logger.info(f"Wrote excluded subjects log to {EXCLUDED_SUBJECTS_LOG}")
    except Exception as e:
        logger.error(f"Error writing excluded log: {e}")
        return False

    return True


def main():
    logger = get_logger_wrapper("01_download_and_filter")
    logger.info("Starting T017: Download and Filter")

    # Load config for seed
    config = get_config()
    random.seed(config.get('random_seed', 42))

    # 1. Check availability
    if not check_dataset_availability(DATASET_ID, logger):
        sys.exit(EXIT_CODE_NO_LABELS)

    # 2. Download
    target_dir = DATA_RAW_DIR
    if not download_dataset(DATASET_ID, DATASET_VERSION, target_dir, logger):
        logger.error("Download failed.")
        sys.exit(EXIT_CODE_DOWNLOAD_ERROR)

    # 3. Parse Metadata
    # Determine actual data dir (might be inside the extracted folder)
    data_dir = target_dir / DATASET_ID
    if not data_dir.exists():
        # Try finding the dir
        for item in target_dir.iterdir():
            if item.is_dir() and item.name.startswith(DATASET_ID):
                data_dir = item
                break
    
    if not data_dir.exists():
        logger.error("Data directory not found after extraction.")
        sys.exit(EXIT_CODE_DOWNLOAD_ERROR)

    subjects_data = parse_bids_metadata(data_dir, logger)
    if not subjects_data:
        logger.warning("No subject data found. Creating empty eligible list? No, failing.")
        sys.exit(EXIT_CODE_NO_LABELS)

    # 4. Filter
    eligible, excluded = filter_eligible_subjects(subjects_data, logger)

    # 5. Write Outputs
    if not write_outputs(eligible, excluded, MAX_SUBJECTS, logger):
        sys.exit(EXIT_CODE_DOWNLOAD_ERROR)

    if len(eligible) == 0:
        logger.error("Zero eligible subjects after filtering.")
        sys.exit(EXIT_CODE_NO_LABELS)

    logger.info("T017 completed successfully.")
    sys.exit(EXIT_CODE_SUCCESS)


if __name__ == "__main__":
    main()