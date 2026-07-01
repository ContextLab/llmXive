"""
Task T015: Ingest raw data from Dryad and AnAge.
Downloads CSVs, applies SHA256 checksums, and saves to data/raw/.
"""
import os
import sys
import hashlib
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import requests
import pandas as pd

# Import from project utilities (API surface provided in prompt)
from utils import generate_checksum, update_state_file
from config import get_config
from logging_config import setup_logging, log_memory_status

# Constants
DRYAD_API_URL = "https://datadryad.org/api/v2/datasets/"
DRYAD_DOWNLOAD_TEMPLATE = "https://datadryad.org/stash/downloads/dataset/{dataset_id}/file/{file_id}"
ANAGE_DATA_URL = "https://api.ouranos.org/anage/birds.csv"  # Direct CSV fetch as per instruction
STATE_FILE_PATH = Path("state/projects/PROJ-055-investigating-the-impact-of-telomere-len.yaml")
DATA_RAW_DIR = Path("data/raw")
LOG_DIR = Path("logs")

logger = setup_logging("ingest")

def load_dataset_ids() -> List[str]:
    """Load discovered Dryad dataset IDs from the previous step."""
    # Assuming T014 saved IDs to a specific file or we derive them from config/state
    # For this task, we assume T014 saved a list of IDs to data/raw/discovered_ids.json
    ids_file = DATA_RAW_DIR / "discovered_ids.json"
    if not ids_file.exists():
        logger.warning(f"Discovered IDs file not found at {ids_file}. Falling back to config or empty.")
        return []
    
    with open(ids_file, 'r') as f:
        data = json.load(f)
    return data.get("dataset_ids", [])

def download_dryad_file(dataset_id: str, file_id: str, output_path: Path) -> bool:
    """
    Download a specific file from Dryad using the API.
    Dryad API requires a two-step process: get dataset metadata -> find file link -> download.
    """
    try:
        # Step 1: Get dataset metadata to find file links
        # Note: Dryad API v2 structure might vary, using generic fetch
        url = f"{DRYAD_API_URL}{dataset_id}/files"
        headers = {"Accept": "application/json"}
        
        logger.info(f"Fetching file metadata for Dryad dataset {dataset_id}...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        files_data = response.json()
        # Dryad API response structure: typically a list of files under a specific key
        # Adjust parsing based on actual API response if known, otherwise generic
        if isinstance(files_data, dict) and "items" in files_data:
            files = files_data["items"]
        elif isinstance(files_data, list):
            files = files_data
        else:
            logger.error(f"Unexpected Dryad API response structure: {files_data}")
            return False

        # Find the specific file or download all if file_id is not specific
        # For this implementation, we assume file_id might be a pattern or we download the main CSV
        target_file = None
        for f in files:
            if isinstance(f, dict):
                # Check if file_id matches or if we just want the first CSV
                if file_id and str(f.get("id", "")) == str(file_id):
                    target_file = f
                    break
                if not file_id and f.get("name", "").lower().endswith(".csv"):
                    target_file = f
                    break
        
        if not target_file:
            # Fallback: try to download the first CSV found
            for f in files:
                if isinstance(f, dict) and f.get("name", "").lower().endswith(".csv"):
                    target_file = f
                    break

        if not target_file:
            logger.error(f"No CSV file found in Dryad dataset {dataset_id}")
            return False

        # Get download URL (Dryad usually provides a 'download_uri' or similar)
        # The API response might contain a 'uri' or we need to construct it
        # Using a common pattern for Dryad direct download
        download_url = target_file.get("download_uri") or target_file.get("uri")
        
        if not download_url:
            # Construct URL if not present (Dryad pattern)
            # This is a heuristic; real implementation might need specific API call
            logger.warning("Download URI not found in metadata, attempting direct construction.")
            return False

        logger.info(f"Downloading {target_file.get('name')} from {download_url}...")
        file_response = requests.get(download_url, timeout=60)
        file_response.raise_for_status()

        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'wb') as f:
            f.write(file_response.content)
        
        logger.info(f"Successfully downloaded to {output_path}")
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download from Dryad: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading Dryad data: {e}")
        return False

def download_anage_data(output_path: Path) -> bool:
    """
    Download AnAge bird data directly via CSV fetch.
    Instruction: Do NOT use rotl for AnAge data.
    """
    try:
        logger.info(f"Downloading AnAge data from {ANAGE_DATA_URL}...")
        response = requests.get(ANAGE_DATA_URL, timeout=60)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        logger.info(f"Successfully downloaded AnAge data to {output_path}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to download AnAge data: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error downloading AnAge data: {e}")
        return False

def verify_checksum(file_path: Path, expected_hash: Optional[str] = None) -> bool:
    """
    Verify the SHA256 checksum of a downloaded file.
    If expected_hash is provided, compare. Otherwise, just generate and log.
    """
    actual_hash = generate_checksum(file_path)
    logger.info(f"Checksum for {file_path.name}: {actual_hash}")
    
    if expected_hash:
        if actual_hash == expected_hash:
            logger.info(f"Checksum verification PASSED for {file_path.name}")
            return True
        else:
            logger.error(f"Checksum verification FAILED for {file_path.name}. Expected: {expected_hash}, Got: {actual_hash}")
            return False
    return True

def main():
    """
    Main execution flow for T015:
    1. Load discovered Dryad dataset IDs.
    2. Download Dryad CSVs.
    3. Download AnAge CSV.
    4. Compute and record SHA256 checksums.
    5. Update state file.
    """
    logger.info("Starting T015: Ingest Data")
    log_memory_status()

    # Ensure directories
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Load Dryad IDs
    dryad_ids = load_dataset_ids()
    if not dryad_ids:
        logger.warning("No Dryad dataset IDs found. Skipping Dryad download.")
    else:
        logger.info(f"Found {len(dryad_ids)} Dryad datasets to process.")
        for dataset_id in dryad_ids:
            # Download logic: assume we download the main CSV for the dataset
            # In a real scenario, we might iterate files. Here we assume one main CSV per dataset.
            output_filename = f"dryad_{dataset_id}.csv"
            output_path = DATA_RAW_DIR / output_filename
            
            # We try to download; if specific file_id is needed, it would be passed or derived
            # For now, we pass None for file_id to trigger auto-detection of first CSV
            success = download_dryad_file(dataset_id, None, output_path)
            
            if success and output_path.exists():
                verify_checksum(output_path)
                # Update state with the new artifact hash
                update_state_file({output_path.name: generate_checksum(output_path)})

    # 2. Download AnAge
    anage_output_path = DATA_RAW_DIR / "anage_birds.csv"
    if not anage_output_path.exists():
        success = download_anage_data(anage_output_path)
        if success:
            verify_checksum(anage_output_path)
            update_state_file({anage_output_path.name: generate_checksum(anage_output_path)})
    else:
        logger.info(f"AnAge file {anage_output_path} already exists. Skipping download.")
        verify_checksum(anage_output_path)
        update_state_file({anage_output_path.name: generate_checksum(anage_output_path)})

    logger.info("T015: Ingest Data completed.")
    log_memory_status()

if __name__ == "__main__":
    main()
