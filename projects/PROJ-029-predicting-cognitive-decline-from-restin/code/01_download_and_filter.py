import os
import sys
import json
import time
import shutil
import tempfile
import logging
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from tqdm import tqdm
import tarfile
import gzip
import io

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logger import get_logger, log_excluded_subjects
from utils.io import ensure_dir, save_csv, load_csv
from config import get_config

# Constants
DATASET_ID = "ds000246"
OPENNEURO_API = "https://api.openneuro.org/crn/datasets"
OUTPUT_ELIGIBLE = "data/processed/eligible_subjects.csv"
OUTPUT_EXCLUDED = "data/processed/excluded_subjects.log"
MAX_SUBJECTS = 100
EXIT_CODE_NO_LABELS = 2
EXIT_CODE_SUCCESS = 0

# Logger setup
logger = get_logger("download_and_filter")

def get_logger_wrapper():
    return logger

def check_dataset_availability(dataset_id: str) -> bool:
    """Check if dataset exists on OpenNeuro."""
    url = f"{OPENNEURO_API}/{dataset_id}/snapshot"
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to check dataset availability: {e}")
        return False

def download_dataset(dataset_id: str, output_dir: Path) -> Optional[Path]:
    """Download dataset snapshot from OpenNeuro."""
    # OpenNeuro snapshot endpoint
    snapshot_url = f"https://datasets.openneuro.org/datasets/{dataset_id}/snapshots"
    try:
        # First, get the list of snapshots to find the latest
        resp = requests.get(snapshot_url, timeout=30)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch snapshot list: {resp.status_code}")
            return None

        snapshots = resp.json()
        if not snapshots:
            logger.error("No snapshots found for dataset")
            return None

        # Sort by version or creation date, pick latest
        latest = sorted(snapshots, key=lambda x: x.get('created', ''), reverse=True)[0]
        snapshot_id = latest.get('id') or latest.get('version')
        
        # Construct download URL for the snapshot tarball
        download_url = f"https://datasets.openneuro.org/datasets/{dataset_id}/snapshots/{snapshot_id}/tarball"
        
        logger.info(f"Downloading dataset from: {download_url}")
        output_tarball = output_dir / f"{dataset_id}.tar.gz"
        
        # Stream download
        with requests.get(download_url, stream=True, timeout=300) as r:
            r.raise_for_status()
            total_size = int(r.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB
            
            with open(output_tarball, 'wb') as f, tqdm(
                total=total_size, unit='B', unit_scale=True, desc="Downloading"
            ) as pbar:
                for chunk in r.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        pbar.update(len(chunk))
        
        # Extract tarball
        logger.info("Extracting dataset...")
        extract_dir = output_dir / "bids_data"
        extract_dir.mkdir(exist_ok=True)
        
        with tarfile.open(output_tarball, 'r:gz') as tar:
            tar.extractall(path=extract_dir)
        
        # Clean up tarball
        output_tarball.unlink()
        
        # Find the actual data directory (usually dataset_id inside)
        contents = list(extract_dir.iterdir())
        if len(contents) == 1 and contents[0].is_dir():
            return contents[0]
        return extract_dir

    except requests.exceptions.RequestException as e:
        logger.error(f"Download failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return None

def parse_bids_metadata(data_dir: Path) -> List[Dict[str, Any]]:
    """Parse BIDS metadata for all subjects to find cognitive scores."""
    subjects = []
    bids_dir = Path(data_dir)
    
    # Walk through BIDS structure
    for root, dirs, files in os.walk(bids_dir):
        for file in files:
            if file.endswith('.json'):
                file_path = Path(root) / file
                # Check if this is a subject-level file with cognitive data
                # Usually in sub-<label>/ses-<label>/anat/ or similar
                path_parts = file_path.relative_to(bids_dir).parts
                
                # Look for subject ID in path
                subject_id = None
                for part in path_parts:
                    if part.startswith('sub-'):
                        subject_id = part
                        break
                
                if not subject_id:
                    continue
                
                # Initialize subject record if not exists
                subject_record = None
                for s in subjects:
                    if s['subject_id'] == subject_id:
                        subject_record = s
                        break
                
                if not subject_record:
                    subject_record = {
                        'subject_id': subject_id,
                        'sessions': {},
                        'file_path': str(file_path)
                    }
                    subjects.append(subject_record)
                
                # Parse JSON content
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # Look for cognitive scores in various fields
                    # Common BIDS fields for cognitive data
                    cognitive_fields = ['MMSE', 'MOCA', 'cognitive_score', 'score']
                    session_id = None
                    
                    # Extract session from path
                    for part in path_parts:
                        if part.startswith('ses-'):
                            session_id = part
                            break
                    
                    if not session_id:
                        session_id = 'default'
                    
                    if session_id not in subject_record['sessions']:
                        subject_record['sessions'][session_id] = {}
                    
                    for field in cognitive_fields:
                        if field in data:
                            subject_record['sessions'][session_id][field] = data[field]
                            
                except (json.JSONDecodeError, IOError) as e:
                    logger.debug(f"Could not parse {file_path}: {e}")
                    continue
    
    return subjects

def filter_eligible_subjects(subjects: List[Dict], max_n: int = 100) -> tuple:
    """Filter subjects with non-null MMSE/MOCA at both timepoints."""
    eligible = []
    excluded = []
    
    for subject in subjects:
        sessions = subject.get('sessions', {})
        
        # Check for at least 2 sessions with cognitive scores
        sessions_with_scores = []
        for session_id, scores in sessions.items():
            mmse = scores.get('MMSE')
            moca = scores.get('MOCA')
            
            if mmse is not None or moca is not None:
                sessions_with_scores.append({
                    'session': session_id,
                    'mmse': mmse,
                    'moca': moca
                })
        
        # Requirement: non-null scores at BOTH timepoints
        if len(sessions_with_scores) >= 2:
            # Verify both sessions have at least one score
            valid = all(
                s['mmse'] is not None or s['moca'] is not None 
                for s in sessions_with_scores
            )
            
            if valid:
                eligible.append({
                    'subject_id': subject['subject_id'],
                    'sessions': sessions_with_scores,
                    'reason': 'Has cognitive scores at >= 2 timepoints'
                })
            else:
                excluded.append({
                    'subject_id': subject['subject_id'],
                    'reason': 'Not all timepoints have cognitive scores'
                })
        else:
            excluded.append({
                'subject_id': subject['subject_id'],
                'reason': f'Only {len(sessions_with_scores)} timepoint(s) with scores (need 2)'
            })
    
    # Limit to max_n
    if len(eligible) > max_n:
        logger.info(f"Limiting to {max_n} eligible subjects (found {len(eligible)})")
        eligible = eligible[:max_n]
        # The rest are effectively excluded due to limit
        for sub in eligible[max_n:]:
            excluded.append({
                'subject_id': sub['subject_id'],
                'reason': f'Exceeded limit of {max_n}'
            })
    
    return eligible, excluded

def write_outputs(eligible: List[Dict], excluded: List[Dict], output_dir: Path):
    """Write eligible subjects CSV and excluded subjects log."""
    ensure_dir(output_dir)
    
    # Write eligible subjects
    eligible_path = output_dir / "eligible_subjects.csv"
    data = []
    for sub in eligible:
        row = {
            'subject_id': sub['subject_id'],
            'num_sessions': len(sub['sessions']),
            'reason': sub['reason']
        }
        # Flatten session data for clarity
        for i, sess in enumerate(sub['sessions']):
            row[f'session_{i+1}'] = sess['session']
            row[f'mmse_{i+1}'] = sess['mmse']
            row[f'moca_{i+1}'] = sess['moca']
        data.append(row)
    
    if data:
        save_csv(data, str(eligible_path))
        logger.info(f"Wrote {len(data)} eligible subjects to {eligible_path}")
    else:
        # Create empty file with headers
        pd.DataFrame(columns=['subject_id', 'num_sessions', 'reason']).to_csv(eligible_path, index=False)
        logger.warning(f"No eligible subjects found. Created empty file at {eligible_path}")
    
    # Write excluded subjects log
    excluded_path = output_dir / "excluded_subjects.log"
    with open(excluded_path, 'w') as f:
        f.write(f"# Excluded Subjects Log - Generated {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total subjects processed: {len(eligible) + len(excluded)}\n")
        f.write(f"# Eligible: {len(eligible)}, Excluded: {len(excluded)}\n")
        f.write("#" + "="*60 + "\n\n")
        
        for sub in excluded:
            f.write(f"Subject: {sub['subject_id']}\n")
            f.write(f"  Reason: {sub['reason']}\n")
            f.write("\n")
    
    logger.info(f"Wrote {len(excluded)} excluded subjects to {excluded_path}")

def main():
    logger.info("Starting T017: Download and Filter")
    
    config = get_config()
    raw_dir = config.get('raw_data_dir', 'data/raw')
    processed_dir = config.get('processed_data_dir', 'data/processed')
    
    ensure_dir(Path(raw_dir))
    ensure_dir(Path(processed_dir))
    
    # Step 1: Check availability
    if not check_dataset_availability(DATASET_ID):
        logger.error(f"Dataset {DATASET_ID} not available on OpenNeuro.")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # Step 2: Download dataset
    data_dir = download_dataset(DATASET_ID, Path(raw_dir))
    if not data_dir or not data_dir.exists():
        logger.error("Failed to download or extract dataset.")
        sys.exit(1)
    
    # Step 3: Parse BIDS metadata
    logger.info("Parsing BIDS metadata...")
    subjects = parse_bids_metadata(data_dir)
    logger.info(f"Found {len(subjects)} subjects in dataset.")
    
    if len(subjects) == 0:
        logger.error("No subjects found in dataset.")
        sys.exit(1)
    
    # Step 4: Filter eligible subjects
    logger.info("Filtering eligible subjects...")
    eligible, excluded = filter_eligible_subjects(subjects, MAX_SUBJECTS)
    
    if len(eligible) == 0:
        logger.error("No eligible subjects found (require MMSE/MOCA at both timepoints).")
        sys.exit(EXIT_CODE_NO_LABELS)
    
    # Step 5: Write outputs
    logger.info("Writing output files...")
    write_outputs(eligible, excluded, Path(processed_dir))
    
    logger.info(f"T017 completed successfully. Eligible: {len(eligible)}, Excluded: {len(excluded)}")
    sys.exit(EXIT_CODE_SUCCESS)

if __name__ == "__main__":
    main()