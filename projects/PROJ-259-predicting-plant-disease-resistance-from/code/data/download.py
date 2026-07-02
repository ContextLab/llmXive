"""
Data Download Module for Plant Disease Resistance Project.

Attempts to fetch real data from NCBI SRA and MetaboLights.
Falls back to synthetic generation if real data is unavailable or inaccessible.
"""
import os
import time
import requests
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np

from config import get_path, Config
from data.manifest import load_manifest, save_manifest, add_dataset, update_dataset_status, get_source_type, is_simulation_mode
from utils.logging import get_logger, log_pipeline_step
from data.generate_synthetic import main as generate_synthetic_main, update_manifest as synthetic_update_manifest

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds
DOWNLOAD_QUERY = "plant AND disease resistance AND (SNP OR metabolite)"
SRA_API_URL = "https://www.ebi.ac.uk/ena/browser/api/xml/"
METABOLIGHTS_API_URL = "https://www.ebi.ac.uk/metabolights/api/v2/assays"

logger = get_logger(__name__)

def check_sra_accession(accession: str) -> Optional[Dict[str, Any]]:
    """
    Check if an SRA accession exists and is accessible.
    
    Args:
        accession: SRA accession ID (e.g., SRP123456)
        
    Returns:
        Dictionary with metadata if found, None otherwise.
    """
    url = f"{SRA_API_URL}{accession}"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Simple check for valid XML response
                if "<ExperimentSet" in response.text or "<RunSet" in response.text:
                    return {
                        "accession": accession,
                        "source": "SRA",
                        "status": "found",
                        "url": url
                    }
            elif response.status_code in [404, 403]:
                logger.warning(f"SRA accession {accession} returned {response.status_code}")
                return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for SRA {accession}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            continue
        
        return None
    
    return None

def check_metabolights_accession(accession: str) -> Optional[Dict[str, Any]]:
    """
    Check if a MetaboLights accession exists and is accessible.
    
    Args:
        accession: MetaboLights accession ID (e.g., MTBLS1234)
        
    Returns:
        Dictionary with metadata if found, None otherwise.
    """
    url = f"{METABOLIGHTS_API_URL}/{accession}/download"
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                # Check for valid JSON response with assay info
                data = response.json()
                if "assayAccession" in data or "studyAccession" in data:
                    return {
                        "accession": accession,
                        "source": "MetaboLights",
                        "status": "found",
                        "url": url
                    }
            elif response.status_code in [404, 403]:
                logger.warning(f"MetaboLights accession {accession} returned {response.status_code}")
                return None
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.warning(f"Attempt {attempt + 1}/{MAX_RETRIES} failed for MetaboLights {accession}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            continue
        
        return None
    
    return None

def search_public_databases(query: str) -> List[Dict[str, Any]]:
    """
    Search public databases for plant disease resistance data.
    
    Args:
        query: Search query string
        
    Returns:
        List of found datasets with metadata
    """
    found_datasets = []
    
    # Try to find datasets via simple accession search
    # In a real implementation, this would use NCBI E-utilities or MetaboLights search API
    # For now, we'll attempt common accession patterns or return empty if no direct hits
    
    # Since we don't have a specific list of accessions to check, we'll try a few common patterns
    # or return empty to trigger synthetic generation
    test_accessions = [
        ("SRP000001", "SRA"),
        ("SRP000002", "SRA"),
        ("MTBLS1", "MetaboLights"),
        ("MTBLS2", "MetaboLights"),
    ]
    
    for accession, source in test_accessions:
        if source == "SRA":
            result = check_sra_accession(accession)
        else:
            result = check_metabolights_accession(accession)
        
        if result:
            found_datasets.append(result)
    
    if not found_datasets:
        logger.info(f"No accessible datasets found for query: '{query}'")
    
    return found_datasets

def fetch_data_from_accession(dataset_info: Dict[str, Any]) -> bool:
    """
    Attempt to download data from a specific accession.
    
    Args:
        dataset_info: Dictionary containing accession and source information
        
    Returns:
        True if download successful, False otherwise
    """
    accession = dataset_info["accession"]
    source = dataset_info["source"]
    
    logger.info(f"Attempting to download {source} data for accession {accession}")
    
    # In a real implementation, this would download the actual files
    # For now, we'll simulate the download process and return False
    # to trigger synthetic generation since we can't actually download
    # without proper authentication and large file handling
    
    try:
        # This is a placeholder - real implementation would use:
        # - NCBI SRA Toolkit for SRA data
        # - Direct FTP/HTTP download for MetaboLights
        # For this task, we return False to demonstrate fallback logic
        logger.warning(f"Real download from {source} {accession} not implemented in this task. "
                     "Returning False to trigger synthetic fallback.")
        return False
    except Exception as e:
        logger.error(f"Failed to download {source} data for {accession}: {e}")
        return False

def trigger_synthetic_fallback() -> bool:
    """
    Trigger synthetic data generation as fallback.
    
    Returns:
        True if synthetic generation successful, False otherwise
    """
    logger.info("Triggering synthetic data generation as fallback...")
    try:
        # Call the synthetic generation function
        generate_synthetic_main()
        
        # Update manifest to reflect simulation mode
        manifest_path = get_path("data_manifest.yaml")
        update_manifest = synthetic_update_manifest
        update_manifest(manifest_path, "SIMULATED")
        
        logger.info("Synthetic data generation completed successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to generate synthetic data: {e}")
        return False

def update_manifest_with_download_status(manifest_path: str, datasets: List[Dict[str, Any]], 
                                         success: bool) -> None:
    """
    Update the data manifest with download status.
    
    Args:
        manifest_path: Path to the manifest file
        datasets: List of attempted datasets
        success: Whether download was successful
    """
    try:
        manifest = load_manifest(manifest_path)
        
        for dataset in datasets:
            dataset_id = dataset.get("accession", "unknown")
            source = dataset.get("source", "unknown")
            
            # Add or update dataset entry
            add_dataset(manifest, dataset_id, {
                "source": source,
                "status": "downloaded" if success else "failed",
                "timestamp": pd.Timestamp.now().isoformat()
            })
        
        # Update overall status
        if success:
            update_dataset_status(manifest, "real_data", "SUCCESS")
        else:
            update_dataset_status(manifest, "real_data", "FALLBACK_TO_SYNTHETIC")
        
        save_manifest(manifest, manifest_path)
        
    except Exception as e:
        logger.error(f"Failed to update manifest: {e}")

def main() -> bool:
    """
    Main download function.
    
    Attempts to fetch real data from public databases.
    Falls back to synthetic generation if real data is unavailable.
    
    Returns:
        True if data acquisition successful (real or synthetic), False otherwise
    """
    log_pipeline_step("download", "Starting data download process")
    
    manifest_path = get_path("data_manifest.yaml")
    
    try:
        # Load manifest to check for existing accessions
        manifest = load_manifest(manifest_path)
        
        # Check if we already have accessions listed
        existing_datasets = manifest.get("datasets", [])
        
        if existing_datasets:
            logger.info(f"Found {len(existing_datasets)} existing datasets in manifest")
            # Try to download each existing dataset
            for dataset in existing_datasets:
                accession = dataset.get("accession")
                source = dataset.get("source")
                
                if source == "SRA":
                    result = check_sra_accession(accession)
                elif source == "MetaboLights":
                    result = check_metabolights_accession(accession)
                else:
                    logger.warning(f"Unknown source type: {source}")
                    continue
                
                if result:
                    if fetch_data_from_accession(result):
                        update_manifest_with_download_status(manifest_path, [result], True)
                        log_pipeline_step("download", "Real data download successful")
                        return True
        else:
            logger.info("No existing datasets in manifest, searching public databases...")
            # Search for new datasets
            found_datasets = search_public_databases(DOWNLOAD_QUERY)
            
            if found_datasets:
                logger.info(f"Found {len(found_datasets)} potential datasets")
                for dataset in found_datasets:
                    if fetch_data_from_accession(dataset):
                        update_manifest_with_download_status(manifest_path, [dataset], True)
                        log_pipeline_step("download", "Real data download successful")
                        return True
            else:
                logger.info("No datasets found in public databases")
        
        # If we reach here, real data acquisition failed
        logger.warning("Real data acquisition failed. Triggering synthetic fallback...")
        
        if trigger_synthetic_fallback():
            log_pipeline_step("download", "Synthetic data generation successful (Simulation Mode)")
            return True
        else:
            logger.error("Both real data acquisition and synthetic generation failed")
            return False
            
    except Exception as e:
        logger.error(f"Download process failed: {e}")
        # Try synthetic fallback as last resort
        try:
            if trigger_synthetic_fallback():
                log_pipeline_step("download", "Synthetic data generation successful (Simulation Mode)")
                return True
        except:
            pass
        return False

if __name__ == "__main__":
    success = main()
    if success:
        logger.info("Data download process completed successfully")
        exit(0)
    else:
        logger.error("Data download process failed completely")
        exit(1)
