import os
import time
import logging
import json
import requests
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import random

# Import from sibling modules as per API surface
from utils import setup_logging, pin_seed, retry_with_exponential_backoff
from config import get_config, initialize_environment

# Constants
MP_API_URL = "https://next-gen.materialsproject.org/api/v2/materials"
MP_CIF_URL = "https://next-gen.materialsproject.org/api/v2/materials"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 60.0
TIMEOUT = 30

# Set up logging
logger = setup_logging("download", "results/download.log")

def fetch_with_retry_rate_limit(url: str, headers: Dict[str, str], params: Optional[Dict] = None) -> Optional[Dict]:
    """Fetch data from a URL with rate-limiting and retry logic."""
    backoff = INITIAL_BACKOFF
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=TIMEOUT)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait_time = backoff
                logger.warning(f"Rate limited. Waiting {wait_time:.1f}s before retry {attempt + 1}/{MAX_RETRIES}.")
                time.sleep(wait_time)
                backoff = min(backoff * 2, MAX_BACKOFF)
            else:
                logger.error(f"HTTP {response.status_code} for {url}. Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}. Retrying {attempt + 1}/{MAX_RETRIES}...")
            time.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF)
    logger.error(f"Failed to fetch {url} after {MAX_RETRIES} attempts.")
    return None

def fetch_materials_with_thermal_conductivity(api_key: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch a list of materials with thermal conductivity data from Materials Project."""
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    params = {
        "fields": "material_id,thermal_conductivity,structure",
        "thermal_conductivity[exists]": "true",
        "limit": limit
    }
    logger.info(f"Fetching materials with thermal conductivity (limit={limit})...")
    data = fetch_with_retry_rate_limit(MP_API_URL, headers, params)
    if data and "data" in data:
        materials = [m for m in data["data"] if m.get("thermal_conductivity")]
        logger.info(f"Found {len(materials)} materials with thermal conductivity data.")
        return materials
    logger.error("No materials data found or API error occurred.")
    return []

def fetch_cif_content(material_id: str, api_key: str) -> Optional[str]:
    """Fetch CIF content for a specific material ID."""
    headers = {"X-API-Key": api_key, "Accept": "text/x-cif"}
    url = f"{MP_CIF_URL}/{material_id}/cif"
    logger.debug(f"Fetching CIF for {material_id}...")
    try:
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Failed to fetch CIF for {material_id}: HTTP {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching CIF for {material_id}: {e}")
        return None

def download_cif_files(materials: List[Dict[str, Any]], api_key: str, output_dir: str, limit: int = 50) -> int:
    """Download CIF files for given materials to the output directory."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    downloaded_count = 0
    start_time = time.time()
    time_limit = 30 * 60  # 30 minutes in seconds

    logger.info(f"Starting download of CIF files to {output_dir} (limit={limit}, timeout=30min)...")

    for material in materials:
        if downloaded_count >= limit:
            logger.info(f"Reached download limit of {limit}. Stopping.")
            break

        elapsed = time.time() - start_time
        if elapsed > time_limit:
            logger.warning(f"Time limit of 30 minutes reached. Stopping. Downloaded {downloaded_count} files.")
            break

        material_id = material.get("material_id")
        if not material_id:
            logger.warning("Skipping material without material_id.")
            continue

        cif_content = fetch_cif_content(material_id, api_key)
        if cif_content:
            file_path = output_path / f"{material_id}.cif"
            try:
                with open(file_path, "w") as f:
                    f.write(cif_content)
                downloaded_count += 1
                logger.info(f"Downloaded {material_id}.cif ({downloaded_count}/{limit})")
            except IOError as e:
                logger.error(f"Failed to write {material_id}.cif: {e}")
        else:
            logger.warning(f"Skipping {material_id} due to CIF fetch failure.")

    logger.info(f"Download complete. {downloaded_count} files saved in {time.time() - start_time:.1f}s.")
    return downloaded_count

def main():
    """Main entry point for the download script."""
    import argparse

    parser = argparse.ArgumentParser(description="Download CIF files from Materials Project.")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of CIF files to download.")
    parser.add_argument("--output", type=str, default="data/raw/cif/", help="Output directory for CIF files.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility.")
    args = parser.parse_args()

    # Initialize environment and config
    initialize_environment()
    config = get_config()
    pin_seed(args.seed)

    api_key = config.get("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY not found in environment or config. Please set it.")
        return

    # Fetch materials with thermal conductivity
    materials = fetch_materials_with_thermal_conductivity(api_key, limit=args.limit * 2)  # Fetch extra to ensure we get enough
    if not materials:
        logger.error("No materials with thermal conductivity found. Exiting.")
        return

    # Download CIF files
    count = download_cif_files(materials, api_key, args.output, limit=args.limit)
    if count < args.limit:
        logger.warning(f"Only downloaded {count} files, which is less than the requested limit of {args.limit}.")
    else:
        logger.info(f"Successfully downloaded {count} CIF files.")

if __name__ == "__main__":
    main()
