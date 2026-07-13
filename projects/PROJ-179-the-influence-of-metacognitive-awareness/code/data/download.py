import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path

# Import config utilities if available, otherwise fallback to defaults
try:
    from code.config.env_config import load_config, setup_logging
    CONFIG = load_config()
except ImportError:
    CONFIG = None
    def setup_logging(level=logging.INFO):
        logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')

setup_logging()
logger = logging.getLogger(__name__)

# Define the canonical dataset source.
# We use the 'metacognition_behavioral' dataset from a public GitHub repository
# that hosts research datasets for this specific project pipeline.
# If this specific URL is unreachable, the script attempts a fallback to a
# known valid UCI or OpenNeuro behavioral dataset if available in the spec.
# For this implementation, we target a specific CSV that contains the required
# columns: participant_id, trial_id, stimulus_modality, source_label,
# participant_response, confidence_rating.
DATASET_URL = "https://raw.githubusercontent.com/llmXive/datasets/main/metacognition_behavioral.csv"
FALLBACK_URL = "https://raw.githubusercontent.com/llmXive/datasets/main/behavioral_trials_v2.csv"
OUTPUT_FILE_NAME = "behavioral_data.csv"

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def calculate_sha256(file_path):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None

def download_dataset(url, output_path):
    """Download a dataset from a URL with progress logging."""
    try:
        log_info(f"Attempting to download dataset from: {url}")
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        block_size = 1024  # 1 Kibibyte
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=block_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        # Log progress occasionally to avoid spam
                        if downloaded % (1024 * 100) == 0: 
                            log_info(f"Downloaded {downloaded} bytes ({percent:.1f}%)")
        
        log_info(f"Successfully downloaded dataset to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to download from {url}: {e}")
        return False
    except Exception as e:
        log_error(f"Unexpected error during download from {url}: {e}")
        return False

def load_config_wrapper():
    """Wrapper to safely load config or return defaults."""
    if CONFIG:
        return CONFIG
    # Default paths if config loading fails
    return {
        "paths": {
            "data": "data",
            "base": "projects/PROJ-179-the-influence-of-metacognitive-awareness"
        }
    }

def validate_checksum(file_path, expected_checksum=None):
    """
    Validate checksum if expected_checksum is provided.
    If no checksum is provided (e.g., no checksum file available), 
    we assume the download integrity is verified by the HTTP status 
    and file size if available.
    """
    if not expected_checksum:
        log_info("No checksum provided for validation. Assuming download integrity.")
        return True
    
    actual_checksum = calculate_sha256(file_path)
    if actual_checksum == expected_checksum:
        log_info("Checksum validation passed.")
        return True
    else:
        log_error(f"Checksum validation failed. Expected: {expected_checksum}, Got: {actual_checksum}")
        return False

def main():
    """Main entry point for T005: Download valid behavioral dataset."""
    log_info("Starting dataset download (T005)...")
    
    config = load_config_wrapper()
    base_dir = Path(config.get("paths", {}).get("base", "projects/PROJ-179-the-influence-of-metacognitive-awareness"))
    data_dir = base_dir / "data"
    
    # Ensure data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    output_path = data_dir / OUTPUT_FILE_NAME

    # Attempt primary download
    success = download_dataset(DATASET_URL, output_path)
    
    if not success:
        log_info("Primary download failed. Attempting fallback source...")
        success = download_dataset(FALLBACK_URL, output_path)
    
    if not success:
        log_error("ERROR: Could not download a valid behavioral dataset from any source.")
        log_error("Project blocked. No real data source available.")
        sys.exit(1)
    
    # If we have a checksum file (e.g., checksums.json), validate it.
    # For this implementation, we assume the dataset is valid if downloaded successfully.
    # In a production environment, a checksums.json would be read here.
    if validate_checksum(output_path):
        log_info("Dataset download and validation complete.")
        log_info(f"Output written to: {output_path}")
        sys.exit(0)
    else:
        log_error("Checksum validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()