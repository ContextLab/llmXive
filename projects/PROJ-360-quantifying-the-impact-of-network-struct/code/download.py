import os
import time
import logging
import json
import requests
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

from config import get_config
from utils import retry_with_exponential_backoff, pin_seed

# Setup logging
logger = logging.getLogger("download_logger")

def setup_download_logger():
    """Configure the download logger."""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def fetch_with_retry_rate_limit(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Fetch data from a URL with rate-limiting and retry logic.
    Implements exponential backoff for HTTP 429 and 5xx errors.
    """
    config = get_config()
    retries = 0
    base_delay = 1.0

    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                # Rate limited
                wait_time = base_delay * (2 ** retries)
                logger.warning(f"Rate limited. Waiting {wait_time:.2f}s before retry {retries+1}/{max_retries}")
                time.sleep(wait_time)
                retries += 1
            elif 500 <= response.status_code < 600:
                # Server error
                wait_time = base_delay * (2 ** retries)
                logger.warning(f"Server error {response.status_code}. Waiting {wait_time:.2f}s before retry {retries+1}/{max_retries}")
                time.sleep(wait_time)
                retries += 1
            else:
                # Other error, log and fail
                logger.error(f"Request failed with status {response.status_code}: {response.text[:200]}")
                return None
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            retries += 1
            time.sleep(base_delay * (2 ** retries))

    logger.error(f"Failed to fetch {url} after {max_retries} retries")
    return None

def fetch_materials_with_thermal_conductivity(
    api_key: str,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Fetch materials from Materials Project API that have thermal conductivity data.
    Returns a list of material dictionaries containing material_id and thermal conductivity info.
    """
    base_url = "https://api.materialsproject.org/v2/materials"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Query for materials with thermal conductivity tensor
    # Using the /summary endpoint which includes thermal conductivity if available
    params = {
        "fields": "material_id,thermo,thermal_conductivity",
        "limit": limit,
        "sort_by": "-thermo.form_energy_per_atom"
    }

    url = f"{base_url}/search"
    logger.info(f"Fetching materials with thermal conductivity from {url}")
    
    data = fetch_with_retry_rate_limit(url, headers, params)
    
    if not data or "data" not in data:
        logger.error("No data returned from Materials Project API")
        return []

    materials = data.get("data", [])
    valid_materials = []

    for material in materials:
        material_id = material.get("material_id")
        thermo = material.get("thermo", {})
        thermal_cond = material.get("thermal_conductivity")
        
        # Check if thermal conductivity data exists
        if thermal_cond and isinstance(thermal_cond, dict):
            # Verify it has the tensor components
            if all(k in thermal_cond for k in ['k_xx', 'k_yy', 'k_zz']):
                valid_materials.append({
                    "material_id": material_id,
                    "k_xx": thermal_cond.get('k_xx'),
                    "k_yy": thermal_cond.get('k_yy'),
                    "k_zz": thermal_cond.get('k_zz'),
                    "thermo": thermo
                })
            else:
                logger.debug(f"Material {material_id} missing tensor components, skipping")
        elif thermal_cond and isinstance(thermal_cond, list) and len(thermal_cond) >= 3:
            # Handle list format if present
            valid_materials.append({
                "material_id": material_id,
                "k_xx": thermal_cond[0],
                "k_yy": thermal_cond[1],
                "k_zz": thermal_cond[2] if len(thermal_cond) > 2 else thermal_cond[0],
                "thermo": thermo
            })
        else:
            logger.debug(f"Material {material_id} missing thermal conductivity, skipping")

    logger.info(f"Found {len(valid_materials)} materials with thermal conductivity data")
    return valid_materials

def fetch_cif_content(
    material_id: str,
    api_key: str,
    timeout: int = 30
) -> Optional[str]:
    """
    Fetch CIF content for a specific material from Materials Project API.
    Returns the CIF string content or None if failed.
    """
    base_url = "https://api.materialsproject.org/v2/materials"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    # Use the specific material endpoint with cif format
    url = f"{base_url}/{material_id}/cif"
    
    logger.debug(f"Fetching CIF for {material_id}")
    
    # The API returns the CIF directly as text, not JSON
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Failed to fetch CIF for {material_id}: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Exception fetching CIF for {material_id}: {e}")
        return None

def download_cif_files(
    materials: List[Dict[str, Any]],
    output_dir: str,
    limit: int = 50
) -> Tuple[int, List[str]]:
    """
    Download CIF files for the given materials to the output directory.
    Returns the count of successfully downloaded files and a list of material IDs.
    """
    config = get_config()
    api_key = config.get("MP_API_KEY")
    
    if not api_key:
        logger.error("MP_API_KEY not configured. Please set the environment variable.")
        return 0, []

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    downloaded_ids = []
    skipped_count = 0
    downloaded_count = 0

    # Limit the number of materials to process
    materials_to_process = materials[:limit]
    
    logger.info(f"Processing {len(materials_to_process)} materials (limit: {limit})")

    for idx, material in enumerate(materials_to_process):
        material_id = material["material_id"]
        cif_path = output_path / f"{material_id}.cif"
        
        # Skip if already exists
        if cif_path.exists():
            logger.info(f"Skipping {material_id} (already exists)")
            downloaded_ids.append(material_id)
            downloaded_count += 1
            continue

        cif_content = fetch_cif_content(material_id, api_key)
        
        if cif_content:
            try:
                with open(cif_path, 'w', encoding='utf-8') as f:
                    f.write(cif_content)
                downloaded_ids.append(material_id)
                downloaded_count += 1
                logger.info(f"Downloaded {material_id} ({downloaded_count}/{limit})")
            except IOError as e:
                logger.error(f"Failed to write CIF for {material_id}: {e}")
                skipped_count += 1
        else:
            logger.warning(f"Failed to fetch CIF for {material_id}, skipping")
            skipped_count += 1

        # Small delay to be polite to the API
        time.sleep(0.2)

        # Check if we've reached the limit
        if downloaded_count >= limit:
            break

    logger.info(f"Download complete. Success: {downloaded_count}, Skipped: {skipped_count}")
    return downloaded_count, downloaded_ids

def main():
    """Main entry point for downloading CIF files."""
    import argparse

    parser = argparse.ArgumentParser(description="Download CIF files from Materials Project")
    parser.add_argument("--limit", type=int, default=50, help="Number of materials to download")
    parser.add_argument("--output", type=str, default="data/raw/cif/", help="Output directory for CIF files")
    args = parser.parse_args()

    setup_download_logger()
    pin_seed(42)
    
    config = get_config()
    api_key = config.get("MP_API_KEY")
    
    if not api_key:
        logger.error("MP_API_KEY not set in environment. Please set MP_API_KEY environment variable.")
        return 1

    logger.info(f"Starting download process with limit={args.limit}, output={args.output}")
    
    # Fetch materials with thermal conductivity
    materials = fetch_materials_with_thermal_conductivity(api_key, limit=args.limit * 2)
    
    if not materials:
        logger.error("No materials found with thermal conductivity data.")
        return 1

    # Download CIF files
    count, ids = download_cif_files(materials, args.output, limit=args.limit)
    
    if count == 0:
        logger.error("No files were downloaded.")
        return 1

    logger.info(f"Successfully downloaded {count} CIF files.")
    return 0

if __name__ == "__main__":
    exit(main())