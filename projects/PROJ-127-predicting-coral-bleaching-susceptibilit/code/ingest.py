import os
import json
import sys
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import warnings

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

import config

# --- Download Helpers ---
def download_file(url, dest_path):
    """Download a file from a URL to a local path."""
    import requests
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    try:
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Downloaded: {dest_path}")
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        raise

def download_csv(url, dest_path):
    """Download a CSV file."""
    download_file(url, dest_path)

def download_geojson(url, dest_path):
    """Download a GeoJSON file."""
    download_file(url, dest_path)

def download_raster(url, dest_path):
    """Download a raster file (e.g., GeoTIFF)."""
    download_file(url, dest_path)

# --- Loaders ---
def load_noaa_sst_dhw():
    """
    Load NOAA SST and DHW data.
    In a real run, this would process downloaded rasters or a merged CSV.
    For this task, we assume T013 has produced a CSV at the configured path.
    """
    path = Path(config.DATA_PROCESSED) / "noaa_climate_data.csv"
    if not path.exists():
        # Attempt to generate a minimal real-like structure if file missing (fail loud later if needed)
        # But per constraints, we assume T013 handled the fetch. If missing, we raise.
        raise FileNotFoundError(f"NOAA data file not found at {path}. Ensure T013 ran successfully.")
    
    df = pd.read_csv(path)
    # Ensure coordinate columns exist
    if 'lon' not in df.columns or 'lat' not in df.columns:
        # Try to infer or rename if standard names differ
        cols = df.columns.tolist()
        if 'longitude' in cols and 'latitude' in cols:
            df.rename(columns={'longitude': 'lon', 'latitude': 'lat'}, inplace=True)
        else:
            raise ValueError("NOAA data missing required 'lon' and 'lat' columns.")
    return df

def load_coral_traits():
    """Load Coral Trait Database data."""
    path = Path(config.DATA_PROCESSED) / "coral_traits.csv"
    if not path.exists():
        raise FileNotFoundError(f"Coral Traits data file not found at {path}. Ensure T013 ran successfully.")
    df = pd.read_csv(path)
    # Standardize columns
    if 'reef_id' not in df.columns and 'reef_name' in df.columns:
        df['reef_id'] = df['reef_name'] # Fallback if ID is name
    return df

def load_unep_reefs():
    """Load UNEP Reef Geometries."""
    path = Path(config.DATA_PROCESSED) / "unep_reefs.geojson"
    if not path.exists():
        raise FileNotFoundError(f"UNEP Reef data file not found at {path}. Ensure T013 ran successfully.")
    gdf = gpd.read_file(path)
    # Convert to DataFrame with centroids for joining
    gdf['geometry'] = gdf.centroid
    df = pd.DataFrame(gdf)
    # Ensure ID column exists
    if 'id' not in df.columns and 'name' in df.columns:
        df['id'] = df['name']
    return df

def load_reefbase_events():
    """Load ReefBase Bleaching Events."""
    path = Path(config.DATA_PROCESSED) / "reefbase_events.csv"
    if not path.exists():
        raise FileNotFoundError(f"ReefBase Events data file not found at {path}. Ensure T013 ran successfully.")
    df = pd.read_csv(path)
    return df

# --- Merge Logic (T014) ---
def merge_datasets():
    """
    Merge data into a unified `data/processed/reef_species_unified.csv` with 5-km grid resolution.
    This implements the core logic for T014.
    """
    print("Starting data merge for T014...")
    
    # 1. Load all components
    try:
        climate_df = load_noaa_sst_dhw()
        traits_df = load_coral_traits()
        reefs_df = load_unep_reefs()
        events_df = load_reefbase_events()
    except FileNotFoundError as e:
        print(f"CRITICAL: Missing input data. {e}")
        print("Ensure T013 (Data Ingestion) has completed successfully to populate data/processed/ with source files.")
        raise

    # 2. Standardize Key Columns for Joining
    # Assume 'reef_id' is the common key. If not, we might need to join on lat/lon or name.
    # For this implementation, we assume T013 standardized the 'reef_id' in all source files.
    # If 'reef_id' is missing in any, we attempt to create it from coordinates if available.
    
    key_cols = ['reef_id', 'lon', 'lat']
    for df_name, df in [("climate", climate_df), ("traits", traits_df), ("reefs", reefs_df), ("events", events_df)]:
        if 'reef_id' not in df.columns:
            # Fallback: create a composite ID from lat/lon if possible, or raise
            if 'lon' in df.columns and 'lat' in df.columns:
                df['reef_id'] = df['reef_id'] = df['lat'].round(2).astype(str) + "_" + df['lon'].round(2).astype(str)
            else:
                raise ValueError(f"{df_name} data missing 'reef_id' and coordinates for ID generation.")

    # 3. Merge Strategy:
    # Start with Reefs (spatial reference) -> Join Climate -> Join Traits -> Join Events
    # We use 'outer' join initially to keep all reefs, then fill missing or drop as needed per T015/T016 later.
    # For T014, we produce the unified structure.

    unified_df = reefs_df[['reef_id', 'lon', 'lat']].copy()
    
    # Merge Climate (SST, DHW)
    climate_cols = ['reef_id', 'sst_avg', 'dhw_avg', 'max_dhw'] # Example columns
    if all(c in climate_df.columns for c in climate_cols):
        unified_df = unified_df.merge(climate_df[climate_cols], on='reef_id', how='left')
    else:
        # Attempt to merge whatever climate columns exist
        climate_cols = [c for c in climate_df.columns if c not in ['reef_id', 'lon', 'lat']]
        if climate_cols:
            unified_df = unified_df.merge(climate_df[['reef_id'] + climate_cols], on='reef_id', how='left')

    # Merge Traits
    trait_cols = [c for c in traits_df.columns if c not in ['reef_id', 'lon', 'lat']]
    if trait_cols:
        # Handle potential multiple traits per reef (e.g., multiple species)
        # For a unified CSV, we might need to pivot or take the first/mean.
        # Assuming one row per reef for simplicity in this merge step, or taking the first occurrence.
        traits_merged = traits_df.groupby('reef_id')[trait_cols].first().reset_index()
        unified_df = unified_df.merge(traits_merged, on='reef_id', how='left')

    # Merge Events
    event_cols = [c for c in events_df.columns if c not in ['reef_id', 'lon', 'lat']]
    if event_cols:
        events_merged = events_df.groupby('reef_id')[event_cols].first().reset_index() # Aggregate if multiple events
        unified_df = unified_df.merge(events_merged, on='reef_id', how='left')

    # 4. 5-km Grid Resolution Handling
    # "5-km grid resolution" implies spatial binning.
    # We round lat/lon to approximate 5km grid cells.
    # Approx 1 degree lat = 111km. 5km ~ 0.045 degrees.
    grid_size = 0.045
    unified_df['grid_lat'] = (unified_df['lat'] / grid_size).round() * grid_size
    unified_df['grid_lon'] = (unified_df['lon'] / grid_size).round() * grid_size
    
    # If multiple reefs fall into the same grid cell, we might need to aggregate again.
    # However, the task asks for a "unified CSV", usually row-per-observation.
    # If the requirement is strictly 1 row per grid cell, we would group by grid_lat/grid_lon.
    # Assuming the "reef_species" granularity is preserved but coordinates are snapped to grid.
    # If the user implies aggregating reefs into grid cells:
    # unified_df = unified_df.groupby(['grid_lat', 'grid_lon']).mean(numeric_only=True).reset_index()
    # But typically, "reef_species_unified" implies a row per reef-species pair.
    # We will keep the reef-level rows but with snapped coordinates as per "5-km grid resolution" requirement for alignment.

    # 5. Save Output
    output_path = Path(config.DATA_PROCESSED) / "reef_species_unified.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    unified_df.to_csv(output_path, index=False)
    print(f"Successfully merged data into {output_path}")
    print(f"Total rows: {len(unified_df)}")
    print(f"Columns: {list(unified_df.columns)}")
    
    return unified_df

# --- Imputation & Flagging (T015, T016) ---
def impute_missing_values(df):
    """
    Handle missing values by imputing with nearest valid temporal neighbor 
    or excluding rows if gaps exceed thresholds.
    """
    # This is a placeholder for the logic in T015. 
    # Since T014 produces the file, T015 will process it. 
    # However, to satisfy the "extend" constraint and ensure the script is runnable:
    # We will apply a simple forward-fill if time exists, else drop.
    if 'date' in df.columns:
        df = df.sort_values('date')
        df = df.ffill()
    return df

def flag_missing_trait_data(df):
    """
    Flag rows where species trait data is missing.
    """
    # Identify trait columns (heuristic: contains 'trait', 'tolerance', 'sensitivity')
    trait_cols = [c for c in df.columns if any(k in c.lower() for k in ['trait', 'tolerance', 'sensitivity', 'bleaching'])]
    if not trait_cols:
        return df

    df['trait_missing_flag'] = df[trait_cols].isnull().any(axis=1)
    return df

# --- Main Entry Point ---
def main():
    """
    Main function to execute the merge process for T014.
    """
    print("Executing T014: Merge data into unified CSV...")
    
    try:
        # Step 1: Merge
        unified_df = merge_datasets()
        
        # Step 2: Apply Imputation (T015 logic inline for completeness of the script)
        # Note: In a real pipeline, T015 might be a separate step, but we extend the script.
        unified_df = impute_missing_values(unified_df)
        
        # Step 3: Flag Missing Traits (T016 logic inline)
        unified_df = flag_missing_trait_data(unified_df)
        
        # Re-save with flags
        output_path = Path(config.DATA_PROCESSED) / "reef_species_unified.csv"
        unified_df.to_csv(output_path, index=False)
        print(f"Final unified dataset saved to {output_path}")
        
    except Exception as e:
        print(f"Error during merge: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
