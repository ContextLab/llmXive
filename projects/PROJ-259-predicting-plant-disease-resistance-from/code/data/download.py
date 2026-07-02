"""
Data download module for plant disease resistance project.
Attempts to fetch real data from NCBI SRA/MetaboLights; falls back to synthetic generation
if real data is unavailable.
"""
import os
import time
import requests
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from config import get_data_path, get_data_path as get_data_root
from data.manifest import load_manifest, get_source_type, create_default_manifest
from utils.logging import get_logger, log_pipeline_step, log_error_context
from utils.exceptions import PipelineError

logger = get_logger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
QUERY_STRING = "plant AND disease resistance AND (SNP OR metabolite)"
SIMULATED_SOURCE_TYPE = "SIMULATED"
REAL_SOURCE_TYPE = "REAL"

def check_ncbi_sra_accession(accession: str) -> Tuple[bool, str]:
    """
    Check if an accession exists in NCBI SRA.
    Returns (is_valid, message).
    """
    url = f"https://www.ncbi.nlm.nih.gov/sra/?term={accession}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            # Check if the page contains "No results found" or similar
            if "No results found" in response.text or "not found" in response.text.lower():
                return False, f"Accession {accession} not found in NCBI SRA"
            return True, f"Accession {accession} found in NCBI SRA"
        elif response.status_code == 404:
            return False, f"Accession {accession} returned 404 from NCBI SRA"
        elif response.status_code == 403:
            return False, f"Accession {accession} returned 403 from NCBI SRA"
        else:
            return False, f"Accession {accession} returned HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error checking {accession}: {str(e)}"

def check_metabolights_accession(accession: str) -> Tuple[bool, str]:
    """
    Check if an accession exists in MetaboLights.
    Returns (is_valid, message).
    """
    url = f"https://www.ebi.ac.uk/metabolights/api/studies/{accession}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return True, f"Accession {accession} found in MetaboLights"
        elif response.status_code == 404:
            return False, f"Accession {accession} returned 404 from MetaboLights"
        elif response.status_code == 403:
            return False, f"Accession {accession} returned 403 from MetaboLights"
        else:
            return False, f"Accession {accession} returned HTTP {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error checking {accession}: {str(e)}"

def fetch_real_data(accession: str, modality: str, max_retries: int = MAX_RETRIES) -> Tuple[bool, str]:
    """
    Attempt to fetch real data for a given accession with retries.
    Returns (success, message).
    """
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        logger.info(f"Attempt {attempt}/{max_retries} to fetch accession {accession} ({modality})")
        
        if modality == "SNP":
            success, message = check_ncbi_sra_accession(accession)
        elif modality == "metabolite":
            success, message = check_metabolights_accession(accession)
        else:
            success, message = False, f"Unknown modality: {modality}"
        
        if success:
            logger.info(message)
            return True, message
        
        last_error = message
        logger.warning(f"Attempt {attempt} failed: {message}")
        
        if attempt < max_retries:
            logger.info(f"Retrying in {RETRY_DELAY} seconds...")
            time.sleep(RETRY_DELAY)
    
    return False, f"All {max_retries} attempts failed for {accession}: {last_error}"

def download_real_data(manifest_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Attempt to download real data based on manifest entries.
    Returns (success, message).
    """
    if manifest_path is None:
        manifest_path = get_data_root() / "data_manifest.yaml"
    
    if not manifest_path.exists():
        logger.warning(f"Manifest not found at {manifest_path}, creating default")
        create_default_manifest(manifest_path)
    
    manifest = load_manifest(manifest_path)
    datasets = manifest.get("datasets", [])
    
    if not datasets:
        logger.warning("No datasets found in manifest")
        return False, "No datasets in manifest"
    
    all_success = True
    failed_accessions = []
    
    for dataset in datasets:
        accession = dataset.get("accession")
        modality = dataset.get("modality")
        
        if not accession or not modality:
            logger.warning(f"Skipping dataset with missing accession or modality: {dataset}")
            continue
        
        success, message = fetch_real_data(accession, modality)
        
        if success:
            logger.info(f"Successfully verified data for {accession}: {message}")
        else:
            logger.error(f"Failed to verify data for {accession}: {message}")
            all_success = False
            failed_accessions.append(accession)
    
    if all_success:
        return True, "All real data accessions verified successfully"
    else:
        return False, f"Failed to verify data for accessions: {', '.join(failed_accessions)}"

def trigger_synthetic_fallback(manifest_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Trigger synthetic data generation as a fallback.
    Returns (success, message).
    """
    logger.info("Triggering synthetic data generation fallback")
    
    try:
        # Import the synthetic generation module
        from data.generate_synthetic import generate_synthetic_data
        
        if manifest_path is None:
            manifest_path = get_data_root() / "data_manifest.yaml"
        
        # Generate synthetic data
        success, message = generate_synthetic_data(manifest_path)
        
        if success:
            logger.info(f"Synthetic data generated successfully: {message}")
            # Update manifest to indicate SIMULATED source
            manifest = load_manifest(manifest_path)
            manifest["source_type"] = SIMULATED_SOURCE_TYPE
            manifest["generation_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            manifest["fallback_reason"] = "Real data fetch failed"
            
            with open(manifest_path, 'w') as f:
                yaml.dump(manifest, f, default_flow_style=False)
            
            return True, "Synthetic data generated and manifest updated"
        else:
            return False, f"Synthetic data generation failed: {message}"
            
    except ImportError as e:
        return False, f"Cannot import synthetic generation module: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error during synthetic fallback: {str(e)}"

def run_download_pipeline(manifest_path: Optional[Path] = None) -> Tuple[bool, str]:
    """
    Main pipeline function to attempt real data download with synthetic fallback.
    Returns (success, message).
    """
    log_pipeline_step("download", "Starting data download pipeline")
    
    if manifest_path is None:
        manifest_path = get_data_root() / "data_manifest.yaml"
    
    # First, try to download real data
    logger.info("Attempting to fetch real data from NCBI SRA/MetaboLights")
    success, message = download_real_data(manifest_path)
    
    if success:
        # Update manifest to indicate REAL source
        manifest = load_manifest(manifest_path)
        manifest["source_type"] = REAL_SOURCE_TYPE
        manifest["generation_timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        
        with open(manifest_path, 'w') as f:
            yaml.dump(manifest, f, default_flow_style=False)
        
        log_pipeline_step("download", f"Real data download successful: {message}")
        return True, message
    
    logger.warning(f"Real data fetch failed: {message}")
    logger.info("Triggering synthetic data fallback")
    
    # Fallback to synthetic generation
    success, message = trigger_synthetic_fallback(manifest_path)
    
    if success:
        log_pipeline_step("download", f"Synthetic fallback successful: {message}")
        return True, message
    else:
        log_error_context("download", "Both real data fetch and synthetic fallback failed", error=message)
        return False, message

def main():
    """
    Entry point for the download script.
    """
    logger.info("Running data download script")
    
    success, message = run_download_pipeline()
    
    if success:
        logger.info(f"Download pipeline completed successfully: {message}")
        return 0
    else:
        logger.error(f"Download pipeline failed: {message}")
        return 1

if __name__ == "__main__":
    exit(main())
