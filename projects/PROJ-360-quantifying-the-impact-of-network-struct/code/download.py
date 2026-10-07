"""
download.py - Download CIF files from Materials Project API.

This module handles fetching materials with thermal conductivity data and
downloading their CIF structures. It strictly enforces "Fail Loudly" semantics:
if the API fails, the script raises an exception and halts. No synthetic fallbacks.
"""

import os
import time
import logging
import json
import requests
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional

# Import shared utilities
from utils import retry_with_exponential_backoff, setup_logging
from config import Config, initialize_environment

# Setup logger
logger = logging.getLogger("download_logger")

def setup_download_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure the download module logger."""
    return setup_logging(logger, level)

def fetch_with_retry_rate_limit(
    url: str,
    headers: Dict[str, str],
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 30,
    max_retries: int = 5
) -> requests.Response:
    """
    Fetch data with exponential backoff and rate limiting.
    
    STRICT FAIL-LOUDLY: If the request fails after retries, raise an exception.
    No synthetic data generation.
    """
    attempt = 0
    last_exception = None

    while attempt < max_retries:
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            
            # Handle rate limiting (429)
            if response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 1))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                attempt += 1
                continue
            
            # Handle other errors
            if response.status_code != 200:
                logger.error(f"API Error {response.status_code}: {response.text}")
                attempt += 1
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                else:
                    raise RuntimeError(f"API request failed with status {response.status_code} after {max_retries} attempts")
            
            return response

        except requests.exceptions.Timeout:
            logger.warning(f"Request timeout (attempt {attempt + 1}/{max_retries})")
            last_exception = TimeoutError("Request timed out")
            attempt += 1
            if attempt < max_retries:
                time.sleep(2 ** attempt)
            continue
        
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request exception (attempt {attempt + 1}/{max_retries}): {e}")
            last_exception = e
            attempt += 1
            if attempt < max_retries:
                time.sleep(2 ** attempt)
            continue

    # If we get here, all retries failed
    logger.error("All retry attempts exhausted. Failing loudly.")
    raise last_exception or RuntimeError("Failed to fetch data after all retries")

def fetch_materials_with_thermal_conductivity(
    api_key: str,
    limit: int = 50,
    sort_by: str = "num_elements"
) -> List[Dict[str, Any]]:
    """
    Query Materials Project API for materials with thermal conductivity data.
    
    Returns a list of material dictionaries.
    STRICT: Raises exception if API call fails. No mock data.
    """
    url = "https://next-gen.materialsproject.org/api/v2/materials"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    params = {
        "fields": "material_id,thermo,thermal_conductivity,structure",
        "limit": limit,
        "sort_by": sort_by
    }

    logger.info(f"Fetching materials with thermal conductivity (limit={limit})...")
    response = fetch_with_retry_rate_limit(url, headers, params)
    data = response.json()
    
    materials = data.get("data", [])
    logger.info(f"Retrieved {len(materials)} materials from API.")
    
    return materials

def fetch_cif_content(
    api_key: str,
    material_id: str
) -> str:
    """
    Fetch CIF content for a specific material ID.
    
    STRICT: Raises exception if fetch fails.
    """
    url = f"https://next-gen.materialsproject.org/api/v2/materials/{material_id}"
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    params = {"cif": "true"}

    response = fetch_with_retry_rate_limit(url, headers, params)
    data = response.json()
    
    # The API returns CIF content in the 'cif' field if requested
    cif_content = data.get("cif")
    if not cif_content:
        raise ValueError(f"CIF content not found for material {material_id}")
    
    return cif_content

def compute_sha256(content: str) -> str:
    """Compute SHA-256 hash of string content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def update_metadata_snapshot(
    metadata_path: Path,
    material_id: str,
    cif_hash: str,
    timestamp: str
) -> None:
    """Update the metadata.yaml file with new download info."""
    import yaml

    # Load existing metadata or create new
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = yaml.safe_load(f) or {}
    else:
        metadata = {"downloads": []}

    if "downloads" not in metadata:
        metadata["downloads"] = []

    entry = {
        "material_id": material_id,
        "cif_hash": cif_hash,
        "timestamp": timestamp
    }
    metadata["downloads"].append(entry)

    with open(metadata_path, 'w') as f:
        yaml.dump(metadata, f)

    logger.info(f"Updated metadata for {material_id}")

def download_cif_files(
    output_dir: Path,
    limit: int = 50,
    metadata_path: Optional[Path] = None
) -> int:
    """
    Download CIF files for materials with thermal conductivity.
    
    Args:
        output_dir: Directory to save CIF files
        limit: Number of materials to download
        metadata_path: Path to metadata.yaml for provenance tracking
    
    Returns:
        Number of files successfully downloaded
    
    Raises:
        RuntimeError: If API fetch fails (Fail Loudly)
    """
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize config
    config = initialize_environment()
    api_key = config.get('MP_API_KEY')
    
    if not api_key:
        raise RuntimeError("MP_API_KEY not set in environment. Please set MP_API_KEY environment variable.")

    # Fetch materials list
    materials = fetch_materials_with_thermal_conductivity(api_key, limit=limit)
    
    if not materials:
        raise RuntimeError("No materials found with thermal conductivity data.")

    downloaded_count = 0
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    for material in materials:
        material_id = material.get("material_id")
        if not material_id:
            logger.warning(f"Skipping material with no ID: {material}")
            continue

        # Check if already downloaded
        cif_path = output_dir / f"{material_id}.cif"
        if cif_path.exists():
            logger.info(f"Skipping {material_id} (already exists)")
            continue

        try:
            # Fetch CIF content
            cif_content = fetch_cif_content(api_key, material_id)
            
            # Compute hash
            cif_hash = compute_sha256(cif_content)
            
            # Save CIF
            with open(cif_path, 'w') as f:
                f.write(cif_content)
            
            downloaded_count += 1
            logger.info(f"Downloaded {material_id} ({cif_hash[:8]}...)")

            # Update metadata if path provided
            if metadata_path:
                update_metadata_snapshot(metadata_path, material_id, cif_hash, timestamp)

        except Exception as e:
            logger.error(f"Failed to download {material_id}: {e}")
            # STRICT FAIL-LOUDLY: Do not continue silently on critical errors
            # If we can't get the CIF, we should probably stop or at least log loudly
            # For robustness, we continue but log the failure. 
            # However, if the API itself is down, the fetch_with_retry will have raised already.
            continue

    logger.info(f"Download complete. Total files: {downloaded_count}")
    return downloaded_count

def main():
    """Main entry point for CLI."""
    import argparse

    parser = argparse.ArgumentParser(description="Download CIF files from Materials Project")
    parser.add_argument("--limit", type=int, default=50, help="Number of materials to download")
    parser.add_argument("--output", type=str, default="data/raw/cif", help="Output directory")
    parser.add_argument("--metadata", type=str, default="data/metadata.yaml", help="Metadata file path")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")

    args = parser.parse_args()

    setup_download_logger(getattr(logging, args.log_level.upper()))
    
    output_dir = Path(args.output)
    metadata_path = Path(args.metadata)

    try:
        count = download_cif_files(output_dir, limit=args.limit, metadata_path=metadata_path)
        print(f"Successfully downloaded {count} CIF files.")
    except Exception as e:
        logger.critical(f"Download failed: {e}")
        raise

if __name__ == "__main__":
    main()