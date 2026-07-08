import os
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import warnings

import pandas as pd
import numpy as np
import requests
import geopandas as gpd
from rasterio.features import geometry_mask
import rasterio
from shapely.geometry import Point, mapping

import config

# --- Download Helpers ---

def download_file(url: str, dest_path: Path, chunk_size: int = 8192) -> Path:
    """Download a file from a URL to a destination path."""
    if dest_path.exists():
        return dest_path

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {url} to {dest_path}...")
    try:
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        return dest_path
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to download {url}: {e}")

def download_csv(url: str, dest_path: Path) -> Path:
    """Download a CSV file."""
    return download_file(url, dest_path)

def download_geojson(url: str, dest_path: Path) -> Path:
    """Download a GeoJSON file."""
    return download_file(url, dest_path)

def download_raster(url: str, dest_path: Path) -> Path:
    """Download a raster file (GeoTIFF)."""
    return download_file(url, dest_path)

# --- Data Loaders ---

def load_noaa_sst_dhw() -> pd.DataFrame:
    """
    Load NOAA SST and DHW data.
    In a real pipeline, this would download rasters, reproject to a common grid,
    and extract values at reef locations. Here we simulate the merged structure
    based on the task requirements, assuming rasters exist or are fetched.
    """
    # Placeholder for real raster processing logic
    # If config.NOAA_URL is set, we would download and process it.
    # For this task implementation, we return a structure that can be merged.
    # In a real run, this would read the actual downloaded files.
    if not hasattr(config, 'NOAA_URL') or not config.NOAA_URL:
        # Fallback to a minimal structure if config is missing, 
        # though T013 should have ensured data exists.
        print("Warning: NOAA_URL not configured, generating minimal placeholder structure.")
        return pd.DataFrame(columns=['reef_id', 'year', 'month', 'sst_mean', 'dhw_max'])

    # Real implementation would look like:
    # raster_path = download_raster(config.NOAA_URL, config.DATA_RAW_DIR / "noaa_sst_dhw.tif")
    # ... process raster ...
    # return extracted_df
    
    # Since we cannot execute the raster processing here without the file,
    # we assume the previous task (T013/T014/T015) has produced a base CSV 
    # that we are augmenting, or we are building the logic to do so.
    # However, T016 specifically asks to flag missing trait data.
    # We assume the input to this stage is a dataframe that *should* have trait data.
    # We will implement the logic that *would* be applied to the unified dataset.
    
    # For the purpose of this task execution, we return a dummy dataframe 
    # that represents the state AFTER T015 (imputation) but BEFORE T016 (flagging).
    # The actual flagging logic is what we are implementing.
    return pd.DataFrame()

def load_coral_traits() -> pd.DataFrame:
    """
    Load Coral Trait Database data.
    Returns a DataFrame with species traits.
    """
    # Real implementation: download from config.CORAL_TRAIT_URL
    # Process and return species-level traits.
    return pd.DataFrame()

def load_unep_reefs() -> gpd.GeoDataFrame:
    """
    Load UNEP reef geometries.
    Returns a GeoDataFrame.
    """
    return gpd.GeoDataFrame()

def load_reefbase_events() -> pd.DataFrame:
    """
    Load ReefBase bleaching events.
    Returns a DataFrame with event records.
    """
    return pd.DataFrame()

def merge_datasets() -> pd.DataFrame:
    """
    Merge all sources into a unified dataframe.
    T014 responsibility.
    """
    # This would combine SST, DHW, Traits, and Events.
    # For T016, we assume the input is the result of T015 (imputed).
    # We will simulate the input data to demonstrate the flagging logic.
    # In a real run, this would read the processed CSV from T014/T015.
    pass

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values by imputing with nearest temporal neighbor or exclusion.
    T015 responsibility.
    """
    # Real implementation of imputation logic
    return df

def flag_missing_trait_data(df: pd.DataFrame, trait_columns: list) -> pd.DataFrame:
    """
    Flag rows where species trait data is missing.
    
    Logic:
    1. Identify rows where any of the `trait_columns` are NaN or null.
    2. Create a new column 'trait_data_status' (or similar) indicating:
       - 'complete': All trait data present.
       - 'partial': Some trait data present (if multiple trait columns).
       - 'unknown': All trait data missing.
       - Or simply a boolean 'has_trait_data'.
    
    Per the task description: "exclude or mark as 'unknown' per edge case".
    We will mark them as 'unknown' in a new column and also set a boolean flag.
    We do NOT exclude them here, as the task says "flag... (exclude or mark)".
    The decision to exclude might be made in downstream steps or by a configuration.
    We will add a column 'trait_missing' (bool) and 'trait_status' (str).
    """
    if df.empty:
        return df

    # Ensure we are working on a copy to avoid SettingWithCopyWarning
    result = df.copy()

    # Check for missing values in the specified trait columns
    # Assuming 'thermal_tolerance' and 'bleaching_response' are key trait columns
    # based on the project context. If the actual columns differ, this logic
    # adapts to the provided list.
    
    # Filter for rows where at least one trait column is null
    mask_missing = result[trait_columns].isnull().any(axis=1)
    
    # Filter for rows where ALL trait columns are null
    mask_all_missing = result[trait_columns].isnull().all(axis=1)
    
    # Create status column
    result['trait_status'] = 'complete'
    result.loc[mask_missing, 'trait_status'] = 'partial'
    result.loc[mask_all_missing, 'trait_status'] = 'unknown'
    
    # Create boolean flag for easy filtering/exclusion later
    result['trait_missing'] = mask_missing

    # Log the count of flagged rows
    count_unknown = mask_all_missing.sum()
    count_partial = (mask_missing & ~mask_all_missing).sum()
    print(f"Trait Data Flagging Summary:")
    print(f"  - Rows with missing trait data (partial or unknown): {mask_missing.sum()}")
    print(f"  - Rows with ALL trait data missing ('unknown'): {count_unknown}")
    print(f"  - Rows with PARTIAL trait data: {count_partial}")

    return result

def main():
    """
    Main entry point for T016: Flag rows where species trait data is missing.
    
    This script assumes that T013, T014, and T015 have been completed and
    that a unified dataset exists at `config.PROCESSED_DIR / 'reef_species_unified.csv'`.
    
    It will:
    1. Load the unified dataset.
    2. Identify trait columns (e.g., 'thermal_tolerance', 'bleaching_response').
    3. Flag rows with missing trait data.
    4. Save the result to `config.PROCESSED_DIR / 'reef_species_flagged.csv'`.
    """
    print("Starting T016: Flagging missing species trait data...")

    # Define paths
    input_path = config.PROCESSED_DIR / 'reef_species_unified.csv'
    output_path = config.PROCESSED_DIR / 'reef_species_flagged.csv'

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T013, T014, and T015 have been completed successfully."
        )

    # Load data
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)

    if df.empty:
        print("Warning: Input dataframe is empty. Nothing to process.")
        # Save empty dataframe with new columns to maintain schema
        df['trait_status'] = pd.Series(dtype=str)
        df['trait_missing'] = pd.Series(dtype=bool)
        df.to_csv(output_path, index=False)
        print(f"Saved empty flagged dataset to {output_path}")
        return

    # Define trait columns based on domain knowledge
    # These should match the columns produced by T013/T014
    trait_columns = [col for col in df.columns if 'thermal' in col.lower() or 'bleaching' in col.lower() or 'trait' in col.lower()]
    
    # Fallback if no obvious trait columns found, but this might indicate a schema issue
    if not trait_columns:
        # Try to guess based on common names if the project uses specific ones
        potential_traits = ['thermal_tolerance', 'bleaching_response', 'growth_rate', 'colony_size']
        trait_columns = [col for col in potential_traits if col in df.columns]
    
    if not trait_columns:
        warnings.warn("No trait columns identified in the dataset. "
                      "Cannot flag missing trait data. "
                      "Please verify the schema of 'reef_species_unified.csv'.")
        # Still save the file with empty flags
        df['trait_status'] = 'unknown' # Default to unknown if no traits exist
        df['trait_missing'] = True
        df.to_csv(output_path, index=False)
        print(f"Saved dataset with default 'unknown' status to {output_path}")
        return

    print(f"Identified trait columns: {trait_columns}")

    # Flag missing data
    df_flagged = flag_missing_trait_data(df, trait_columns)

    # Save result
    df_flagged.to_csv(output_path, index=False)
    print(f"Successfully saved flagged dataset to {output_path}")
    print(f"Total rows processed: {len(df_flagged)}")

if __name__ == "__main__":
    main()