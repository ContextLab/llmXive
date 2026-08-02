import os
import time
import logging
from datetime import datetime
from pathlib import Path
import requests
import pandas as pd
import yaml

from config import DATA_DIR, RND_SEED
from logging_config import get_logger

# Ensure directories exist
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

logger = get_logger(__name__)

GBIF_API_BASE = "https://api.gbif.org/v2/occurrence/search"

# Target species (North American birds) - simplified list for MVP
# In a full implementation, this would be a larger curated list
TARGET_SPECIES = [
    "Turdus migratorius",  # American Robin
    "Setophaga ruticilla", # American Redstart
    "Cardinalis cardinalis", # Northern Cardinal
    "Sialia sialis",       # Eastern Bluebird
    "Poecile carolinensis" # Carolina Chickadee
]

def fetch_occurrences(year_start: int, year_end: int, output_file: Path) -> pd.DataFrame:
    """
    Fetches bird occurrence data from GBIF API for a given year range.
    Implements pagination and year filtering.
    """
    all_records = []
    max_results_per_request = 300
    total_fetched = 0

    for species in TARGET_SPECIES:
        logger.info(f"Fetching data for species: {species}")
        
        # GBIF API parameters
        params = {
            'taxonKey': None, # We will search by scientificName as taxonKey lookup is complex without a registry
            'scientificName': species,
            'year': f"{year_start},{year_end}",
            'hasCoordinate': True,
            'limit': max_results_per_request,
            'offset': 0,
            'country': 'US,CA,MX' # North America focus
        }

        # Note: GBIF does not support direct scientificName search with year filter in a single call easily
        # without a taxonKey. We will use the scientificName filter which is supported.
        # The API endpoint 'search' allows scientificName.
        
        has_more = True
        while has_more:
            try:
                # GBIF API requires a valid email in the User-Agent header
                headers = {
                    'User-Agent': 'llmXive-sdm-pipeline (research@example.com)'
                }
                
                response = requests.get(GBIF_API_BASE, params=params, headers=headers, timeout=60)
                response.raise_for_status()
                data = response.json()
                
                results = data.get('results', [])
                if not results:
                    has_more = False
                    break
                
                for record in results:
                    # Filter for valid coordinates
                    if 'decimalLatitude' in record and 'decimalLongitude' in record:
                        all_records.append(record)
                
                total_fetched += len(results)
                params['offset'] += max_results_per_request
                
                # Check if we got fewer results than requested (last page)
                if len(results) < max_results_per_request:
                    has_more = False
                
                # Rate limiting: GBIF suggests 5 requests per second max
                time.sleep(0.25)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error fetching data for {species}: {e}")
                has_more = False
                break

    if not all_records:
        logger.warning("No records fetched. Returning empty dataframe.")
        return pd.DataFrame()

    # Convert to DataFrame
    df = pd.DataFrame(all_records)
    
    # Select relevant columns
    columns_to_keep = [
        'scientificName', 'decimalLatitude', 'decimalLongitude', 
        'eventDate', 'year', 'basisOfRecord', 'institutionCode',
        'datasetName', 'occurrenceID'
    ]
    
    # Filter columns that exist
    existing_columns = [c for c in columns_to_keep if c in df.columns]
    df = df[existing_columns].copy()
    
    # Ensure year is integer for filtering if needed (though API filters it)
    if 'year' in df.columns:
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df = df.dropna(subset=['year'])
        df = df[(df['year'] >= year_start) & (df['year'] <= year_end)]
    
    # Remove duplicates based on occurrenceID
    if 'occurrenceID' in df.columns:
        df = df.drop_duplicates(subset=['occurrenceID'])
    
    logger.info(f"Fetched {len(df)} records for {year_start}-{year_end}")
    return df

def add_metadata_columns(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Adds required metadata columns per Constitution Principle VI:
    - source_identifier
    - download_timestamp
    - original_dataset_name
    """
    if df.empty:
        logger.warning("DataFrame is empty, cannot add metadata.")
        return df

    download_timestamp = datetime.now().isoformat()
    
    # Create metadata columns
    df['source_identifier'] = 'GBIF_API'
    df['download_timestamp'] = download_timestamp
    
    # Map datasetName to original_dataset_name (if present, else default)
    if 'datasetName' in df.columns:
        df['original_dataset_name'] = df['datasetName']
    else:
        df['original_dataset_name'] = 'Unknown_GBIF_Dataset'
    
    # Reorder columns to put metadata at the end or specific position
    # Let's put them at the end for clarity
    meta_cols = ['source_identifier', 'download_timestamp', 'original_dataset_name']
    other_cols = [c for c in df.columns if c not in meta_cols]
    df = df[other_cols + meta_cols]
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Saved metadata-enhanced data to {output_path}")
    
    return df

def derive_effort_data(df: pd.DataFrame, output_path: Path) -> pd.DataFrame:
    """
    Derives target-group effort data (all-observer density) from the occurrence data.
    This is an internal derivation, not an external download.
    """
    if df.empty:
        logger.warning("Empty input for effort data derivation.")
        return pd.DataFrame()
    
    # Simple binning approach for density:
    # 1. Create a grid (e.g., 0.1 degree bins)
    # 2. Count occurrences per bin
    # This is a simplified proxy for "target-group" effort.
    
    # Create grid keys
    lat_bins = pd.cut(df['decimalLatitude'], bins=100, labels=False)
    lon_bins = pd.cut(df['decimalLongitude'], bins=100, labels=False)
    
    df_temp = df.copy()
    df_temp['lat_bin'] = lat_bins
    df_temp['lon_bin'] = lon_bins
    
    effort = df_temp.groupby(['lat_bin', 'lon_bin']).size().reset_index(name='count')
    
    effort.to_csv(output_path, index=False)
    logger.info(f"Derived effort data saved to {output_path}")
    return effort

def main():
    """
    Main entry point for T010: Fetch historical data (1970-2000).
    """
    logger.info("Starting historical data download (1970-2000)...")
    output_file = RAW_DIR / "occurrence_1970_2000.csv"
    
    df = fetch_occurrences(1970, 2000, output_file)
    if not df.empty:
        add_metadata_columns(df, output_file)
    else:
        logger.error("Failed to fetch historical data.")
        # Create empty file with headers to satisfy downstream checks if needed, 
        # but strictly speaking, we should fail loudly if no data.
        # Per constraints: "FAIL LOUDLY — never fall back to synthetic".
        raise RuntimeError("No historical data fetched from GBIF.")

def main_effort():
    """
    Main entry point for T010c: Derive effort data from historical data.
    """
    logger.info("Starting effort data derivation...")
    input_file = RAW_DIR / "occurrence_1970_2000.csv"
    output_file = RAW_DIR / "effort_data.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}. Run main() first.")
    
    df = pd.read_csv(input_file)
    derive_effort_data(df, output_file)

if __name__ == "__main__":
    # Check which function to run based on environment or args could be added
    # For now, run historical fetch
    main()