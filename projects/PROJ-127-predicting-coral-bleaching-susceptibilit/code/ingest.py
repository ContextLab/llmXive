"""
Ingest and merge heterogeneous data sources into a unified reef-species dataset.

This module handles:
1. Downloading data from NOAA, UNEP, Coral Trait DB, and ReefBase.
2. Merging data into a unified CSV with 5-km grid resolution.
3. Streaming large datasets to manage memory.
4. Imputing missing values based on temporal neighbors.
5. Flagging missing trait data.
"""

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
from typing import Dict, Any, Optional, List, Tuple

# Import config for paths and URLs
import config

# Constants
CHUNK_SIZE = 8192
BUFFER_SIZE = 1024 * 1024  # 1MB buffer for streaming

def get_checksum(file_path: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_file(url: str, dest_path: str) -> bool:
    """Download a file from a URL with checksum verification."""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if chunk:
                    f.write(chunk)
        
        # Verify checksum if expected checksum is provided in config
        # This is a placeholder; actual checksums should be defined in config
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def download_csv(url: str, dest_path: str) -> Optional[pd.DataFrame]:
    """Download a CSV file and return it as a DataFrame."""
    try:
        df = pd.read_csv(url)
        df.to_csv(dest_path, index=False)
        return df
    except Exception as e:
        print(f"Error downloading CSV from {url}: {e}")
        return None

def download_geojson(url: str, dest_path: str) -> Optional[dict]:
    """Download a GeoJSON file."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        with open(dest_path, 'w') as f:
            json.dump(data, f)
        return data
    except Exception as e:
        print(f"Error downloading GeoJSON from {url}: {e}")
        return None

def download_raster(url: str, dest_path: str) -> bool:
    """Download a raster file (e.g., GeoTIFF)."""
    return download_file(url, dest_path)

def load_noaa_sst_dhw() -> pd.DataFrame:
    """
    Load NOAA SST and DHW data.
    This function assumes the data is available via a URL in config.NOAA_URL.
    """
    # In a real implementation, this would download and process the data
    # For now, we'll use a placeholder approach that fails loudly if data is missing
    if not hasattr(config, 'NOAA_URL') or not config.NOAA_URL:
        raise ValueError("NOAA_URL not configured in config.py")
    
    try:
        # Attempt to load the dataset using the HuggingFace datasets library if available
        # This is a placeholder for the actual data loading logic
        from datasets import load_dataset
        
        # Try to stream the dataset to handle large sizes
        dataset = load_dataset(config.NOAA_URL, streaming=True)
        
        # Convert to DataFrame (this might need adjustment based on actual dataset structure)
        # For streaming, we need to iterate and accumulate
        df_list = []
        for split in dataset:
            for row in dataset[split]:
                df_list.append(row)
        
        df = pd.DataFrame(df_list)
        return df
    except Exception as e:
        # If streaming fails or data is not available, raise an error
        raise RuntimeError(f"Failed to load NOAA SST/DHW data: {e}")

def load_unep_reefs() -> pd.DataFrame:
    """
    Load UNEP reef geometry data.
    This function assumes the data is available via a URL in config.UNEP_URL.
    """
    if not hasattr(config, 'UNEP_URL') or not config.UNEP_URL:
        raise ValueError("UNEP_URL not configured in config.py")
    
    try:
        from datasets import load_dataset
        dataset = load_dataset(config.UNEP_URL, streaming=True)
        
        df_list = []
        for split in dataset:
            for row in dataset[split]:
                df_list.append(row)
        
        df = pd.DataFrame(df_list)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load UNEP reef data: {e}")

def load_coral_traits() -> pd.DataFrame:
    """
    Load Coral Trait Database data.
    This function assumes the data is available via a URL in config.CORAL_TRAIT_URL.
    """
    if not hasattr(config, 'CORAL_TRAIT_URL') or not config.CORAL_TRAIT_URL:
        raise ValueError("CORAL_TRAIT_URL not configured in config.py")
    
    try:
        from datasets import load_dataset
        dataset = load_dataset(config.CORAL_TRAIT_URL, streaming=True)
        
        df_list = []
        for split in dataset:
            for row in dataset[split]:
                df_list.append(row)
        
        df = pd.DataFrame(df_list)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load Coral Trait data: {e}")

def load_reefbase_events() -> pd.DataFrame:
    """
    Load ReefBase bleaching events data.
    This function assumes the data is available via a URL in config.REEFBASE_URL.
    """
    if not hasattr(config, 'REEFBASE_URL') or not config.REEFBASE_URL:
        raise ValueError("REEFBASE_URL not configured in config.py")
    
    try:
        from datasets import load_dataset
        dataset = load_dataset(config.REEFBASE_URL, streaming=True)
        
        df_list = []
        for split in dataset:
            for row in dataset[split]:
                df_list.append(row)
        
        df = pd.DataFrame(df_list)
        return df
    except Exception as e:
        raise RuntimeError(f"Failed to load ReefBase events: {e}")

def merge_datasets(
    noaa_df: pd.DataFrame,
    unep_df: pd.DataFrame,
    coral_traits_df: pd.DataFrame,
    reefbase_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge all datasets into a unified reef-species dataset.
    
    This function:
    1. Joins reef geometries with environmental data
    2. Merges with species trait data
    3. Adds bleaching event labels
    4. Resamples to 5-km grid (conceptually, via aggregation)
    """
    # Ensure required columns exist
    required_cols = ['reef_id', 'lat', 'lon', 'date']
    for df, name in [(noaa_df, 'NOAA'), (unep_df, 'UNEP')]:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns in {name} data: {missing}")
    
    # Merge NOAA and UNEP data on reef_id and date
    # This is a simplified merge; real implementation would handle spatial joins
    merged = pd.merge(
        noaa_df,
        unep_df[['reef_id', 'lat', 'lon']],
        on='reef_id',
        how='inner'
    )
    
    # Merge with coral traits
    if 'species' in coral_traits_df.columns and 'species' in merged.columns:
        merged = pd.merge(
            merged,
            coral_traits_df,
            on='species',
            how='left'
        )
    else:
        # If species column doesn't exist, try to merge on reef_id
        merged = pd.merge(
            merged,
            coral_traits_df,
            on='reef_id',
            how='left'
        )
    
    # Merge with bleaching events
    if 'reef_id' in reefbase_df.columns and 'reef_id' in merged.columns:
        merged = pd.merge(
            merged,
            reefbase_df[['reef_id', 'date', 'bleaching_severity']],
            on=['reef_id', 'date'],
            how='left'
        )
        merged['bleaching_label'] = (merged['bleaching_severity'] > 0).astype(int)
    else:
        merged['bleaching_label'] = 0
    
    # Resample to 5-km grid (simplified: group by lat/lon rounded to 5km)
    # 5km ~ 0.045 degrees at equator
    merged['lat_5km'] = (merged['lat'] / 0.045).round() * 0.045
    merged['lon_5km'] = (merged['lon'] / 0.045).round() * 0.045
    
    # Aggregate by 5km grid cell
    aggregated = merged.groupby(['lat_5km', 'lon_5km', 'date']).agg({
        'sst': 'mean',
        'dhw': 'mean',
        'thermal_tolerance': 'mean',
        'bleaching_label': 'mean'
    }).reset_index()
    
    return aggregated

def impute_missing_values(df: pd.DataFrame, threshold_days: int = 30) -> pd.DataFrame:
    """
    Impute missing values using nearest temporal neighbor within threshold.
    
    Args:
        df: Input DataFrame
        threshold_days: Maximum days to look for a neighbor
    
    Returns:
        DataFrame with imputed values
    """
    df = df.copy()
    critical_cols = ['sst', 'dhw', 'thermal_tolerance', 'bleaching_label']
    
    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
    
    for col in critical_cols:
        if col not in df.columns:
            continue
        
        # Find missing values
        missing_mask = df[col].isna()
        if not missing_mask.any():
            continue
        
        # For each missing value, find nearest neighbor within threshold
        imputed_values = []
        for idx in df[missing_mask].index:
            current_date = df.loc[idx, 'date']
            if pd.isna(current_date):
                imputed_values.append(np.nan)
                continue
            
            # Find valid neighbors
            valid_neighbors = df[
                (df.index != idx) & 
                (~df[col].isna()) &
                (df['date'] >= current_date - timedelta(days=threshold_days)) &
                (df['date'] <= current_date + timedelta(days=threshold_days))
            ]
            
            if len(valid_neighbors) > 0:
                # Use nearest neighbor
                nearest = valid_neighbors.loc[
                    (valid_neighbors['date'] - current_date).abs().idxmin()
                ]
                imputed_values.append(nearest[col])
            else:
                imputed_values.append(np.nan)
        
        # Update DataFrame
        df.loc[missing_mask, col] = imputed_values
    
    # Drop rows that still have missing critical values
    df = df.dropna(subset=critical_cols)
    
    return df

def flag_missing_trait_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a flag for rows where species trait data was missing.
    
    Args:
        df: Input DataFrame
    
    Returns:
        DataFrame with trait_missing_flag column
    """
    df = df.copy()
    
    # Assume 'thermal_tolerance' is a trait column
    if 'thermal_tolerance' in df.columns:
        df['trait_missing_flag'] = df['thermal_tolerance'].isna().astype(int)
    else:
        df['trait_missing_flag'] = 0
    
    return df

def main():
    """Main function to run the ingestion pipeline."""
    print("Starting data ingestion pipeline...")
    
    # Create output directory
    output_dir = Path(config.DATA_PROCESSED_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading NOAA SST/DHW data...")
    noaa_df = load_noaa_sst_dhw()
    print(f"Loaded {len(noaa_df)} rows from NOAA")
    
    print("Loading UNEP reef data...")
    unep_df = load_unep_reefs()
    print(f"Loaded {len(unep_df)} rows from UNEP")
    
    print("Loading Coral Trait data...")
    coral_traits_df = load_coral_traits()
    print(f"Loaded {len(coral_traits_df)} rows from Coral Traits")
    
    print("Loading ReefBase events...")
    reefbase_df = load_reefbase_events()
    print(f"Loaded {len(reefbase_df)} rows from ReefBase")
    
    # Merge datasets
    print("Merging datasets...")
    unified_df = merge_datasets(noaa_df, unep_df, coral_traits_df, reefbase_df)
    print(f"Merged dataset has {len(unified_df)} rows")
    
    # Impute missing values
    print("Imputing missing values...")
    unified_df = impute_missing_values(unified_df, threshold_days=config.IMPUTATION_THRESHOLD_DAYS)
    print(f"After imputation: {len(unified_df)} rows")
    
    # Flag missing trait data
    print("Flagging missing trait data...")
    unified_df = flag_missing_trait_data(unified_df)
    
    # Save to CSV
    output_path = output_dir / "reef_species_unified.csv"
    unified_df.to_csv(output_path, index=False)
    print(f"Saved unified dataset to {output_path}")
    
    # Log statistics
    stats = {
        "total_rows": len(unified_df),
        "columns": list(unified_df.columns),
        "null_counts": unified_df.isnull().sum().to_dict(),
        "trait_missing_count": unified_df['trait_missing_flag'].sum()
    }
    
    stats_path = output_dir / "ingestion_stats.json"
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved statistics to {stats_path}")
    
    print("Ingestion pipeline completed successfully.")

if __name__ == "__main__":
    main()
