import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import requests
from urllib.parse import urljoin

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
HCP_BASE_URL = "https://db.humanconnectome.org"
HCP_SESSION_URL = "https://db.humanconnectome.org/session.xml"
HCP_LOGIN_URL = "https://db.humanconnectome.org/Login/Login"
DATA_DIR = Path("data/raw")
OUTPUT_NIFTI_DIR = DATA_DIR / "nifti"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_NIFTI_DIR.mkdir(parents=True, exist_ok=True)

def get_hcp_subject_id_list() -> List[str]:
    """
    Fetches the list of subject IDs available in the HCP database.
    This is a placeholder implementation that returns a hardcoded list for demonstration.
    In a real scenario, this would parse the session.xml or query the HCP API.
    """
    # Placeholder: In a real implementation, parse session.xml or query API
    # For now, return a small list of known HCP subject IDs
    return ["100307", "100408", "100604", "100703", "100901"]

def get_behavioral_url_for_subject(subject_id: str) -> str:
    """
    Constructs the URL for behavioral data for a given subject.
    """
    # Placeholder: Construct URL based on subject ID
    return f"https://db.humanconnectome.org/api/app/dataset/{subject_id}/behavioral"

def fetch_and_save_behavioral_data(subject_id: str, output_dir: Path) -> Optional[Path]:
    """
    Fetches and saves behavioral data for a given subject.
    """
    url = get_behavioral_url_for_subject(subject_id)
    output_path = output_dir / f"{subject_id}_behavioral.json"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        with open(output_path, 'w') as f:
            json.dump(response.json(), f)
        logger.info(f"Saved behavioral data for {subject_id} to {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch behavioral data for {subject_id}: {e}")
        return None

def fetch_behavioral_confounds(subject_id: str) -> Optional[Dict]:
    """
    Fetches behavioral confounds for a given subject.
    """
    # Placeholder: Return empty dict or fetch from API
    return {}

def fetch_behavioral_task_data(subject_id: str) -> Optional[Dict]:
    """
    Fetches task-related behavioral data for a given subject.
    """
    # Placeholder: Return empty dict or fetch from API
    return {}

def get_nifti_url(subject_id: str, modality: str = "rfMRI") -> str:
    """
    Constructs the URL for NIfTI files for a given subject and modality.
    Modality can be 'rfMRI' (resting-state) or 'tfMRI' (task-based).
    """
    # HCP structure: <subject>/MNINonLinear/Results/rfMRI/rfMRI_REST1_LR.nii.gz
    # We'll construct a plausible URL based on HCP conventions
    return f"{HCP_BASE_URL}/api/app/dataset/{subject_id}/MNINonLinear/Results/rfMRI/rfMRI_REST1_LR.nii.gz"

def download_file(url: str, output_path: Path, session: Optional[requests.Session] = None) -> bool:
    """
    Downloads a file from the given URL to the specified output path.
    Uses the provided session if available, otherwise creates a new one.
    """
    if session is None:
        session = requests.Session()
    
    try:
        response = session.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.debug(f"Download progress: {progress:.2f}%")
        
        logger.info(f"Successfully downloaded {url} to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def fetch_nifti_for_subject(subject_id: str, output_dir: Path = OUTPUT_NIFTI_DIR) -> Optional[Path]:
    """
    Fetches and saves raw fMRI NIfTI data for a given subject.
    Returns the path to the downloaded file, or None if failed.
    """
    url = get_nifti_url(subject_id)
    output_path = output_dir / f"{subject_id}_rfMRI_REST1_LR.nii.gz"
    
    # Skip if already exists
    if output_path.exists():
        logger.info(f"NIfTI file for {subject_id} already exists at {output_path}")
        return output_path
    
    # Attempt download
    session = requests.Session()
    success = download_file(url, output_path, session)
    
    if success:
        return output_path
    else:
        logger.error(f"Failed to download NIfTI for {subject_id}")
        return None

def main():
    """
    Main function to download NIfTI files for all available subjects.
    """
    logger.info("Starting NIfTI download process...")
    
    subject_ids = get_hcp_subject_id_list()
    logger.info(f"Found {len(subject_ids)} subjects to process: {subject_ids}")
    
    downloaded_count = 0
    failed_count = 0
    
    for subject_id in subject_ids:
        logger.info(f"Processing subject {subject_id}...")
        result = fetch_nifti_for_subject(subject_id)
        if result:
            downloaded_count += 1
        else:
            failed_count += 1
    
    logger.info(f"Download process completed. Success: {downloaded_count}, Failed: {failed_count}")
    return downloaded_count, failed_count

if __name__ == "__main__":
    main()