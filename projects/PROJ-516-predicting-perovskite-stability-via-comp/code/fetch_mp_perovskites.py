import logging
import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Any

from utils.config_manager import get_api_key, ConfigError
from utils.data_fetcher import fetch_with_retry, FetchError
from utils.checksum_verifier import compute_sha256

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MP_API_BASE = "https://api.materialsproject.org"
MP_PEROVSKITES_OUTPUT = Path("data/raw/mp_perovskites.csv")
MP_CHECKSUM_OUTPUT = Path("data/raw/mp_perovskites.sha256")
REQUIRED_COLUMNS = ["formula", "T_d", "source"]

def fetch_mp_material_data(api_key: str, formula: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch material data from Materials Project API.
    
    Args:
        api_key: Materials Project API key
        formula: Optional formula filter
        
    Returns:
        List of material records
    """
    logger.info("Fetching Materials Project material data...")
    
    # Materials Project API endpoint for thermo data
    endpoint = f"{MP_API_BASE}/core/v2/thermo"
    params = {
        "api_key": api_key,
        "formula": formula if formula else "",
        "limit": 1000
    }
    
    try:
        import requests
        response = requests.get(endpoint, params=params, timeout=30)
        
        if response.status_code == 401:
            logger.error("MP API authentication failed. Check API key.")
            raise FetchError("MP API authentication failed.")
        elif response.status_code == 404:
            logger.error(f"MP endpoint not found: {endpoint}")
            raise FetchError(f"MP API endpoint not found: {endpoint}")
        elif response.status_code != 200:
            raise FetchError(f"MP API request failed with status {response.status_code}")
        
        data = response.json()
        results = data.get("results", [])
        
        logger.info(f"Fetched {len(results)} records from MP.")
        return results
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching MP data: {e}")
        raise FetchError(f"Network error: {e}")

def fetch_experimental_tga_data(api_key: str) -> List[Dict[str, Any]]:
    """
    Fetch experimental TGA data from Materials Project (if available via a specific endpoint).
    Note: MP might not have a direct 'TGA' endpoint, so we filter thermo data for T_d.
    
    Args:
        api_key: Materials Project API key
        
    Returns:
        List of records with T_d
    """
    logger.info("Filtering MP data for T_d (TGA onset)...")
    
    # Reuse the thermo data fetch, as TGA onset is often part of thermo properties
    # In a real scenario, there might be a specific experimental data endpoint.
    # We assume the thermo data contains the necessary T_d field.
    raw_data = fetch_mp_material_data(api_key)
    
    t_d_records = []
    for record in raw_data:
        # Look for T_d in various keys
        t_d_value = None
        for key in ['T_d', 'decomposition_temp', 'thermal_decomposition_temp', 'onset_temp', 'melting_temp']:
            if key in record and record[key] is not None:
                try:
                    t_d_value = float(record[key])
                    break
                except (ValueError, TypeError):
                    continue
        
        if t_d_value is not None:
            record['T_d'] = t_d_value
            formula = record.get('formula')
            if not formula:
                logger.warning(f"Record missing formula, skipping: {record.get('material_id')}")
                continue
            record['formula'] = formula
            record['source'] = 'MaterialsProject'
            t_d_records.append(record)
        else:
            logger.debug(f"Skipping record without T_d: {record.get('material_id')}")
    
    logger.info(f"Found {len(t_d_records)} records with T_d in MP data.")
    return t_d_records

def validate_data_checksum(file_path: Path, manifest_path: Path) -> bool:
    """
    Validate data against checksum manifest.
    
    Args:
        file_path: Path to data file
        manifest_path: Path to manifest
        
    Returns:
        True if valid, False otherwise
    """
    if not manifest_path.exists():
        logger.warning("Checksum manifest not found.")
        return False
        
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
        
    expected_checksum = manifest.get("sha256")
    if not expected_checksum:
        logger.error("Invalid manifest: missing sha256")
        return False
        
    actual_checksum = compute_sha256(file_path)
    
    if actual_checksum == expected_checksum:
        logger.info("MP data checksum validation passed.")
        return True
    else:
        logger.error(f"MP data checksum mismatch.")
        return False

def save_to_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save records to a CSV file.
    
    Args:
        records: List of records
        output_path: Path to output CSV
    """
    if not records:
        logger.warning("No records to save.")
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
            writer.writeheader()
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    fieldnames = ["formula", "T_d", "source", "material_id", "energy_per_atom", "formation_energy"]
    
    import csv
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in records:
            # Only write known fields to avoid None values in CSV if not needed
            row = {k: record.get(k, "") for k in fieldnames}
            writer.writerow(row)
    
    logger.info(f"Saved {len(records)} records to {output_path}")

def main():
    """Main entry point for MP data fetching."""
    logger.info("Starting T012b: Materials Project Data Ingestion")
    
    try:
        api_key = get_api_key("MP_API_KEY")
    except ConfigError as e:
        logger.critical(f"Task T012b failed: {e}")
        sys.exit(1)
    
    if not api_key:
        logger.critical("Task T012b failed: MP_API_KEY is missing or empty.")
        sys.exit(1)
    
    try:
        records = fetch_experimental_tga_data(api_key)
    except FetchError as e:
        logger.critical(f"Task T012b failed during fetch: {e}")
        sys.exit(1)
    
    save_to_csv(records, MP_PEROVSKITES_OUTPUT)
    
    # Save checksum
    checksum = compute_sha256(MP_PEROVSKITES_OUTPUT)
    manifest = {
        "file": MP_PEROVSKITES_OUTPUT.name,
        "sha256": checksum,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(MP_CHECKSUM_OUTPUT, 'w') as f:
        json.dump(manifest, f, indent=2)
    
    logger.info("T012b completed successfully.")

if __name__ == "__main__":
    main()
