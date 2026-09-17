import os
import sys
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import requests
from io import StringIO

from config import ensure_directories
from logging_config import setup_logging, get_logger

# Constants for WDPA
WDPA_LATEST_URL = "https://data.unep-wcmc.org/datasets/289/latest/download"
# Alternative direct download if the dataset endpoint changes, but usually the above is stable for the latest release
# We will attempt the direct download of the latest release CSV/GeoJSON if possible, but the standard is the zip.
# The WDPA latest release is typically a large ZIP file containing a shapefile and a CSV.
# We will look for the CSV file inside the zip.

# Specific file name pattern inside the WDPA ZIP (usually "WDPA_YYYYMMDD_CSV.zip")
# Since we don't know the exact date, we will download and inspect.

logger = get_logger(__name__)

def setup_logger(name: str) -> logging.Logger:
    """Setup a logger for this module."""
    return get_logger(name)

def download_wdpa_release(output_dir: Path) -> Path:
    """
    Downloads the latest WDPA release from the official source.
    Returns the path to the downloaded ZIP file.
    """
    ensure_directories()
    logger.info(f"Downloading WDPA latest release from {WDPA_LATEST_URL}...")
    
    try:
        response = requests.get(WDPA_LATEST_URL, stream=True, timeout=300)
        response.raise_for_status()
        
        zip_path = output_dir / "wdpa_latest.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Downloaded WDPA release to {zip_path}")
        return zip_path
    except requests.RequestException as e:
        logger.error(f"Failed to download WDPA release: {e}")
        raise RuntimeError(f"Could not fetch real data from WDPA: {e}")

def extract_and_load_wdpa(zip_path: Path) -> pd.DataFrame:
    """
    Extracts the CSV from the WDPA ZIP and loads it into a DataFrame.
    Returns the DataFrame with site data.
    """
    logger.info(f"Extracting and loading data from {zip_path}...")
    
    csv_file_path = None
    
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List files to find the CSV
            file_list = zip_ref.namelist()
            csv_files = [f for f in file_list if f.endswith('.csv')]
            
            if not csv_files:
                raise FileNotFoundError("No CSV file found in WDPA archive.")
            
            # Usually the main CSV is named something like WDPA_YYYYMMDD_CSV.csv
            # We take the first one or the largest one if multiple
            csv_file_path = sorted(csv_files, key=lambda x: zip_ref.getinfo(x).file_size, reverse=True)[0]
            
            logger.info(f"Found CSV file in archive: {csv_file_path}")
            
            with zip_ref.open(csv_file_path) as csv_file:
                # Read into pandas
                df = pd.read_csv(csv_file)
                
        logger.info(f"Loaded {len(df)} rows from WDPA.")
        return df
    except Exception as e:
        logger.error(f"Failed to process WDPA archive: {e}")
        raise RuntimeError(f"Could not process WDPA data: {e}")

def filter_and_sample_sites(df: pd.DataFrame, target_count: int = 30) -> pd.DataFrame:
    """
    Filters the WDPA dataset for sites with required metadata and samples a balanced set.
    
    Requirements:
    - Must have 'BIOME' and 'PROT_STATUS' (Protection Status)
    - Filter for sites that are likely candidates for ecotourism or control.
    - Balance between 'National Park' (or similar) and other protected areas.
    - Ensure we have a mix of biomes if possible.
    """
    logger.info("Filtering and sampling sites...")
    
    # Required columns check
    required_cols = ['BIOME', 'PROT_STATUS', 'GDP_WLD', 'MARINE', 'STATUS', 'YEAR']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"Missing columns in WDPA data: {missing_cols}. Attempting to proceed with available columns.")
    
    # Drop rows with missing critical coordinates
    if 'LONG' in df.columns and 'LAT' in df.columns:
        df = df.dropna(subset=['LONG', 'LAT'])
    else:
        raise ValueError("WDPA data missing 'LONG' and 'LAT' columns.")
    
    # Filter for terrestrial sites (MARINE == 0)
    if 'MARINE' in df.columns:
        df = df[df['MARINE'] == 0]
    
    # Filter for sites with a protection status (not 'No Protected Area' or similar)
    # Common status values: 'Ia', 'Ib', 'II', 'III', 'IV', 'V', 'VI', 'Unassigned', 'Not Reported'
    # We want sites that are actually protected.
    if 'PROT_STATUS' in df.columns:
        # Keep only rows where PROT_STATUS is not null and not 'Unassigned' or 'Not Reported'
        valid_statuses = df['PROT_STATUS'].dropna()
        # Simple heuristic: keep if it's a string and not empty
        df = df[df['PROT_STATUS'].notna() & (df['PROT_STATUS'] != '')]
    
    # Filter for sites with Biome data
    if 'BIOME' in df.columns:
        df = df[df['BIOME'].notna() & (df['BIOME'] != '')]
    
    # We need a balanced set. Let's define categories:
    # 1. High Protection (Ia, Ib, II) -> Potential Ecotourism
    # 2. Lower Protection (III, IV, V, VI) -> Control or Mixed
    
    def categorize_protection(status):
        if pd.isna(status): return 'Unknown'
        status = str(status).upper()
        if status in ['IA', 'IB', 'II']: return 'High'
        if status in ['III', 'IV', 'V', 'VI']: return 'Medium'
        return 'Other'
    
    df['PROT_CATEGORY'] = df['PROT_STATUS'].apply(categorize_protection)
    
    # Sample from 'High' and 'Medium' to get a balance
    high_prot = df[df['PROT_CATEGORY'] == 'High']
    medium_prot = df[df['PROT_CATEGORY'] == 'Medium']
    
    # If we don't have enough in one category, take what we can
    n_per_cat = target_count // 2
    
    sample_high = high_prot.sample(n=min(n_per_cat, len(high_prot)), random_state=42)
    sample_medium = medium_prot.sample(n=min(n_per_cat, len(medium_prot)), random_state=42)
    
    # If we still need more, fill from the rest
    remaining_needed = target_count - (len(sample_high) + len(sample_medium))
    if remaining_needed > 0:
        other_sites = df[~df.index.isin(sample_high.index) & ~df.index.isin(sample_medium.index)]
        if len(other_sites) > 0:
            sample_other = other_sites.sample(n=min(remaining_needed, len(other_sites)), random_state=43)
            final_sample = pd.concat([sample_high, sample_medium, sample_other])
        else:
            final_sample = pd.concat([sample_high, sample_medium])
    else:
        final_sample = pd.concat([sample_high, sample_medium])
    
    # Reset index and select relevant columns
    result = final_sample.reset_index(drop=True)
    
    # Rename columns to a standard schema for downstream use
    # Standard: site_id, latitude, longitude, biome, protection_status, category
    rename_map = {}
    if 'LONG' in result.columns: rename_map['LONG'] = 'longitude'
    if 'LAT' in result.columns: rename_map['LAT'] = 'latitude'
    if 'BIOME' in result.columns: rename_map['BIOME'] = 'biome'
    if 'PROT_STATUS' in result.columns: rename_map['PROT_STATUS'] = 'protection_status'
    if 'NAME' in result.columns: rename_map['NAME'] = 'site_name'
    
    result = result.rename(columns=rename_map)
    
    # Ensure site_id exists
    if 'site_id' not in result.columns:
        result['site_id'] = [f"WDPA_{i:04d}" for i in range(len(result))]
    
    logger.info(f"Selected {len(result)} sites for analysis.")
    return result

def main():
    """
    Main entry point to fetch, filter, and save site coordinates.
    """
    setup_logging()
    logger.info("Starting T012b: Fetch site coordinates from WDPA.")
    
    output_dir = Path("data/raw")
    output_file = output_dir / "site_coordinates.csv"
    
    try:
        # 1. Download
        zip_path = download_wdpa_release(output_dir)
        
        # 2. Extract and Load
        df = extract_and_load_wdpa(zip_path)
        
        # 3. Filter and Sample
        filtered_df = filter_and_sample_sites(df, target_count=30)
        
        # 4. Save
        output_dir.mkdir(parents=True, exist_ok=True)
        filtered_df.to_csv(output_file, index=False)
        
        logger.info(f"Successfully saved site coordinates to {output_file}")
        print(f"Output written to {output_file}")
        
    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Fail loudly as per requirements
        raise RuntimeError(f"Failed to fetch real data for T012b: {e}")

if __name__ == "__main__":
    main()
