import hashlib
import json
import logging
import os
import sys
import time
from pathlib import Path
import requests
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path (relative to where the script is run)
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
CHECKSUMS_FILE = DATA_DIR / "checksums.json"

# Known datasets with their URLs and required columns
DATASETS = [
    {
        "name": "Metacognitive Awareness Behavioral Sample",
        "url": "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv",
        "checksum": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",  # Placeholder, will be updated on first download
        "required_columns": ["participant_id", "trial_id", "stimulus_modality", "source_label", "participant_response", "confidence_rating"],
        "description": "Behavioral dataset with confidence ratings and source labels"
    }
]

def log_info(message):
    logger.info(message)

def log_error(message):
    logger.error(message)

def calculate_sha256(file_path):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_checksums():
    """Load existing checksums from file."""
    if CHECKSUMS_FILE.exists():
        with open(CHECKSUMS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_checksums(checksums):
    """Save checksums to file."""
    with open(CHECKSUMS_FILE, "w") as f:
        json.dump(checksums, f, indent=2)

def validate_checksum(file_path, expected_checksum):
    """Validate file checksum."""
    if not expected_checksum:
        return True  # Skip validation if no checksum provided
    actual_checksum = calculate_sha256(file_path)
    return actual_checksum == expected_checksum

def check_required_columns(df, required_columns):
    """Check if DataFrame has required columns."""
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return False, missing
    return True, []

def download_dataset(url, output_path):
    """Download dataset from URL."""
    try:
        log_info(f"Attempting to download from: {url}")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save the file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        log_info(f"Successfully downloaded to: {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to download from {url}: {e}")
        return False
    except Exception as e:
        log_error(f"Unexpected error during download: {e}")
        return False

def load_and_validate_dataset(file_path):
    """Load and validate a dataset."""
    try:
        df = pd.read_csv(file_path)
        
        # Check for required columns
        dataset_info = next((d for d in DATASETS if d["name"] in str(file_path)), None)
        if dataset_info:
            required_cols = dataset_info["required_columns"]
            valid, missing = check_required_columns(df, required_cols)
            if not valid:
                log_error(f"Missing required columns: {missing}")
                return None
        
        log_info(f"Successfully loaded dataset with {len(df)} rows and {len(df.columns)} columns")
        return df
    except Exception as e:
        log_error(f"Failed to load dataset: {e}")
        return None

def main():
    """Main function to download and validate behavioral dataset."""
    log_info("Starting data download (T005)...")
    
    # Ensure data directories exist
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Try to download each known dataset
    downloaded = False
    for dataset in DATASETS:
        output_file = RAW_DATA_DIR / f"{dataset['name'].replace(' ', '_').lower()}.csv"
        
        # Check if file already exists and is valid
        if output_file.exists():
            log_info(f"Found existing file: {output_file}")
            df = load_and_validate_dataset(output_file)
            if df is not None:
                log_info(f"Using existing valid dataset: {dataset['name']}")
                downloaded = True
                break
        
        # Attempt download
        if download_dataset(dataset["url"], output_file):
            # Validate downloaded file
            df = load_and_validate_dataset(output_file)
            if df is not None:
                log_info(f"Successfully downloaded and validated: {dataset['name']}")
                downloaded = True
                
                # Update checksum
                checksums = load_checksums()
                checksums[dataset["name"]] = calculate_sha256(output_file)
                save_checksums(checksums)
                break
            else:
                log_error(f"Downloaded file is invalid: {dataset['name']}")
                output_file.unlink()  # Remove invalid file
        
        log_info(f"Failed to download: {dataset['name']}")
    
    if not downloaded:
        log_error("Failed to download and validate any known behavioral dataset.")
        log_error("Project cannot proceed without valid behavioral data.")
        sys.exit(1)
    
    log_info("Data download completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()