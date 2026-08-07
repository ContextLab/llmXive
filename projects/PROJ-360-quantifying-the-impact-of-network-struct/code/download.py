import os
import time
import logging
import json
import requests
import hashlib
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
import yaml

# Import shared utilities
from utils import retry_with_exponential_backoff, setup_logging
from config import Config

# Setup logger
def setup_download_logger():
    logger = logging.getLogger("download_logger")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

logger = setup_download_logger()

def fetch_with_retry_rate_limit(url: str, headers: Dict[str, str], params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> Optional[Dict[str, Any]]:
    """Fetch data with retry logic and rate limiting."""
    max_retries = 5
    base_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=timeout)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                delay = base_delay * (2 ** attempt)
                logger.warning(f"Rate limited. Waiting {delay}s before retry {attempt + 1}/{max_retries}")
                time.sleep(delay)
                continue
            else:
                logger.error(f"API request failed with status {response.status_code}: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            if attempt == max_retries - 1:
                return None
            time.sleep(base_delay * (2 ** attempt))
    
    return None

def fetch_materials_with_thermal_conductivity(api_key: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Query Materials Project API for materials with thermal conductivity data.
    Returns a list of material dictionaries.
    """
    base_url = "https://api.materialsproject.org/v2/materials"
    headers = {"X-API-Key": api_key}
    
    # Filter for materials with thermal conductivity data
    # Using the thermal_conductivity endpoint filter
    params = {
        "thermal_conductivity": "true",
        "fields": "material_id,nsites,formula,reduced_cell_formula,structure,thermo,thermal_conductivity",
        "sort_by": "-nsites", # Sort by size to get diverse structures
        "limit": limit
    }
    
    logger.info(f"Fetching {limit} materials with thermal conductivity data...")
    data = fetch_with_retry_rate_limit(base_url, headers, params)
    
    if data and "data" in data:
        materials = data.get("data", [])
        logger.info(f"Retrieved {len(materials)} materials.")
        return materials
    
    logger.error("No materials found or API request failed.")
    return []

def fetch_cif_content(api_key: str, material_id: str) -> Optional[str]:
    """Fetch CIF content for a specific material ID."""
    url = f"https://api.materialsproject.org/v2/materials/{material_id}/cif"
    headers = {"X-API-Key": api_key}
    
    data = fetch_with_retry_rate_limit(url, headers)
    if data and "cif" in data:
        return data["cif"]
    return None

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def update_metadata_snapshot(metadata_path: str, material_id: str, cif_path: str, checksum: str, status: str = "raw"):
    """Update the metadata.yaml file with snapshot information."""
    metadata_file = Path(metadata_path)
    
    # Load existing metadata or create new
    if metadata_file.exists():
        with open(metadata_file, 'r') as f:
            try:
                metadata = yaml.safe_load(f) or {}
            except yaml.YAMLError:
                metadata = {}
    else:
        metadata = {
            "project_id": "PROJ-360-quantifying-the-impact-of-network-struct",
            "schema_version": "1.0.0",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "materials": []
        }
    
    # Ensure materials list exists
    if "materials" not in metadata:
        metadata["materials"] = []
    
    # Check if material already exists
    existing_entry = None
    for mat in metadata["materials"]:
        if mat.get("material_id") == material_id:
            existing_entry = mat
            break
    
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    entry = {
        "material_id": material_id,
        "cif_path": cif_path,
        "network_path": None, # Will be updated later
        "snapshot_timestamp": timestamp,
        "status": status,
        "thermal_conductivity": None,
        "notes": "Downloaded from Materials Project API",
        "cif_checksum": checksum,
        "graph_checksum": None
    }
    
    if existing_entry:
        # Update existing entry
        existing_entry.update(entry)
    else:
        metadata["materials"].append(entry)
    
    # Write back to file
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, 'w') as f:
        yaml.dump(metadata, f, default_flow_style=False)
    
    logger.info(f"Updated metadata snapshot for {material_id}")

def download_cif_files(output_dir: str, limit: int = 50, metadata_path: str = "data/metadata.yaml") -> int:
    """
    Download CIF files for materials with thermal conductivity data.
    Returns the number of successfully downloaded files.
    """
    api_key = os.getenv("MP_API_KEY")
    if not api_key:
        logger.error("MP_API_KEY not set in environment. Please set MP_API_KEY environment variable.")
        raise RuntimeError("MP_API_KEY environment variable is missing.")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    materials = fetch_materials_with_thermal_conductivity(api_key, limit)
    
    if not materials:
        logger.error("No materials retrieved from API.")
        return 0
    
    downloaded_count = 0
    
    for material in materials:
        material_id = material.get("material_id")
        if not material_id:
            continue
        
        cif_content = fetch_cif_content(api_key, material_id)
        
        if cif_content:
            file_path = output_path / f"{material_id}.cif"
            with open(file_path, 'w') as f:
                f.write(cif_content)
            
            checksum = compute_sha256(str(file_path))
            
            # Update metadata immediately after download
            update_metadata_snapshot(
                metadata_path,
                material_id,
                str(file_path),
                checksum,
                status="raw"
            )
            
            downloaded_count += 1
            logger.info(f"Downloaded {material_id} ({downloaded_count}/{limit})")
        else:
            logger.warning(f"Failed to download CIF for {material_id}")
    
    logger.info(f"Successfully downloaded {downloaded_count} CIF files.")
    return downloaded_count

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Download CIF files from Materials Project API.")
    parser.add_argument("--limit", type=int, default=50, help="Number of materials to download")
    parser.add_argument("--output", type=str, default="data/raw/cif/", help="Output directory for CIF files")
    parser.add_argument("--metadata", type=str, default="data/metadata.yaml", help="Path to metadata file")
    
    args = parser.parse_args()
    
    try:
        count = download_cif_files(args.output, args.limit, args.metadata)
        logger.info(f"Download complete. {count} files downloaded.")
    except RuntimeError as e:
        logger.error(str(e))
        exit(1)

if __name__ == "__main__":
    main()
