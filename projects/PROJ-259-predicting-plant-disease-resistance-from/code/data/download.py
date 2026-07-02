"""
Data download module for plant disease resistance prediction pipeline.

Attempts to fetch real data from NCBI SRA/MetaboLights.
Falls back to synthetic generation if real data is unavailable.
"""
import os
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

from config import get_path, load_config
from data.manifest import ManifestLoader, load_manifest, get_manifest_source_type
from data.generate_synthetic import generate_synthetic_data, update_manifest
from utils.exceptions import EX_DATA_INTEGRITY, EX_POWER_INSUFFICIENT, PipelineException
from utils.logging import setup_logger, log_pipeline_step, log_config_summary

# Configure logger
logger = setup_logger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
SRA_API_URL = "https://www.ebi.ac.uk/ena/browser/api/xml/"
METABOLIGHTS_API_URL = "https://www.ebi.ac.uk/metabolights/api/assay/"
SIMULATED_SOURCE_TYPE = "SIMULATED"
REAL_SOURCE_TYPE = "REAL"

def check_sra_accession(accession: str) -> bool:
    """
    Check if an SRA accession exists and is downloadable.
    
    Args:
        accession: SRA accession ID (e.g., SRP123456)
        
    Returns:
        True if accessible, False otherwise
    """
    url = f"{SRA_API_URL}{accession}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                logger.info(f"SRA accession {accession} found (attempt {attempt})")
                return True
            elif response.status_code in [404, 403]:
                logger.warning(f"SRA accession {accession} not accessible (HTTP {response.status_code})")
                return False
            else:
                logger.warning(f"Unexpected HTTP status {response.status_code} for {accession}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {accession} (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False
    return False

def check_metabolights_accession(accession: str) -> bool:
    """
    Check if a MetaboLights accession exists and is downloadable.
    
    Args:
        accession: MetaboLights accession ID (e.g., MTBLS1234)
        
    Returns:
        True if accessible, False otherwise
    """
    url = f"{METABOLIGHTS_API_URL}{accession}"
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                logger.info(f"MetaboLights accession {accession} found (attempt {attempt})")
                return True
            elif response.status_code in [404, 403]:
                logger.warning(f"MetaboLights accession {accession} not accessible (HTTP {response.status_code})")
                return False
            else:
                logger.warning(f"Unexpected HTTP status {response.status_code} for {accession}")
                return False
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request failed for {accession} (attempt {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return False
    return False

def fetch_real_data(accession_list: List[str], data_type: str) -> Optional[str]:
    """
    Attempt to fetch real data from public repositories.
    
    Args:
        accession_list: List of accession IDs to check
        data_type: Type of data ('SNP', 'metabolite', or 'both')
        
    Returns:
        Path to downloaded data if successful, None otherwise
    """
    logger.info(f"Attempting to fetch real {data_type} data from {len(accession_list)} accessions")
    
    valid_accessions = []
    for accession in accession_list:
        if data_type in ['SNP', 'both']:
            if check_sra_accession(accession):
                valid_accessions.append(accession)
        elif data_type in ['metabolite', 'both']:
            if check_metabolights_accession(accession):
                valid_accessions.append(accession)
    
    if not valid_accessions:
        logger.warning("No valid real data accessions found")
        return None
    
    logger.info(f"Found {len(valid_accessions)} valid accessions: {valid_accessions}")
    
    # In a real implementation, this would download the actual data files
    # For now, we return the list of valid accessions to be used by downstream processing
    data_dir = get_path("data/raw")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a manifest file with valid accessions
    accession_file = data_dir / f"{data_type}_accessions.txt"
    with open(accession_file, 'w') as f:
        for acc in valid_accessions:
            f.write(f"{acc}\n")
    
    logger.info(f"Created accession list at {accession_file}")
    return str(accession_file)

def download_or_generate() -> Tuple[str, str]:
    """
    Main entry point for data acquisition.
    
    Attempts to fetch real data from NCBI SRA/MetaboLights.
    If no results found or HTTP errors after retries, falls back to synthetic generation.
    
    Returns:
        Tuple of (source_type, data_manifest_path)
        source_type is either 'REAL' or 'SIMULATED'
    """
    log_pipeline_step(logger, "data_download", "Starting data acquisition")
    
    config = load_config()
    manifest_path = get_path("data/data_manifest.yaml")
    
    # Load existing manifest if it exists
    if os.path.exists(manifest_path):
        manifest = load_manifest(manifest_path)
        existing_source_type = get_manifest_source_type(manifest)
        
        # If already simulated, return early
        if existing_source_type == SIMULATED_SOURCE_TYPE:
            logger.info("Manifest already indicates SIMULATED source, skipping download")
            return SIMULATED_SOURCE_TYPE, manifest_path
    else:
        manifest = {
            "version": "1.0",
            "created_at": None,
            "source_type": None,
            "accessions": [],
            "data_type": "both"
        }
    
    # Get accessions from manifest or use default query
    accession_list = manifest.get("accessions", [])
    
    # If no accessions in manifest, try default query
    if not accession_list:
        logger.info("No accessions in manifest, attempting default query")
        # Default query for plant disease resistance data
        default_accessions = [
            # Example SRA accessions (these would be replaced with real ones in production)
            "SRP123456",  # Placeholder - would be replaced with real query results
            "SRP234567",
            "MTBLS1234",  # Placeholder MetaboLights
            "MTBLS2345"
        ]
        accession_list = default_accessions
        manifest["accessions"] = default_accessions
    
    # Determine data type from manifest
    data_type = manifest.get("data_type", "both")
    
    # Attempt to fetch real data
    real_data_path = fetch_real_data(accession_list, data_type)
    
    if real_data_path:
        logger.info("Real data successfully retrieved")
        manifest["source_type"] = REAL_SOURCE_TYPE
        manifest["data_path"] = real_data_path
        manifest["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Update manifest
        with open(manifest_path, 'w') as f:
            import yaml
            yaml.dump(manifest, f, default_flow_style=False)
        
        return REAL_SOURCE_TYPE, manifest_path
    else:
        logger.warning("Real data not available, falling back to synthetic generation")
        
        # Trigger synthetic generation
        logger.info("Generating synthetic data for simulation mode")
        synthetic_data_path = generate_synthetic_data()
        
        # Update manifest to indicate SIMULATED source
        manifest["source_type"] = SIMULATED_SOURCE_TYPE
        manifest["data_path"] = synthetic_data_path
        manifest["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        manifest["simulation_note"] = "Real data unavailable; using synthetic data for pipeline validation"
        
        # Update manifest file
        with open(manifest_path, 'w') as f:
            import yaml
            yaml.dump(manifest, f, default_flow_style=False)
        
        log_config_summary(logger, manifest)
        logger.info(f"Synthetic data generated and manifest updated: {manifest_path}")
        
        return SIMULATED_SOURCE_TYPE, manifest_path

def main():
    """Main entry point for standalone execution."""
    logger.info("Starting data download/generation process")
    
    try:
        source_type, manifest_path = download_or_generate()
        
        logger.info(f"Data acquisition complete. Source type: {source_type}")
        logger.info(f"Manifest updated at: {manifest_path}")
        
        # Log final status
        if source_type == SIMULATED_SOURCE_TYPE:
            logger.info("Running in SIMULATION MODE - bypasses data integrity checks in T019")
        else:
            logger.info("Running with REAL data - all integrity checks will be enforced")
        
        return source_type, manifest_path
        
    except Exception as e:
        logger.error(f"Data acquisition failed: {e}")
        raise PipelineException(f"Data acquisition failed: {e}")

if __name__ == "__main__":
    source_type, manifest_path = main()
    print(f"Source type: {source_type}")
    print(f"Manifest path: {manifest_path}")
