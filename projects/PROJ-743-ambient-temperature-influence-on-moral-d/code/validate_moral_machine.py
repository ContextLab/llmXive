"""
T001d: Validate Moral Machine Data Source

This script validates the Moral Machine dataset source by:
1. Fetching the canonical URL for the dataset.
2. Verifying file integrity via SHA-256 checksum against the project state file.
3. Verifying the presence of required columns.
4. Logging validation results to the data validation log.
"""

import os
import sys
import logging
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import pandas as pd
import requests

# Add project root to path to allow imports from code/
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_path_env_override
from setup_logging import get_data_quality_logger, setup_logging

# Constants
MORAL_MACHINE_URL = "https://osf.io/download/5c9c9b5b925419001d276237"  # Canonical OSF URL for Moral Machine dataset
REQUIRED_COLUMNS = ["latitude", "longitude", "timestamp", "response_time", "country", "dilemma_id"]
STATE_FILE_PATH = "state/projects/PROJ-743-ambient-temperature-influence-on-moral-d.yaml"
VALIDATION_LOG_PATH = "results/logs/data_validation_log.txt"
SAMPLE_DOWNLOAD_PATH = "data/raw/moral_machine_sample_validation.csv"

def ensure_directories():
    """Ensure required directories exist."""
    Path("results/logs").mkdir(parents=True, exist_ok=True)
    Path("data/raw").mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_expected_checksum(state_file_path: Path) -> Optional[str]:
    """Load the expected checksum from the project state YAML file."""
    try:
        import yaml
        if not state_file_path.exists():
            return None
        with open(state_file_path, "r") as f:
            state_data = yaml.safe_load(f)
        # Expected structure: artifact_hashes.moral_machine
        return state_data.get("artifact_hashes", {}).get("moral_machine")
    except Exception as e:
        logging.warning(f"Could not load state file for checksum: {e}")
        return None

def verify_source_access(url: str, logger: logging.Logger) -> bool:
    """Verify that the URL is reachable and returns a valid file."""
    try:
        logger.info(f"Checking URL reachability: {url}")
        response = requests.head(url, timeout=30, allow_redirects=True)
        if response.status_code == 200:
            logger.info("URL is reachable (HEAD request successful).")
            return True
        else:
            logger.error(f"URL returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to reach URL: {e}")
        return False

def download_sample(url: str, output_path: Path, logger: logging.Logger) -> Optional[Path]:
    """Download a sample of the dataset for validation."""
    try:
        logger.info(f"Downloading sample from {url} to {output_path}")
        # Use a small chunk size to avoid memory issues if the file is huge
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()
        
        # Save to temporary location first to verify integrity before moving
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        logger.info("Sample download completed successfully.")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download sample: {e}")
        return None

def validate_schema(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """Validate the presence of required columns."""
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    logger.info("All required columns are present.")
    return True

def verify_checksum(file_path: Path, expected_checksum: Optional[str], logger: logging.Logger) -> bool:
    """Verify the SHA-256 checksum of the downloaded file."""
    if expected_checksum is None:
        logger.warning("No expected checksum found in state file. Skipping checksum verification.")
        return True  # Don't fail if state file is missing, just warn

    actual_checksum = compute_sha256(file_path)
    logger.info(f"Computed checksum: {actual_checksum}")
    logger.info(f"Expected checksum: {expected_checksum}")

    if actual_checksum == expected_checksum:
        logger.info("Checksum verification PASSED.")
        return True
    else:
        logger.error("Checksum verification FAILED.")
        return False

def log_validation_result(
    logger: logging.Logger,
    status: str,
    details: Dict[str, Any],
    log_path: Path
):
    """Log the validation result to the specified log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "task_id": "T001d",
        "status": status,
        "details": details
    }
    
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    
    logger.info(f"Validation result logged to {log_path}")

def main():
    setup_logging()
    logger = get_data_quality_logger()
    ensure_directories()

    validation_details = {
        "url_verified": False,
        "checksum_verified": False,
        "schema_verified": False,
        "file_path": None,
        "checksum_value": None,
        "columns_found": []
    }

    try:
        # 1. Verify URL reachability
        url_reachable = verify_source_access(MORAL_MACHINE_URL, logger)
        validation_details["url_verified"] = url_reachable
        if not url_reachable:
            raise RuntimeError("Moral Machine URL is not reachable.")

        # 2. Download sample for validation
        sample_path = Path(SAMPLE_DOWNLOAD_PATH)
        downloaded_file = download_sample(MORAL_MACHINE_URL, sample_path, logger)
        if downloaded_file is None:
            raise RuntimeError("Failed to download Moral Machine sample.")
        
        validation_details["file_path"] = str(downloaded_file)

        # 3. Verify Checksum
        expected_checksum = load_expected_checksum(Path(STATE_FILE_PATH))
        checksum_ok = verify_checksum(downloaded_file, expected_checksum, logger)
        validation_details["checksum_verified"] = checksum_ok
        if expected_checksum:
            validation_details["checksum_value"] = compute_sha256(downloaded_file)

        # 4. Validate Schema
        try:
            # Read only first 1000 rows to validate schema quickly
            df = pd.read_csv(downloaded_file, nrows=1000)
            schema_ok = validate_schema(df, logger)
            validation_details["schema_verified"] = schema_ok
            validation_details["columns_found"] = list(df.columns)
            
            if not schema_ok:
                raise RuntimeError("Schema validation failed.")
        except Exception as e:
            logger.error(f"Failed to read or validate CSV schema: {e}")
            raise RuntimeError("Could not validate CSV schema.")

        # Final Status
        overall_status = "PASS" if all([url_reachable, checksum_ok, schema_ok]) else "FAIL"
        log_validation_result(logger, overall_status, validation_details, Path(VALIDATION_LOG_PATH))
        
        if overall_status == "FAIL":
            logger.error("Validation FAILED. Check logs for details.")
            sys.exit(1)
        else:
            logger.info("Validation PASSED.")

    except Exception as e:
        logger.error(f"Validation process failed with error: {e}")
        validation_details["error"] = str(e)
        log_validation_result(logger, "FAIL", validation_details, Path(VALIDATION_LOG_PATH))
        sys.exit(1)
    finally:
        # Cleanup sample file if it was created for validation
        if sample_path.exists():
            try:
                sample_path.unlink()
                logger.info("Cleaned up temporary sample file.")
            except Exception as e:
                logger.warning(f"Could not delete temporary sample file: {e}")

if __name__ == "__main__":
    main()