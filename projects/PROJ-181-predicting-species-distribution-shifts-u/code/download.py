"""
Data Download Module for Species Distribution Modeling.

Handles fetching occurrence data from GBIF and climate data from WorldClim/CMIP6.
Integrates with manifest_manager.py to track all downloads.
"""
import os
import time
import logging
import json
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import csv
import urllib.parse

from config import DATA_DIR, PROJECT_ROOT
from manifest_manager import update_manifest, compute_sha256, verify_dataset
from logging_config import get_download_logger

logger = get_download_logger()


def fetch_gbif_occurrences(
    species_list: List[str],
    year_start: int,
    year_end: int,
    output_path: Path,
    api_key: Optional[str] = None
) -> None:
    """
    Fetch occurrence data from GBIF API for specified species and year range.
    
    Args:
        species_list: List of species scientific names
        year_start: Start year for occurrence records
        year_end: End year for occurrence records
        output_path: Path to save the output CSV
        api_key: GBIF API key (optional, can be set via env variable)
    """
    gbif_api_key = api_key or os.getenv("GBIF_API_KEY")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    all_records = []
    
    for species in species_list:
        logger.info(f"Fetching occurrences for {species} ({year_start}-{year_end})")
        
        base_url = "https://api.gbif.org/v1/occurrence/search"
        params = {
            "scientificName": species,
            "year": f"{year_start},{year_end}",
            "hasCoordinate": "true",
            "limit": 300,
            "offset": 0
        }
        
        if gbif_api_key:
            params["key"] = gbif_api_key
        
        total_count = None
        fetched_count = 0
        
        while True:
            try:
                response = requests.get(base_url, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                if not results:
                    break
                
                for record in results:
                    mapped_record = {
                        "species": record.get("scientificName", ""),
                        "decimalLatitude": record.get("decimalLatitude"),
                        "decimalLongitude": record.get("decimalLongitude"),
                        "eventDate": record.get("eventDate", ""),
                        "source_identifier": record.get("basisOfRecord", ""),
                        "download_timestamp": datetime.utcnow().isoformat(),
                        "original_dataset_name": record.get("datasetKey", "")
                    }
                    all_records.append(mapped_record)
                    fetched_count += 1
                
                total_count = data.get("endOfRecords", False)
                if total_count:
                    break
                
                params["offset"] += params["limit"]
                time.sleep(1)  # Rate limiting
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data for {species}: {e}")
                raise
        
        logger.info(f"Fetched {fetched_count} records for {species}")
    
    # Write to CSV
    if all_records:
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                "species", "decimalLatitude", "decimalLongitude", 
                "eventDate", "source_identifier", "download_timestamp",
                "original_dataset_name"
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_records)
        
        logger.info(f"Saved {len(all_records)} records to {output_path}")
        
        # Update manifest
        update_manifest(
            dataset_name=f"occurrence_{year_start}_{year_end}",
            file_path=str(output_path.relative_to(PROJECT_ROOT)),
            source_url="https://api.gbif.org/v1/occurrence/search",
            dataset_type="occurrence",
            description=f"GBIF occurrence records for {', '.join(species_list)} from {year_start}-{year_end}"
        )
    else:
        logger.warning(f"No records found for {species_list} in {year_start}-{year_end}")
        raise ValueError(f"No occurrence records found for the specified criteria.")


def download_worldclim_bioclim_variables(output_dir: Path) -> None:
    """
    Download WorldClim historical climate rasters (1970-2000) for all 19 Bioclim variables.
    
    Args:
        output_dir: Directory to save the downloaded rasters
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    base_url = "https://biogeo.ucdavis.edu/data/worldclim/v2.1/bioclim/WC2.1_10m_bio"
    variables = [f"{i:02d}" for i in range(1, 20)]  # 01-19
    
    downloaded_files = []
    
    for var in variables:
        filename = f"WC2.1_10m_bio_{var}.tif"
        url = f"{base_url}_{var}.tif"
        output_path = output_dir / filename
        
        logger.info(f"Downloading {filename}...")
        
        try:
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify file size (WorldClim rasters are ~10MB each)
            file_size = output_path.stat().st_size
            if file_size < 1000000:  # Less than 1MB is suspicious
                logger.error(f"File {filename} seems too small ({file_size} bytes)")
                raise ValueError(f"Downloaded file {filename} is suspiciously small")
            
            downloaded_files.append(filename)
            logger.info(f"Downloaded {filename} ({file_size} bytes)")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {filename}: {e}")
            raise
    
    # Update manifest
    update_manifest(
        dataset_name="climate_historical",
        file_path=str(output_dir.relative_to(PROJECT_ROOT)),
        source_url="https://biogeo.ucdavis.edu/data/worldclim/v2.1/bioclim/",
        dataset_type="climate_historical",
        description="WorldClim 2.1 historical bioclimatic variables (1970-2000), 19 variables at 10m resolution"
    )


def download_cmip6_future_bioclim_variables(output_dir: Path) -> None:
    """
    Download CMIP6 future climate rasters (SSP2-4.5, 2050) for all 19 Bioclim variables.
    
    Args:
        output_dir: Directory to save the downloaded rasters
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # CMIP6 data is typically hosted on ESGF or mirrored. Using a common mirror.
    # Note: In production, this would require authentication or specific dataset selection.
    base_url = "https://esgf-node.llnl.gov/projects/esgf-llnl/other/cmip6"
    
    # For demonstration, we'll use a placeholder URL pattern that would need to be
    # replaced with actual working URLs. In a real scenario, this would involve
    # querying ESGF for the specific dataset and downloading the files.
    # Here we simulate the process with a known public mirror if available.
    
    # Alternative: Use a pre-processed CMIP6 Bioclim dataset if available
    # For this implementation, we'll use a placeholder that raises an error
    # if no real source is found, as per the "fail loudly" constraint.
    
    variables = [f"{i:02d}" for i in range(1, 20)]  # 01-19
    downloaded_files = []
    
    logger.info("Downloading CMIP6 future climate rasters...")
    logger.warning("CMIP6 data download requires specific ESGF access. Using placeholder logic.")
    
    # In a real implementation, this would:
    # 1. Query ESGF for CMIP6 SSP2-4.5 bioclim datasets
    # 2. Download the specific files using the ESGF API
    # 3. Handle authentication if required
    
    # For now, we raise an error to indicate that the real data source is not accessible
    # This satisfies the "fail loudly" requirement
    raise FileNotFoundError(
        "CMIP6 future climate data is not directly accessible from the configured source. "
        "Please configure a valid ESGF endpoint or use a pre-downloaded dataset."
    )


def compute_sha256_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        SHA-256 checksum as hex string
    """
    return compute_sha256(file_path)


def verify_file_size(file_path: Path, min_size: int = 1000000) -> bool:
    """
    Verify that a file meets a minimum size requirement.
    
    Args:
        file_path: Path to the file
        min_size: Minimum expected file size in bytes
        
    Returns:
        True if file size is sufficient, False otherwise
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False
    
    file_size = file_path.stat().st_size
    if file_size < min_size:
        logger.error(f"File {file_path} is too small ({file_size} bytes < {min_size} bytes)")
        return False
    
    return True


def verify_climate_rasters(data_dir: Path, expected_variables: int = 19) -> bool:
    """
    Verify that all expected climate rasters are present and non-null.
    
    Args:
        data_dir: Directory containing the climate rasters
        expected_variables: Number of expected variables (default 19 for Bioclim)
        
    Returns:
        True if all variables are present and valid, False otherwise
    """
    if not data_dir.exists():
        logger.error(f"Climate data directory not found: {data_dir}")
        return False
    
    found_files = list(data_dir.glob("*.tif"))
    if len(found_files) != expected_variables:
        logger.error(
            f"Expected {expected_variables} climate rasters, found {len(found_files)}"
        )
        return False
    
    for file_path in found_files:
        if not verify_file_size(file_path, min_size=100000):
            logger.error(f"Climate raster {file_path} is invalid")
            return False
    
    logger.info(f"Verified {len(found_files)} climate rasters in {data_dir}")
    return True


def main():
    """Main entry point for data download."""
    logger.info("Starting data download process...")
    
    # Example usage (would be called from task scripts):
    # species_list = ["Buteo jamaicensis", "Accipiter striatus"]
    # fetch_gbif_occurrences(species_list, 1970, 2000, DATA_DIR / "raw" / "occurrence_1970_2000.csv")
    # download_worldclim_bioclim_variables(DATA_DIR / "raw" / "climate_historical")
    
    logger.info("Data download module ready.")


if __name__ == "__main__":
    main()
