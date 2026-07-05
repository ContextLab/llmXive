import os
import time
import logging
import json
import requests
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import sys

# Import shared utilities from the project API surface
from utils import setup_logging, pin_seed, retry_with_exponential_backoff
from config import get_config

# Constants
MAX_MATERIALS_TO_DOWNLOAD = 50
TIMEOUT_SECONDS = 30
CIF_DIR = Path("data/raw/cif")
MANIFEST_PATH = Path("data/processed/download_manifest.json")

def fetch_with_retry_rate_limit(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """
    Fetches data from a URL with exponential backoff for rate limits (429) and server errors (5xx).
    Retries: 3 times (1s, 2s, 4s backoff).
    """
    config = get_config()
    max_retries = 3
    backoff_times = [1, 2, 4]
    
    session = requests.Session()
    session.headers.update(headers or {})

    for attempt in range(max_retries):
        try:
            response = session.get(url, params=params, timeout=TIMEOUT_SECONDS)
            
            if response.status_code == 429:
                wait_time = backoff_times[attempt]
                logging.warning(f"Rate limited (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            
            if 500 <= response.status_code < 600:
                wait_time = backoff_times[attempt]
                logging.warning(f"Server error ({response.status_code}). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(backoff_times[attempt])
    
    return None

def fetch_materials_with_thermal_conductivity(api_key: str, limit: int = 1000) -> List[Dict[str, Any]]:
    """
    Queries Materials Project API for materials with thermal conductivity data.
    Returns a list of material dictionaries containing 'material_id', 'thermal_conductivity', etc.
    """
    base_url = "https://next-gen.materialsproject.org/v2/materials"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    params = {
        "fields": "material_id,thermal_conductivity,structure",
        "sort_by": "nsites",
        "limit": limit,
        "has_thermal_conductivity": "true"
    }

    logging.info(f"Fetching materials with thermal conductivity (limit={limit})...")
    data = fetch_with_retry_rate_limit(base_url, params=params, headers=headers)
    
    if not data or "data" not in data:
        logging.error("Failed to retrieve materials list or invalid response structure.")
        return []

    materials = data.get("data", [])
    valid_materials = [
        m for m in materials 
        if m.get("thermal_conductivity") is not None and m.get("material_id")
    ]
    
    logging.info(f"Found {len(valid_materials)} materials with thermal conductivity data.")
    return valid_materials

def fetch_cif_content(api_key: str, material_id: str) -> Optional[str]:
    """
    Fetches the CIF content string for a specific material_id.
    """
    url = f"https://next-gen.materialsproject.org/v2/materials/{material_id}/cif"
    headers = {"X-API-Key": api_key}
    
    # The API returns the CIF content directly as text, not JSON, for this endpoint
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        logging.warning(f"Failed to fetch CIF for {material_id}: {e}")
        return None

def download_cif_files(materials: List[Dict[str, Any]], output_dir: Path, max_files: int = MAX_MATERIALS_TO_DOWNLOAD) -> Tuple[int, List[str]]:
    """
    Downloads CIF files for the given list of materials.
    Saves them to output_dir.
    Returns (count_success, list_of_failed_ids).
    """
    config = get_config()
    api_key = config.get("MP_API_KEY")
    if not api_key:
        logging.error("MP_API_KEY not found in configuration.")
        return 0, []

    output_dir.mkdir(parents=True, exist_ok=True)
    success_count = 0
    failed_ids = []
    start_time = time.time()
    time_limit = 30 * 60  # 30 minutes in seconds

    logging.info(f"Starting download of up to {max_files} CIF files to {output_dir}")

    for material in materials:
        # Check time limit
        elapsed = time.time() - start_time
        if elapsed > time_limit:
            logging.warning(f"Time limit ({time_limit}s) exceeded. Stopping download.")
            break

        if success_count >= max_files:
            break

        mid = material.get("material_id")
        if not mid:
            continue

        # Check if already exists to avoid re-downloading
        cif_path = output_dir / f"{mid}.cif"
        if cif_path.exists():
            logging.debug(f"CIF already exists: {mid}. Skipping.")
            success_count += 1
            continue

        cif_content = fetch_cif_content(api_key, mid)
        if cif_content:
            with open(cif_path, 'w', encoding='utf-8') as f:
                f.write(cif_content)
            success_count += 1
            logging.info(f"Downloaded: {mid} ({success_count}/{max_files})")
        else:
            failed_ids.append(mid)
            logging.warning(f"Skipped (no CIF): {mid}")

    elapsed = time.time() - start_time
    logging.info(f"Download completed. Success: {success_count}, Failed: {len(failed_ids)}. Time: {elapsed:.2f}s")
    return success_count, failed_ids

def main():
    """
    Main entry point for T008: Fetch and save >=50 CIF files.
    """
    # Setup logging
    log_file = Path("logs/download.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    setup_logging(log_file, level=logging.INFO)
    
    # Pin seed for reproducibility (though not strictly needed for download, good practice)
    pin_seed(42)

    config = get_config()
    if not config.get("MP_API_KEY"):
        logging.critical("MP_API_KEY environment variable or config setting is missing. Aborting.")
        return

    # Ensure directories exist
    CIF_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Fetch materials
    # We request more than 50 to account for potential download failures or missing CIFs
    materials = fetch_materials_with_thermal_conductivity(config.get("MP_API_KEY"), limit=200)
    
    if not materials:
        logging.error("No materials found with thermal conductivity data.")
        return

    # Download CIFs
    count, failed = download_cif_files(materials, CIF_DIR, max_files=MAX_MATERIALS_TO_DOWNLOAD)

    # Save manifest
    manifest = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_requested": len(materials),
        "total_downloaded": count,
        "failed_ids": failed,
        "output_directory": str(CIF_DIR),
        "target_count": MAX_MATERIALS_TO_DOWNLOAD
    }

    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    logging.info(f"Manifest saved to {MANIFEST_PATH}")

    if count < MAX_MATERIALS_TO_DOWNLOAD:
        logging.warning(f"Only downloaded {count} files. Target was {MAX_MATERIALS_TO_DOWNLOAD}.")
    else:
        logging.info(f"Successfully downloaded {count} files (>= {MAX_MATERIALS_TO_DOWNLOAD}).")

if __name__ == "__main__":
    main()