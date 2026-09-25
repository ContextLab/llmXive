import os
import time
import logging
import json
from datetime import datetime
from pathlib import Path
import requests
import csv

from config import DATA_DIR, PROJECT_ROOT
from logging_config import get_download_logger

# Ensure directories exist
RAW_DATA_DIR = DATA_DIR / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

def fetch_gbif_occurrences(
    species_list,
    start_year,
    end_year,
    output_path,
    max_results_per_page=300,
    api_key_env="GBIF_API_KEY"
):
    """
    Fetch occurrence data from GBIF API for given species and year range.
    
    Args:
        species_list: List of species names to fetch
        start_year: Start year for occurrence records
        end_year: End year for occurrence records
        output_path: Path to save the CSV file
        max_results_per_page: Max results per API request (pagination)
        api_key_env: Environment variable name for GBIF API key
    
    Returns:
        None (writes directly to CSV)
    """
    logger = get_download_logger()
    logger.info(f"Starting GBIF fetch for {len(species_list)} species from {start_year} to {end_year}")
    
    # GBIF API endpoint
    base_url = "https://api.gbif.org/v2/occurrence/search"
    
    # Headers
    headers = {
        "User-Agent": "llmXive-sdm-pipeline/1.0",
        "Accept": "application/json"
    }
    
    # Add API key if available
    api_key = os.environ.get(api_key_env)
    if api_key:
        headers["Authorization"] = f"Basic {api_key}"
    
    all_records = []
    total_fetched = 0
    
    for species in species_list:
        logger.info(f"Fetching data for species: {species}")
        
        params = {
            "scientificName": species,
            "year": f"{start_year},{end_year}",
            "limit": max_results_per_page,
            "offset": 0,
            "hasCoordinate": "true",
            "typeStatus": "verbatim",
            "recordedBy": "",
            "datasetKey": ""
        }
        
        page_count = 0
        while True:
            try:
                response = requests.get(base_url, headers=headers, params=params, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                results = data.get("results", [])
                if not results:
                    break
                
                page_count += 1
                logger.debug(f"  Page {page_count}: fetched {len(results)} records")
                
                for record in results:
                    # Extract required fields
                    rec = {
                        "source_identifier": record.get("basisOfRecord", "UNKNOWN"),
                        "download_timestamp": datetime.now().isoformat(),
                        "original_dataset_name": record.get("datasetKey", "UNKNOWN"),
                        "species": record.get("scientificName", species),
                        "decimalLatitude": record.get("decimalLatitude"),
                        "decimalLongitude": record.get("decimalLongitude"),
                        "eventDate": record.get("eventDate", "")
                    }
                    
                    # Validate coordinates exist
                    if rec["decimalLatitude"] is not None and rec["decimalLongitude"] is not None:
                        all_records.append(rec)
                        total_fetched += 1
                
                # Check if there are more pages
                if len(results) < max_results_per_page:
                    break
                
                params["offset"] += max_results_per_page
                
                # Rate limiting
                time.sleep(0.5)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching page for {species}: {e}")
                break
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for {species}: {e}")
                break
        
        logger.info(f"  Completed species {species}: {len([r for r in all_records if r['species'] == species])} records")
    
    # Write to CSV
    logger.info(f"Writing {total_fetched} records to {output_path}")
    
    fieldnames = [
        "source_identifier", 
        "download_timestamp", 
        "original_dataset_name", 
        "species", 
        "decimalLatitude", 
        "decimalLongitude", 
        "eventDate"
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)
    
    logger.info(f"Successfully wrote {total_fetched} records to {output_path}")
    return total_fetched

def download_worldclim_bioclim_variables(output_dir):
    """
    Download WorldClim v2 historical climate rasters (1970-2000).
    All 19 bioclim variables (bio1-bio19).
    """
    logger = get_download_logger()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # WorldClim download URLs for North America (5 arc-minutes resolution)
    # Using the direct download links for bioclim variables
    base_url = "https://worldclim.org/data/bioclim.html"
    
    # We will use rasterio or requests to download from the official source
    # For this implementation, we use the direct file URLs from WorldClim
    # Note: In production, you might want to use the wcapi or a more robust method
    
    variables = [f"bio{i}" for i in range(1, 20)]
    missing_vars = []
    
    logger.info("Downloading WorldClim historical climate rasters...")
    
    for var in variables:
        filename = f"{var}.tif"
        filepath = output_path / filename
        
        # WorldClim 5-min resolution URLs
        # These are example URLs - in practice, you'd need to construct them properly
        # or use the WorldClim API
        url = f"https://biogeo.ucdavis.edu/data/worldclim/v2.0/bioclim/wc2.0_5min_bio/{var}.tif"
        
        if filepath.exists():
            logger.info(f"  {var} already exists, skipping")
            continue
        
        try:
            logger.info(f"  Downloading {var}...")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"  Saved {var}")
        except Exception as e:
            logger.error(f"  Failed to download {var}: {e}")
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing variables: {missing_vars}")
        raise RuntimeError(f"Failed to download all 19 bioclim variables. Missing: {missing_vars}")
    
    logger.info("WorldClim historical download complete")

def download_cmip6_future_bioclim_variables(output_dir):
    """
    Download CMIP6 SSP2-4.5 future climate rasters (2050).
    All 19 bioclim variables (bio1-bio19).
    """
    logger = get_download_logger()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    variables = [f"bio{i}" for i in range(1, 20)]
    missing_vars = []
    
    logger.info("Downloading CMIP6 future climate rasters...")
    
    for var in variables:
        filename = f"{var}.tif"
        filepath = output_path / filename
        
        # CMIP6 SSP2-4.5 URLs (example - adjust based on actual source)
        # Using WorldClim's CMIP6 projections
        url = f"https://biogeo.ucdavis.edu/data/cmip6/ssp245/5min/{var}.tif"
        
        if filepath.exists():
            logger.info(f"  {var} already exists, skipping")
            continue
        
        try:
            logger.info(f"  Downloading {var}...")
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"  Saved {var}")
        except Exception as e:
            logger.error(f"  Failed to download {var}: {e}")
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing variables: {missing_vars}")
        raise RuntimeError(f"Failed to download all 19 CMIP6 bioclim variables. Missing: {missing_vars}")
    
    logger.info("CMIP6 future download complete")

def main():
    """
    Main function to fetch recent occurrence data (2005-2020) for evaluation.
    This implements T011.
    """
    logger = get_download_logger()
    
    # Load species list from config
    from config import SPECIES_LIST
    
    output_path = RAW_DATA_DIR / "occurrence_2005_2020.csv"
    
    logger.info("Starting T011: Fetch recent occurrence data (2005-2020)")
    
    count = fetch_gbif_occurrences(
        species_list=SPECIES_LIST,
        start_year=2005,
        end_year=2020,
        output_path=output_path
    )
    
    logger.info(f"T011 complete: {count} records fetched and saved to {output_path}")
    
    if count == 0:
        logger.warning("No records fetched. Check species list and API connectivity.")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
