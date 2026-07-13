"""
T017: Download and Filter Dataset
Downloads ds000246 from OpenNeuro, parses BIDS metadata, filters for subjects
with non-null MMSE/MOCA scores at both timepoints, and outputs eligible/excluded lists.
"""
import os
import sys
import json
import time
import shutil
import tempfile
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Local imports based on project API surface
from utils.logger import get_logger, log_excluded_subjects
from utils.io import ensure_dir, save_csv
from config import get_config

# Constants
DATASET_ID = "ds000246"
OPENNEURO_API_BASE = "https://api.openneuro.org/crn"
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_SUCCESS = 0
EXIT_CODE_DOWNLOAD_FAILURE = 1

logger = get_logger(__name__)

def check_dataset_availability(dataset_id: str) -> bool:
    """
    Check if the dataset exists on OpenNeuro.
    Returns True if available, False otherwise.
    """
    url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/snapshot"
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
    Download dataset from OpenNeuro using the API.
    Since we cannot use git-annex in this environment, we attempt to fetch
    a manifest or specific files if possible, or simulate the structure
    if the real download is blocked by network restrictions in the CI environment.
    
    NOTE: In a real CI environment without external network access to api.openneuro.org,
    this function will attempt to download a minimal manifest to verify existence,
    but for the purpose of this task, we rely on the 'data/raw' directory being
    pre-populated or the dataset being available via a local mirror if the network fails.
    However, per strict requirements, we MUST try the real source.
    """
    logger.info(f"Attempting to download {dataset_id} to {target_dir}...")
    
    # Ensure target directory exists
    ensure_dir(target_dir)
    
    # Attempt to download the dataset description first
    desc_url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/snapshot/dataset_description.json"
    try:
        resp = requests.get(desc_url, timeout=15)
        if resp.status_code == 200:
            desc_file = target_dir / "dataset_description.json"
            with open(desc_file, 'w') as f:
                f.write(resp.text)
            logger.info("Dataset description downloaded successfully.")
        else:
            logger.warning(f"Could not download dataset description: {resp.status_code}")
            # If we can't get the description, we can't verify the dataset structure
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during download: {e}")
        # If network is blocked, we cannot proceed with real data download.
        # We must fail loudly rather than fabricate data.
        return False

    # For a full download, OpenNeuro usually requires git-annex or their CLI.
    # Since we are restricted to Python standard libs + requests, we will fetch
    # the participant list and phenotype files if they exist.
    # We construct a list of potential phenotype files to fetch.
    # In a real scenario, we would use 'openneuro download'.
    # Here we simulate the extraction of subject metadata by fetching
    # the 'participants.tsv' and 'phenotype' directory if available.
    
    # Try to fetch participants.tsv
    participants_url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/snapshot/participants.tsv"
    try:
        resp = requests.get(participants_url, timeout=15)
        if resp.status_code == 200:
            part_file = target_dir / "participants.tsv"
            with open(part_file, 'w') as f:
                f.write(resp.text)
            logger.info("participants.tsv downloaded.")
        else:
            logger.warning("participants.tsv not found at standard location.")
    except Exception as e:
        logger.warning(f"Could not download participants.tsv: {e}")

    # Try to fetch phenotype data (where MMSE/MOCA usually live)
    # OpenNeuro datasets often store longitudinal data in phenotype/*.tsv
    phenotype_url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/snapshot/phenotype"
    try:
        resp = requests.get(phenotype_url, timeout=15)
        if resp.status_code == 200:
            # This returns a list of files
            files = resp.json()
            phenotype_dir = target_dir / "phenotype"
            ensure_dir(phenotype_dir)
            
            for file_info in files:
                fname = file_info.get('filename')
                if fname:
                    file_url = f"{OPENNEURO_API_BASE}/datasets/{dataset_id}/snapshot/phenotype/{fname}"
                    file_resp = requests.get(file_url, timeout=15)
                    if file_resp.status_code == 200:
                        with open(phenotype_dir / fname, 'w') as f:
                            f.write(file_resp.text)
                        logger.info(f"Downloaded phenotype file: {fname}")
    except Exception as e:
        logger.warning(f"Could not download phenotype directory: {e}")

    # Verify we have some data
    if not (target_dir / "dataset_description.json").exists():
        return False
        
    return True

def parse_bids_metadata(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Parse BIDS metadata to extract subject IDs and cognitive scores (MMSE/MOCA).
    Looks for participants.tsv and phenotype files.
    """
    subjects_data = []
    
    # 1. Check participants.tsv
    participants_file = data_dir / "participants.tsv"
    if participants_file.exists():
        try:
            df = pd.read_csv(participants_file, sep='\t')
            # Normalize columns
            df.columns = df.columns.str.strip().str.lower()
            
            # Look for cognitive scores
            # Common columns: 'participant_id', 'mmse', 'moca', 'timepoint'
            # We need to handle cases where scores are in phenotype files
            
            for idx, row in df.iterrows():
                sub_id = row.get('participant_id', row.get('subject_id', f'sub-{idx}'))
                # Clean sub_id
                if not sub_id.startswith('sub-'):
                    sub_id = f"sub-{sub_id}"
                
                # Extract scores if present in participants.tsv
                mmse = row.get('mmse', None)
                moca = row.get('moca', None)
                timepoint = row.get('timepoint', 'baseline') # Default assumption
                
                subjects_data.append({
                    'subject_id': sub_id,
                    'mmse': mmse,
                    'moca': moca,
                    'timepoint': timepoint,
                    'source': 'participants.tsv'
                })
        except Exception as e:
            logger.warning(f"Error parsing participants.tsv: {e}")
    else:
        logger.warning("participants.tsv not found. Attempting to parse phenotype files.")

    # 2. Check phenotype directory for longitudinal data
    phenotype_dir = data_dir / "phenotype"
    if phenotype_dir.exists():
        for file_path in phenotype_dir.glob("*.tsv"):
            try:
                df = pd.read_csv(file_path, sep='\t')
                df.columns = df.columns.str.strip().str.lower()
                
                # Identify subject column
                sub_col = None
                for col in ['participant_id', 'subject_id', 'sub', 'participant']:
                    if col in df.columns:
                        sub_col = col
                        break
                
                if not sub_col:
                    logger.warning(f"Could not find subject column in {file_path}")
                    continue
                
                # Identify score columns (mmse, moca)
                score_cols = [c for c in df.columns if 'mmse' in c or 'moca' in c]
                
                if not score_cols:
                    continue
                
                # Determine timepoint column
                tp_col = None
                for col in ['timepoint', 'visit', 'session', 'wave']:
                    if col in df.columns:
                        tp_col = col
                        break
                
                for idx, row in df.iterrows():
                    sub_id = row.get(sub_col, f"sub-{idx}")
                    if not isinstance(sub_id, str) or not sub_id.startswith('sub-'):
                        sub_id = f"sub-{sub_id}"
                    
                    # Find MMSE and MOCA values
                    mmse_val = None
                    moca_val = None
                    tp_val = row.get(tp_col, 'unknown') if tp_col else 'unknown'
                    
                    for col in score_cols:
                        val = row.get(col)
                        if pd.notna(val):
                            if 'mmse' in col:
                                mmse_val = val
                            elif 'moca' in col:
                                moca_val = val
                    
                    # Check if we already have this subject+timepoint
                    existing = next((s for s in subjects_data if s['subject_id'] == sub_id and s['timepoint'] == tp_val), None)
                    if existing:
                        # Update if new data is better
                        if mmse_val is not None: existing['mmse'] = mmse_val
                        if moca_val is not None: existing['moca'] = moca_val
                    else:
                        subjects_data.append({
                            'subject_id': sub_id,
                            'mmse': mmse_val,
                            'moca': moca_val,
                            'timepoint': tp_val,
                            'source': file_path.name
                        })
            except Exception as e:
                logger.warning(f"Error parsing phenotype file {file_path}: {e}")

    return subjects_data

def filter_eligible_subjects(subjects_data: List[Dict[str, Any]], n_limit: int = 100) -> Tuple[List[Dict], List[Dict]]:
    """
    Filter subjects who have non-null MMSE or MOCA at BOTH timepoints (baseline and follow-up).
    Returns (eligible_list, excluded_list).
    """
    # Group by subject
    from collections import defaultdict
    subject_scores = defaultdict(list)
    
    for s in subjects_data:
        sub_id = s['subject_id']
        # Only consider if they have at least one score
        if pd.notna(s['mmse']) or pd.notna(s['moca']):
            subject_scores[sub_id].append(s)
    
    eligible = []
    excluded = []
    
    for sub_id, scores in subject_scores.items():
        # Check for at least two timepoints
        timepoints = set(s['timepoint'] for s in scores)
        
        # We need 'both' timepoints. Assuming standard BIDS has 'baseline' and 'followup' or similar.
        # If the dataset only has one timepoint per subject, they are excluded for longitudinal analysis.
        # However, if the task implies 'two measurements' regardless of label, we check count >= 2.
        # Strict interpretation: "at both timepoints" implies two distinct visits.
        if len(timepoints) < 2:
            excluded.append({'subject_id': sub_id, 'reason': f'Only {len(timepoints)} timepoint(s) found. Need 2.'})
            continue
        
        # Check if every timepoint has a score (MMSE or MOCA)
        # We assume the data structure has one row per timepoint.
        # If a subject has 2 rows, both must have a score.
        valid_scores = all(pd.notna(s['mmse']) or pd.notna(s['moca']) for s in scores)
        
        if valid_scores:
            # Aggregate scores for the subject (e.g., take the first available MMSE/MOCA per timepoint)
            # For the output, we just need the subject ID and the fact they are eligible.
            # We store the raw scores for reference.
            eligible.append({
                'subject_id': sub_id,
                'timepoints': list(timepoints),
                'score_count': len(scores)
            })
        else:
            excluded.append({'subject_id': sub_id, 'reason': 'Missing scores at one or more timepoints.'})
    
    # Limit to N
    if len(eligible) > n_limit:
        # Sort by subject_id for reproducibility
        eligible.sort(key=lambda x: x['subject_id'])
        eligible = eligible[:n_limit]
        logger.info(f"Limiting eligible subjects to {n_limit}.")
    
    return eligible, excluded

def write_outputs(eligible: List[Dict], excluded: List[Dict], output_dir: Path):
    """
    Write eligible_subjects.csv and excluded_subjects.log
    """
    ensure_dir(output_dir)
    
    # Write eligible subjects
    eligible_file = output_dir / "eligible_subjects.csv"
    if eligible:
        df_eligible = pd.DataFrame(eligible)
        save_csv(df_eligible, eligible_file)
        logger.info(f"Written {len(eligible)} eligible subjects to {eligible_file}")
    else:
        # Create empty file with headers if none found
        pd.DataFrame(columns=['subject_id', 'timepoints', 'score_count']).to_csv(eligible_file, index=False)
        logger.warning("No eligible subjects found. Created empty file.")
    
    # Write excluded subjects log
    excluded_file = output_dir / "excluded_subjects.log"
    with open(excluded_file, 'w') as f:
        f.write("Excluded Subjects Log\n")
        f.write("=" * 40 + "\n")
        for item in excluded:
            f.write(f"Subject: {item['subject_id']} | Reason: {item['reason']}\n")
        if not excluded:
            f.write("No subjects excluded.\n")
    logger.info(f"Written excluded subjects log to {excluded_file}")

def main():
    logger.info("Starting T017: Download and Filter")
    
    config = get_config()
    data_raw_dir = Path(config.get('data_raw_dir', 'data/raw'))
    data_processed_dir = Path(config.get('data_processed_dir', 'data/processed'))
    
    # 1. Check availability
    if not check_dataset_availability(DATASET_ID):
        logger.error(f"Dataset {DATASET_ID} not available on OpenNeuro.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 2. Download
    if not download_dataset(DATASET_ID, data_raw_dir):
        logger.error("Failed to download dataset.")
        sys.exit(EXIT_CODE_DOWNLOAD_FAILURE)
    
    # 3. Parse metadata
    subjects_data = parse_bids_metadata(data_raw_dir)
    logger.info(f"Parsed metadata for {len(subjects_data)} subject entries.")
    
    if not subjects_data:
        logger.error("No subject data found in dataset.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 4. Filter
    eligible, excluded = filter_eligible_subjects(subjects_data, n_limit=100)
    
    if len(eligible) == 0:
        logger.error("Zero eligible subjects found after filtering.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # 5. Write outputs
    write_outputs(eligible, excluded, data_processed_dir)
    
    logger.info("T017 completed successfully.")
    sys.exit(EXIT_CODE_SUCCESS)

if __name__ == "__main__":
    main()