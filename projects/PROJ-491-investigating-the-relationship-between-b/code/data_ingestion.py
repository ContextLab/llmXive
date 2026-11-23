import os
import sys
import json
import logging
import hashlib
import time
import requests
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Set
from collections import defaultdict

# Import from local project modules (per API surface)
from config import ensure_directories
from env_config import get_openneuro_config, OpenNeuroConfig
from state_manager import update_state_artifact, load_state, save_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/ingestion_warnings.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
REQUIRED_SUBJECTS = 50

def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def fetch_subject_list() -> List[Dict]:
    """
    Fetch list of subjects from OpenNeuro HCP dataset.
    Returns a list of dicts with 'subject_id' and 'session_id'.
    """
    config = get_openneuro_config()
    dataset_id = config.dataset_id
    base_url = f"https://openneuro.org/datasets/{dataset_id}/files"
    
    # In a real implementation, this would query the OpenNeuro API or
    # parse the dataset manifest. For this pipeline, we assume a manifest
    # exists or we fetch from a known endpoint.
    # Placeholder logic to simulate fetching subject info:
    # Real implementation would parse JSON from OpenNeuro API
    logger.info(f"Fetching subject list for dataset {dataset_id}...")
    
    # Simulating a fetch - in production, replace with actual API call
    # Example: response = requests.get(f"{base_url}/manifest.json")
    # subjects = response.json()
    
    # Since we cannot actually call OpenNeuro API without credentials/network in this context,
    # we assume the data ingestion script T012 has already populated data/raw with a manifest
    # or we use a local cache.
    manifest_path = DATA_RAW_DIR / 'hcp_subject_manifest.json'
    
    if not manifest_path.exists():
        # Fallback: try to download a small manifest if possible
        # For now, raise error if manifest missing (T012 should have created it)
        raise FileNotFoundError(
            f"Subject manifest not found at {manifest_path}. "
            "Ensure T012 (data ingestion) has run to download subject metadata."
        )
    
    with open(manifest_path, 'r') as f:
        manifest_data = json.load(f)
    
    return manifest_data.get('subjects', [])

def validate_session_distinctness(subjects: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Validate that each subject has a unique session ID.
    FR-008: Explicitly exclude subjects with matching session IDs.
    
    Args:
        subjects: List of subject dicts with 'subject_id' and 'session_id'
    
    Returns:
        Tuple of (valid_subjects, excluded_subjects)
    """
    logger.info("Validating session ID distinctness...")
    
    # Track session IDs seen
    session_to_subjects: Dict[str, List[str]] = defaultdict(list)
    
    for sub in subjects:
        sid = sub.get('session_id')
        subj_id = sub.get('subject_id')
        if not sid or not subj_id:
            logger.warning(f"Skipping subject {subj_id} due to missing session ID")
            continue
        session_to_subjects[sid].append(subj_id)
    
    # Identify duplicate sessions
    duplicate_sessions = {sid: subs for sid, subs in session_to_subjects.items() if len(subs) > 1}
    
    valid_subjects = []
    excluded_subjects = []
    
    for sub in subjects:
        sid = sub.get('session_id')
        subj_id = sub.get('subject_id')
        
        if not sid:
            excluded_subjects.append(sub)
            logger.warning(f"Excluded subject {subj_id}: Missing session ID")
            continue
        
        if len(session_to_subjects[sid]) > 1:
            # This session has duplicates, exclude ALL subjects with this session
            excluded_subjects.append(sub)
            logger.warning(
                f"Excluded subject {subj_id} (session {sid}): "
                f"Session ID shared with {len(session_to_subjects[sid])} other subjects"
            )
        else:
            valid_subjects.append(sub)
    
    logger.info(f"Session validation complete: {len(valid_subjects)} valid, {len(excluded_subjects)} excluded")
    return valid_subjects, excluded_subjects

def download_file_with_progress(url: str, dest_path: Path, chunk_size: int = 8192):
    """Download a file with progress logging."""
    logger.info(f"Downloading {url} to {dest_path}")
    ensure_directories([dest_path.parent])
    
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

def verify_nifti_file(filepath: Path) -> bool:
    """Verify a NIfTI file is readable and valid."""
    try:
        import nibabel as nib
        img = nib.load(str(filepath))
        # Check if data can be accessed
        _ = img.get_fdata()
        return True
    except Exception as e:
        logger.warning(f"Invalid NIfTI file {filepath}: {e}")
        return False

def download_subject_data(subject_info: Dict, config: OpenNeuroConfig):
    """Download data for a single subject."""
    subj_id = subject_info['subject_id']
    session_id = subject_info['session_id']
    
    subject_dir = DATA_RAW_DIR / subj_id / session_id
    ensure_directories([subject_dir])
    
    # In real implementation, download resting and task files
    # For T013, we assume T012 handles the actual download
    logger.info(f"Subject {subj_id} (session {session_id}) data location: {subject_dir}")
    # Placeholder for actual download logic
    return True

def check_disk_usage(path: Path) -> float:
    """Check disk usage in GB."""
    total, used, free = shutil.disk_usage(path)
    return used / (1024 ** 3)

def main():
    """Main entry point for T013: Session ID distinctness validation."""
    ensure_directories([DATA_RAW_DIR, DATA_PROCESSED_DIR])
    
    try:
        # Fetch subject list
        subjects = fetch_subject_list()
        logger.info(f"Fetched {len(subjects)} subjects from manifest")
        
        if not subjects:
            logger.error("No subjects found in manifest")
            sys.exit(1)
        
        # Validate session distinctness
        valid_subjects, excluded_subjects = validate_session_distinctness(subjects)
        
        # Write excluded subject IDs to CSV (T013c requirement)
        if excluded_subjects:
            excluded_csv_path = DATA_PROCESSED_DIR / 'excluded_session_ids.csv'
            with open(excluded_csv_path, 'w') as f:
                f.write('subject_id,session_id,reason\n')
                for sub in excluded_subjects:
                    reason = "Duplicate session ID" if sub.get('session_id') else "Missing session ID"
                    f.write(f"{sub.get('subject_id')},{sub.get('session_id')},{reason}\n")
            logger.info(f"Wrote {len(excluded_subjects)} excluded subjects to {excluded_csv_path}")
        
        # Calculate pass-rate percentage (T013b requirement)
        total_subjects = len(subjects)
        valid_count = len(valid_subjects)
        pass_rate = (valid_count / total_subjects * 100) if total_subjects > 0 else 0.0
        
        metrics = {
            "total_subjects": total_subjects,
            "valid_subjects": valid_count,
            "excluded_subjects": len(excluded_subjects),
            "pass_rate_percentage": round(pass_rate, 2),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        metrics_path = DATA_PROCESSED_DIR / 'session_validation_metrics.json'
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Wrote session validation metrics to {metrics_path}")
        
        # Update state manager
        update_state_artifact("session_validation_metrics.json", metrics_path)
        update_state_artifact("excluded_session_ids.csv", DATA_PROCESSED_DIR / "excluded_session_ids.csv")
        
        # Log final status
        if valid_count < REQUIRED_SUBJECTS:
            logger.warning(
                f"Only {valid_count} valid subjects found (required: {REQUIRED_SUBJECTS}). "
                "Downstream tasks may fail."
            )
        else:
            logger.info(f"Successfully validated {valid_count} subjects with distinct session IDs.")
        
        return valid_subjects, excluded_subjects, metrics
        
    except Exception as e:
        logger.error(f"Session validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()