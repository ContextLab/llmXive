import os
import hashlib
import requests
from urllib.parse import urljoin
import logging
import time
import json
from pathlib import Path
import sys

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
OPENNEURO_BASE_URL = "https://openneuro.org/datasets"
DATA_DIR = Path(__file__).parent.parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
METADATA_DIR = DATA_DIR / "metadata"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

class DataFetchError(Exception):
    """Exception raised when data fetch fails."""
    pass

def download_url_exists(dataset_id: str) -> bool:
    """
    Check if the dataset URL exists on OpenNeuro.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier (e.g., 'ds000030')
        
    Returns:
        True if the dataset exists, False otherwise
    """
    url = f"{OPENNEURO_BASE_URL}/{dataset_id}"
    try:
        response = requests.head(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException as e:
        logger.warning(f"Could not check URL existence for {dataset_id}: {e}")
        return False

def get_dataset_download_url(dataset_id: str) -> str:
    """
    Get the download URL for an OpenNeuro dataset.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier
        
    Returns:
        The download URL string
    """
    # OpenNeuro download URL pattern
    return f"https://s3.amazonaws.com/openneuro.org/{dataset_id}.tar.gz"

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the SHA256 checksum of a downloaded file.
    
    Args:
        file_path: Path to the downloaded file
        expected_checksum: Expected SHA256 checksum string
        
    Returns:
        True if checksum matches, False otherwise
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        actual_checksum = sha256_hash.hexdigest()
        return actual_checksum == expected_checksum
    except Exception as e:
        logger.error(f"Error verifying checksum for {file_path}: {e}")
        return False

def download_dataset(dataset_id: str, output_dir: Path = None):
    """
    Download an OpenNeuro dataset.
    
    Args:
        dataset_id: The OpenNeuro dataset identifier
        output_dir: Directory to save the downloaded file (default: data/raw)
        
    Raises:
        DataFetchError: If download fails
    """
    if output_dir is None:
        output_dir = RAW_DIR
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    download_url = get_dataset_download_url(dataset_id)
    output_file = output_dir / f"{dataset_id}.tar.gz"
    
    logger.info(f"Downloading dataset {dataset_id} from {download_url}")
    
    try:
        response = requests.get(download_url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Download progress: {progress:.1f}%")
        
        logger.info(f"Download completed: {output_file}")
        return output_file
      
    except requests.RequestException as e:
        raise DataFetchError(f"Failed to download dataset {dataset_id}: {e}")
    except Exception as e:
        raise DataFetchError(f"Error during download of {dataset_id}: {e}")

def process_metadata_and_exclude_subjects(dataset_dir: Path):
    """
    Process dataset metadata and exclude subjects based on diagnostic labels.
    
    Args:
        dataset_dir: Path to the extracted dataset directory
        
    Returns:
        List of excluded subject IDs
    """
    excluded_subjects = []
    exclusion_log_path = METADATA_DIR / "exclusion_log.txt"
    
    # Look for participants.tsv or similar metadata file
    participants_file = dataset_dir / "participants.tsv"
    if not participants_file.exists():
        # Try other common names
        for name in ["participants.csv", "participants.json", "metadata.json"]:
            alt_file = dataset_dir / name
            if alt_file.exists():
                participants_file = alt_file
                break
    
    if not participants_file.exists():
        logger.warning(f"Participants file not found in {dataset_dir}")
        return excluded_subjects
    
    try:
        import pandas as pd
        df = pd.read_csv(participants_file, sep='\t')
        
        # Look for diagnosis column
        diagnosis_col = None
        for col in df.columns:
            if 'diagnosis' in col.lower() or 'group' in col.lower() or 'label' in col.lower():
                diagnosis_col = col
                break
        
        if diagnosis_col is None:
            logger.warning("No diagnosis column found in participants file")
            return excluded_subjects
        
        # Process each subject
        with open(exclusion_log_path, 'w') as log_file:
            log_file.write(f"Exclusion Log - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            log_file.write("=" * 50 + "\n\n")
        
            for idx, row in df.iterrows():
                subject_id = row.get('participant_id', f'sub-{idx}')
                if pd.isna(row.get(diagnosis_col)):
                    excluded_subjects.append(subject_id)
                    log_file.write(f"[{subject_id}] Excluded: Missing diagnostic label\n")
                    logger.info(f"Excluded {subject_id}: Missing diagnostic label")
        
        logger.info(f"Processed metadata: {len(excluded_subjects)} subjects excluded")
        return excluded_subjects
      
    except Exception as e:
        logger.error(f"Error processing metadata: {e}")
        return excluded_subjects

def check_motion_parameters_exist(dataset_dir: Path) -> bool:
    """
    Check if motion parameters exist in the dataset metadata.
    
    Args:
        dataset_dir: Path to the dataset directory
        
    Returns:
        True if motion parameters are found, False otherwise
    """
    # Look for common motion parameter files
    motion_file_patterns = [
        "*confounds*.tsv",
        "*motion*.txt",
        "*motion*.csv",
        "*regressors*.txt",
        "task-*_desc-confounds_timeseries.tsv"
    ]
    
    # Search in dataset directory and subdirectories
    for root, dirs, files in os.walk(dataset_dir):
        for pattern in motion_file_patterns:
            import glob
            matches = glob.glob(os.path.join(root, pattern))
            if matches:
                logger.info(f"Found motion parameters: {matches[0]}")
                return True
    
    logger.info("No motion parameters found in dataset")
    return False

def save_motion_params_check_result(motion_available: bool):
    """
    Save the result of motion parameters check to a JSON file.
    
    Args:
        motion_available: Boolean indicating if motion parameters were found
    """
    output_file = METADATA_DIR / "motion_params_available.json"
    
    result = {
        "motion_params_available": motion_available
    }
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved motion parameters check result to {output_file}")

def run_motion_params_check_pipeline():
    """
    Run the motion parameters check pipeline.
    
    This function:
    1. Checks for the presence of motion parameters in the dataset
    2. Saves the result to data/metadata/motion_params_available.json
    """
    logger.info("Starting motion parameters check pipeline")
    
    # Look for the dataset directory
    dataset_dirs = [d for d in RAW_DIR.iterdir() if d.is_dir() and d.name.startswith("ds")]
    
    if not dataset_dirs:
        logger.warning("No dataset directory found. Assuming motion parameters not available.")
        save_motion_params_check_result(False)
        return False
    
    # Check the first dataset found
    dataset_dir = dataset_dirs[0]
    motion_available = check_motion_parameters_exist(dataset_dir)
    save_motion_params_check_result(motion_available)
    
    return motion_available

def main():
    """Main entry point for the script."""
    try:
        # Example usage: check motion parameters
        motion_available = run_motion_params_check_pipeline()
        logger.info(f"Motion parameters check complete: {motion_available}")
        return 0
    except Exception as e:
        logger.error(f"Motion parameters check failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())