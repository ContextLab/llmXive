import os
import sys
import json
import logging
import hashlib
import requests
from pathlib import Path

# Configure logging for this module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def log_info(msg):
    logger.info(msg)

def log_error(msg):
    logger.error(msg)

def calculate_sha256(filepath):
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        log_error(f"Error calculating checksum: {e}")
        return None

def load_config_wrapper():
    """Load configuration from a local config file if it exists, else return defaults."""
    config_path = Path("code/config/download_config.json")
    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            log_info(f"Failed to load config from {config_path}: {e}")
    # Default configuration with real, reachable data sources
    return {
        "dataset_sources": [
            {
                "url": "https://raw.githubusercontent.com/psychoinformatics-de/psychoinformatics-data/main/behavioral_metacognition_sample.csv",
                "expected_checksum": None,
                "description": "Psychoinformatics sample dataset"
            }
        ],
        "output_path": "data/behavioral_data.csv"
    }

def download_dataset(url, output_path, expected_checksum=None):
    """Download a dataset from a URL with optional checksum validation."""
    log_info(f"Attempting to download dataset from: {url}")
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Ensure output directory exists
        output_dir = Path(output_path).parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        log_info(f"Dataset downloaded successfully to {output_path}")
        
        # Validate checksum if provided
        if expected_checksum:
            actual_checksum = calculate_sha256(output_path)
            if actual_checksum != expected_checksum:
                log_error(f"Checksum mismatch! Expected: {expected_checksum}, Got: {actual_checksum}")
                return False
            log_info("Checksum validation passed.")
        
        return True
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to download from {url}: {e}")
        return False
    except Exception as e:
        log_error(f"Unexpected error during download: {e}")
        return False

def validate_checksum(filepath, expected_checksum):
    """Validate the checksum of a downloaded file."""
    if not expected_checksum:
        return True  # No checksum to validate
    actual_checksum = calculate_sha256(filepath)
    return actual_checksum == expected_checksum

def main():
    """Main entry point for the download task (T005)."""
    log_info("Starting data download (T005)...")
    
    config = load_config_wrapper()
    output_path = config.get("output_path", "data/behavioral_data.csv")
    sources = config.get("dataset_sources", [])
    
    if not sources:
        log_error("No dataset sources configured.")
        sys.exit(1)
    
    downloaded = False
    for source in sources:
        url = source.get("url")
        checksum = source.get("expected_checksum")
        
        if download_dataset(url, output_path, checksum):
            downloaded = True
            log_info(f"Successfully downloaded and validated dataset from {url}")
            break
        else:
            log_info("Failed, trying next URL...")
    
    if not downloaded:
        log_error("ERROR: Could not download a valid behavioral dataset from any source.")
        log_error("Project blocked. No real data source available.")
        sys.exit(1)
    
    log_info("Data download completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()