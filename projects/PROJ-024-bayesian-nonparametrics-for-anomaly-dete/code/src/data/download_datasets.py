"""
Dataset Download and Verification Script (T052 + T059)

This script performs two main functions:
1. (T052) Downloads verified datasets (UCI Electricity, Traffic) if the search phase (T052b) succeeded.
2. (T059) Verifies dataset integrity against SHA256 checksums recorded in the state file before processing.

Dependencies:
    - ucimlrepo (for UCI datasets)
    - requests (for direct downloads if needed)
"""

import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/results/download.log')
    ]
)
logger = logging.getLogger(__name__)

# Project root relative to script execution
# The script is expected to run from the project root or code/ directory
# We normalize paths relative to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
STATE_FILE = PROJECT_ROOT / "state" / "projects" / "PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml"
SEARCH_RESULTS_FILE = PROJECT_ROOT / "data" / "processed" / "results" / "search_results.json"
DOWNLOAD_MANIFEST_FILE = PROJECT_ROOT / "data" / "processed" / "results" / "download_manifest.json"

try:
    import yaml
except ImportError:
    logger.error("PyYAML is required. Install with: pip install pyyaml")
    sys.exit(1)

try:
    from ucimlrepo import fetch_ucirepo
except ImportError:
    logger.error("ucimlrepo is required. Install with: pip install ucimlrepo")
    sys.exit(1)


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute SHA256 checksum of a file.
    Reads file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def load_state_file() -> Dict[str, Any]:
    """Load the project state file containing artifact hashes."""
    if not STATE_FILE.exists():
        logger.warning(f"State file not found: {STATE_FILE}")
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {}


def load_checksums_from_state() -> Dict[str, str]:
    """
    Extract dataset checksums from the state file.
    Expected structure: state.artifacts.datasets[filename].checksum
    """
    state = load_state_file()
    checksums = {}
    artifacts = state.get("artifacts", {})
    datasets = artifacts.get("datasets", {})
    for filename, data in datasets.items():
        if isinstance(data, dict) and "checksum" in data:
            checksums[filename] = data["checksum"]
    return checksums


def verify_dataset_integrity(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify a dataset file against its expected checksum.
    Returns True if valid, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"Dataset file missing: {file_path}")
        return False

    logger.info(f"Verifying integrity of {file_path.name}...")
    try:
        actual_checksum = compute_file_checksum(file_path)
        if actual_checksum.lower() == expected_checksum.lower():
            logger.info(f"Checksum verified for {file_path.name}")
            return True
        else:
            logger.error(
                f"Checksum mismatch for {file_path.name}!\n"
                f"  Expected: {expected_checksum}\n"
                f"  Actual:   {actual_checksum}"
            )
            return False
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        return False


def download_electricity_dataset() -> Optional[Path]:
    """
    Download UCI Electricity Load Diagrams dataset.
    Returns path to downloaded file if successful, None otherwise.
    """
    logger.info("Downloading UCI Electricity Load Diagrams dataset...")
    try:
        # Fetch dataset 593 from UCI
        electricity = fetch_ucirepo(id=593)
        data = electricity.data
        variables = electricity.variables

        # Save to CSV
        output_path = DATA_RAW_DIR / "electricity_load_diagrams.csv"
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        data.to_csv(output_path, index=False)
        logger.info(f"Saved Electricity dataset to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download Electricity dataset: {e}")
        return None


def download_traffic_dataset() -> Optional[Path]:
    """
    Download UCI Traffic dataset.
    Returns path to downloaded file if successful, None otherwise.
    """
    logger.info("Downloading UCI Traffic dataset...")
    try:
        # Fetch dataset 215 from UCI (PEMS Traffic)
        traffic = fetch_ucirepo(id=215)
        data = traffic.data
        variables = traffic.variables

        # Save to CSV
        output_path = DATA_RAW_DIR / "traffic_volume.csv"
        DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
        data.to_csv(output_path, index=False)
        logger.info(f"Saved Traffic dataset to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to download Traffic dataset: {e}")
        return None


def download_all_datasets() -> Dict[str, Path]:
    """
    Download all verified datasets.
    Returns a dictionary mapping dataset name to file path.
    """
    downloaded = {}
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Download Electricity
    elec_path = download_electricity_dataset()
    if elec_path:
        downloaded["electricity"] = elec_path

    # Download Traffic
    traffic_path = download_traffic_dataset()
    if traffic_path:
        downloaded["traffic"] = traffic_path

    return downloaded


def check_search_results() -> bool:
    """
    Check if the search phase (T052b) completed successfully.
    Returns True if search_results.json exists and indicates success.
    """
    if not SEARCH_RESULTS_FILE.exists():
        logger.warning(f"Search results file not found: {SEARCH_RESULTS_FILE}")
        return False

    try:
        with open(SEARCH_RESULTS_FILE, "r") as f:
            results = json.load(f)
        status = results.get("status", "").upper()
        if status == "SUCCESS" or status == "VERIFIED":
            return True
        else:
            logger.warning(f"Search status indicates failure: {status}")
            return False
    except Exception as e:
        logger.error(f"Error reading search results: {e}")
        return False


def main():
    """
    Main entry point for the download and verification script.
    1. Check if search phase succeeded.
    2. If yes, download datasets (if not already present).
    3. Verify downloaded datasets against checksums in state file.
    4. Update manifest with verification results.
    """
    logger.info("=" * 60)
    logger.info("Dataset Download and Verification Script (T052 + T059)")
    logger.info("=" * 60)

    # Step 1: Check search results
    if not check_search_results():
        logger.critical("Aborting download. T052b Search failed or not found.")
        # Still create a manifest indicating failure
        manifest = {
            "status": "FAILED",
            "reason": "Search phase (T052b) did not complete successfully",
            "datasets": {}
        }
        with open(DOWNLOAD_MANIFEST_FILE, "w") as f:
            json.dump(manifest, f, indent=2)
        sys.exit(1)

    logger.info("Search phase verified. Proceeding with download/verification.")

    # Step 2: Download datasets if not present
    downloaded_files = {}
    dataset_names = ["electricity", "traffic"]
    
    for name in dataset_names:
        # Check if already downloaded
        if name == "electricity":
            candidate = DATA_RAW_DIR / "electricity_load_diagrams.csv"
        else:
            candidate = DATA_RAW_DIR / "traffic_volume.csv"
        
        if candidate.exists():
            logger.info(f"Dataset {name} already exists at {candidate}")
            downloaded_files[name] = candidate
        else:
            logger.info(f"Downloading dataset {name}...")
            if name == "electricity":
                path = download_electricity_dataset()
            else:
                path = download_traffic_dataset()
            
            if path:
                downloaded_files[name] = path
            else:
                logger.warning(f"Failed to download {name}")

    # Step 3: Verify checksums (T059)
    expected_checksums = load_checksums_from_state()
    verification_results = {}
    all_verified = True

    for name, file_path in downloaded_files.items():
        expected = expected_checksums.get(file_path.name)
        if expected:
            is_valid = verify_dataset_integrity(file_path, expected)
            verification_results[name] = {
                "file": str(file_path),
                "verified": is_valid,
                "expected_checksum": expected
            }
            if not is_valid:
                all_verified = False
        else:
            logger.warning(f"No expected checksum found for {file_path.name} in state file.")
            verification_results[name] = {
                "file": str(file_path),
                "verified": False,
                "reason": "No checksum in state file"
            }
            all_verified = False

    # Step 4: Save manifest
    manifest = {
        "status": "SUCCESS" if all_verified else "VERIFICATION_FAILED",
        "timestamp": str(Path(__file__).stat().st_mtime),
        "datasets": verification_results
    }

    with open(DOWNLOAD_MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)

    if all_verified:
        logger.info("All datasets verified successfully.")
        sys.exit(0)
    else:
        logger.error("Dataset verification failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()