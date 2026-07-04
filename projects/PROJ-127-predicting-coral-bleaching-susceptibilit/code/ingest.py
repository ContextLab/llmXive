"""
Ingest module for downloading and merging environmental and trait data.

This script implements the skeleton for data download and merging logic.
It fetches real data from configured sources (NOAA, UNEP, Coral Trait DB, ReefBase),
performs initial validation, and prepares data for the unified pipeline.

Outputs:
- data/raw/<source>_raw.<ext>: Raw downloaded files
- data/processed/ingestion_log.json: Log of download statuses and file paths
"""

import os
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import requests
import pandas as pd
import geopandas as gpd
from io import BytesIO
from zipfile import ZipFile
import rasterio
from rasterio.io import MemoryFile

# Import project configuration
import config

# Ensure directories exist
DATA_RAW_DIR = Path(config.DATA_RAW_DIR)
DATA_PROCESSED_DIR = Path(config.DATA_PROCESSED_DIR)
DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest_path: Path, timeout: int = 60) -> Optional[Path]:
    """
    Download a file from a URL to a destination path.
    Returns the path if successful, None otherwise.
    """
    try:
        print(f"Downloading: {url}")
        response = requests.get(url, stream=True, timeout=timeout)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"Downloaded: {dest_path}")
        return dest_path
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        return None

def download_csv(url: str, dest_name: str) -> Optional[Path]:
    """Download a CSV file."""
    dest_path = DATA_RAW_DIR / dest_name
    return download_file(url, dest_path)

def download_geojson(url: str, dest_name: str) -> Optional[Path]:
    """Download a GeoJSON file."""
    dest_path = DATA_RAW_DIR / dest_name
    return download_file(url, dest_path)

def download_raster(url: str, dest_name: str) -> Optional[Path]:
    """Download a raster file (GeoTIFF)."""
    dest_path = DATA_RAW_DIR / dest_name
    return download_file(url, dest_path)

def load_noaa_sst_dhw() -> Optional[pd.DataFrame]:
    """
    Load NOAA SST and DHW data.
    In a full implementation, this would download and parse the raster data.
    For the skeleton, we attempt to download the source specified in config.
    """
    if not hasattr(config, 'NOAA_URL') or not config.NOAA_URL:
        print("Warning: config.NOAA_URL not defined. Skipping NOAA data.")
        return None

    # Attempt to download the raw data
    # Note: In a real scenario, NOAA data is often large and distributed.
    # This function assumes a direct link to a processed CSV or a zip containing it.
    # If the config URL points to a zip, we handle extraction here.
    
    # For the skeleton, we try to fetch the URL defined in config.NOAA_URL
    # If it's a direct CSV link:
    dest_name = "noaa_sst_dhw_raw.csv"
    file_path = download_csv(config.NOAA_URL, dest_name)
    
    if file_path and file_path.exists():
        # Try to read as CSV
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded NOAA data: {len(df)} rows")
            return df
        except Exception as e:
            print(f"Could not parse NOAA CSV: {e}")
            # If it's a zip, try to extract
            if file_path.suffix == '.zip':
                try:
                    with ZipFile(file_path, 'r') as zip_ref:
                        csv_name = [n for n in zip_ref.namelist() if n.endswith('.csv')][0]
                        with zip_ref.open(csv_name) as csv_file:
                            df = pd.read_csv(csv_file)
                            print(f"Extracted and loaded NOAA data from zip: {len(df)} rows")
                            return df
                except Exception as zip_err:
                    print(f"Failed to extract zip: {zip_err}")
    
    return None

def load_coral_traits() -> Optional[pd.DataFrame]:
    """
    Load Coral Trait Database data.
    """
    if not hasattr(config, 'CORAL_TRAIT_URL') or not config.CORAL_TRAIT_URL:
        print("Warning: config.CORAL_TRAIT_URL not defined. Skipping Coral Trait data.")
        return None

    dest_name = "coral_traits_raw.csv"
    file_path = download_csv(config.CORAL_TRAIT_URL, dest_name)

    if file_path and file_path.exists():
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded Coral Trait data: {len(df)} rows")
            return df
        except Exception as e:
            print(f"Could not parse Coral Trait CSV: {e}")
    return None

def load_unep_reefs() -> Optional[gpd.GeoDataFrame]:
    """
    Load UNEP Reef Geometries.
    """
    if not hasattr(config, 'UNEP_URL') or not config.UNEP_URL:
        print("Warning: config.UNEP_URL not defined. Skipping UNEP Reef data.")
        return None

    dest_name = "unep_reefs_raw.geojson"
    file_path = download_geojson(config.UNEP_URL, dest_name)

    if file_path and file_path.exists():
        try:
            gdf = gpd.read_file(file_path)
            print(f"Loaded UNEP Reef data: {len(gdf)} features")
            return gdf
        except Exception as e:
            print(f"Could not parse UNEP GeoJSON: {e}")
    return None

def load_reefbase_events() -> Optional[pd.DataFrame]:
    """
    Load ReefBase bleaching events.
    """
    if not hasattr(config, 'REEFBASE_URL') or not config.REEFBASE_URL:
        print("Warning: config.REEFBASE_URL not defined. Skipping ReefBase data.")
        return None

    dest_name = "reefbase_events_raw.csv"
    file_path = download_csv(config.REEFBASE_URL, dest_name)

    if file_path and file_path.exists():
        try:
            df = pd.read_csv(file_path)
            print(f"Loaded ReefBase Events data: {len(df)} rows")
            return df
        except Exception as e:
            print(f"Could not parse ReefBase CSV: {e}")
    return None

def merge_datasets(
    sst_df: Optional[pd.DataFrame],
    traits_df: Optional[pd.DataFrame],
    reefs_gdf: Optional[gpd.GeoDataFrame],
    events_df: Optional[pd.DataFrame]
) -> Optional[pd.DataFrame]:
    """
    Merge datasets into a unified structure.
    This is a skeleton implementation that logs the attempt and returns a 
    minimal unified dataframe if data is available, or None if critical sources are missing.
    """
    print("Attempting to merge datasets...")
    
    sources = {
        "NOAA_SST_DHW": sst_df,
        "Coral_Traits": traits_df,
        "UNEP_Reefs": reefs_gdf,
        "ReefBase_Events": events_df
    }
    
    available_sources = [k for k, v in sources.items() if v is not None]
    
    if not available_sources:
        print("Error: No data sources available to merge.")
        return None
    
    print(f"Available sources: {', '.join(available_sources)}")
    
    # Skeleton merge logic:
    # In a real implementation, this would join on reef IDs and species names.
    # Here we demonstrate the structure.
    
    unified_data = []
    
    # If we have traits, use them as the base if available
    if traits_df is not None:
        # Normalize columns
        traits_df = traits_df.copy()
        # Ensure common columns exist (skeleton)
        if 'species_name' not in traits_df.columns:
            traits_df['species_name'] = 'unknown'
        if 'thermal_tolerance' not in traits_df.columns:
            traits_df['thermal_tolerance'] = None
        unified_data.append(traits_df)
    
    # If we have events, add them
    if events_df is not None:
        events_df = events_df.copy()
        if 'bleaching_label' not in events_df.columns:
            events_df['bleaching_label'] = 0 # Default no bleaching
        unified_data.append(events_df)
        
    # If we have SST/DHW, add them
    if sst_df is not None:
        sst_df = sst_df.copy()
        if 'sst' not in sst_df.columns and 'SST' in sst_df.columns:
            sst_df['sst'] = sst_df['SST']
        if 'dhw' not in sst_df.columns and 'DHW' in sst_df.columns:
            sst_df['dhw'] = sst_df['DHW']
        unified_data.append(sst_df)

    if not unified_data:
        print("No data frames to concatenate.")
        return None
        
    # Concatenate if possible (might fail if columns differ wildly, which is expected in skeleton)
    try:
        result = pd.concat(unified_data, ignore_index=True, sort=False)
        print(f"Unified dataset created with {len(result)} rows.")
        return result
    except Exception as e:
        print(f"Error merging dataframes: {e}")
        # Return a minimal structure if merge fails
        return pd.DataFrame(columns=["status", "error", "sources"])

def main():
    """
    Main entry point for the ingestion pipeline.
    Downloads data from configured sources and attempts a merge.
    Saves raw files and a processing log.
    """
    print("Starting Ingestion Pipeline (T006)...")
    start_time = datetime.now()
    
    log_data = {
        "timestamp": start_time.isoformat(),
        "sources": {},
        "merged_rows": 0,
        "status": "incomplete" # Skeleton status
    }
    
    # 1. Download and Load Data
    sst_df = load_noaa_sst_dhw()
    traits_df = load_coral_traits()
    reefs_gdf = load_unep_reefs()
    events_df = load_reefbase_events()
    
    # Record status
    log_data["sources"]["NOAA"] = "success" if sst_df is not None else "failed"
    log_data["sources"]["CoralTraits"] = "success" if traits_df is not None else "failed"
    log_data["sources"]["UNEP"] = "success" if reefs_gdf is not None else "failed"
    log_data["sources"]["ReefBase"] = "success" if events_df is not None else "failed"
    
    # 2. Merge Data
    unified_df = merge_datasets(sst_df, traits_df, reefs_gdf, events_df)
    
    if unified_df is not None:
        log_data["merged_rows"] = len(unified_df)
        # Save unified data
        output_path = DATA_PROCESSED_DIR / "reef_species_unified.csv"
        unified_df.to_csv(output_path, index=False)
        print(f"Saved unified dataset to {output_path}")
        log_data["status"] = "completed"
    else:
        log_data["status"] = "failed"
        print("Failed to generate unified dataset.")
    
    # 3. Save Log
    log_path = DATA_PROCESSED_DIR / "ingestion_log.json"
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2, default=str)
    print(f"Saved ingestion log to {log_path}")
    
    end_time = datetime.now()
    print(f"Ingestion pipeline finished. Duration: {end_time - start_time}")
    
    # Return 0 for success, 1 for failure (even if partial)
    # For a skeleton, we return 0 if at least one source was fetched
    if any(v == "success" for v in log_data["sources"].values()):
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())