import os
import sys
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import xarray as xr

from utils.logging_config import get_logger, setup_logging

# Ensure the code directory is in the path for relative imports if running as script
if __name__ == "__main__":
    code_dir = Path(__file__).parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

logger = get_logger(__name__)

# Configuration paths
DATA_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
LOGS_DIR = Path("data/logs")

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Constants for Quality Flags (MODIS)
# Based on standard Ocean Color Product Quality Flags
# 0 = Good, 1 = Cloud, 2 = High Aerosol, 3 = Glint, etc.
MODIS_CLOUD_FLAG = 1
MODIS_AEROSOL_FLAG = 2

def load_modis_quality_flags(modis_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load MODIS quality flags.
    If modis_path is not provided, attempts to find the file in data/raw.
    Returns a DataFrame with 'lat', 'lon', 'timestamp', 'quality_flag'.
    """
    if modis_path is None:
        # Look for common MODIS file patterns
        potential_paths = list(DATA_DIR.glob("modis*.nc")) + list(DATA_DIR.glob("MODIS*.nc"))
        if not potential_paths:
            raise FileNotFoundError("No MODIS data file found in data/raw/.")
        modis_path = str(potential_paths[0])

    logger.info(f"Loading MODIS quality flags from {modis_path}")
    ds = xr.open_dataset(modis_path)
    
    # Attempt to map standard variable names
    # This depends on the specific NetCDF structure from the fetch step
    # Assuming standard variables: 'lat', 'lon', 'time', 'quality_flags' or similar
    df = ds.to_dataframe().reset_index()
    
    # Normalize column names
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    # Identify quality flag column
    flag_col = None
    for col in ['quality_flag', 'qflag', 'l2_flags', 'flags']:
        if col in df.columns:
            flag_col = col
            break
    
    if flag_col is None:
        # Fallback: try to find any column with 'flag' in name
        flag_cols = [c for c in df.columns if 'flag' in c]
        if flag_cols:
            flag_col = flag_cols[0]
        else:
            raise ValueError("Could not identify quality flag column in MODIS data.")

    # Select relevant columns
    required_cols = ['lat', 'lon', 'time', flag_col]
    # Handle potential 'timestamp' vs 'time'
    if 'timestamp' in df.columns:
        required_cols = ['lat', 'lon', 'timestamp', flag_col]
    
    available_cols = [c for c in required_cols if c in df.columns]
    result_df = df[available_cols].copy()
    result_df.rename(columns={flag_col: 'quality_flag'}, inplace=True)
    
    return result_df

def load_reanalysis_data(reanalysis_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load Reanalysis data (Temp, Salinity, Nutrients).
    Returns DataFrame with 'lat', 'lon', 'timestamp', 'temp', 'salinity', 'nutrients'.
    """
    if reanalysis_path is None:
        potential_paths = list(DATA_DIR.glob("copernicus*.nc"))
        if not potential_paths:
            raise FileNotFoundError("No Reanalysis data file found in data/raw/.")
        reanalysis_path = str(potential_paths[0])

    logger.info(f"Loading Reanalysis data from {reanalysis_path}")
    ds = xr.open_dataset(reanalysis_path)
    df = ds.to_dataframe().reset_index()
    
    # Normalize columns
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    # Map standard variable names
    temp_col = next((c for c in ['temperature', 'temp', 't'] if c in df.columns), None)
    sal_col = next((c for c in ['salinity', 'sal', 's'] if c in df.columns), None)
    nut_col = next((c for c in ['nutrients', 'nut', 'nitrate', 'phosphate'] if c in df.columns), None)
    
    if not all([temp_col, sal_col]):
        raise ValueError("Reanalysis data missing required temperature or salinity columns.")
    
    # For nutrients, if not found, we might need to handle it as missing or use a proxy
    # But for this task, we assume the fetch step provided it or we handle it in filtering
    if nut_col:
        nutrient_data = df[nut_col]
    else:
        # If nutrients are missing in the file, we might need to handle this gracefully
        # For now, assume it's missing and we'll filter or impute later
        nutrient_data = pd.Series([np.nan] * len(df), index=df.index)

    result_df = pd.DataFrame({
        'lat': df['lat'],
        'lon': df['lon'],
        'timestamp': df['time'] if 'time' in df.columns else df['timestamp'],
        'temp': df[temp_col],
        'salinity': df[sal_col],
        'nutrients': nutrient_data
    })
    
    return result_df

def load_seabass_data(seabass_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load SeaBASS in-situ data.
    Returns DataFrame with 'lat', 'lon', 'timestamp', 'chl_a', 'sst', 'salinity'.
    """
    if seabass_path is None:
        potential_paths = list(DATA_DIR.glob("seabass*.csv"))
        if not potential_paths:
            raise FileNotFoundError("No SeaBASS data file found in data/raw/.")
        seabass_path = str(potential_paths[0])

    logger.info(f"Loading SeaBASS data from {seabass_path}")
    df = pd.read_csv(seabass_path)
    
    # Normalize columns
    df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    # Map standard variable names
    lat_col = next((c for c in ['latitude', 'lat'] if c in df.columns), 'lat')
    lon_col = next((c for c in ['longitude', 'lon'] if c in df.columns), 'lon')
    time_col = next((c for c in ['time', 'date', 'timestamp'] if c in df.columns), 'time')
    chl_col = next((c for c in ['chlorophyll_a', 'chl_a', 'chl'] if c in df.columns), None)
    sst_col = next((c for c in ['sea_surface_temp', 'sst', 'temp'] if c in df.columns), None)
    sal_col = next((c for c in ['salinity', 'sal'] if c in df.columns), None)
    
    if not all([lat_col, lon_col, time_col]):
        raise ValueError("SeaBASS data missing required location or time columns.")
    
    result_df = pd.DataFrame({
        'lat': df[lat_col],
        'lon': df[lon_col],
        'timestamp': df[time_col],
        'chl_a': df[chl_col] if chl_col else pd.Series([np.nan] * len(df), index=df.index),
        'sst': df[sst_col] if sst_col else pd.Series([np.nan] * len(df), index=df.index),
        'salinity': df[sal_col] if sal_col else pd.Series([np.nan] * len(df), index=df.index)
    })
    
    return result_df

def filter_modis_flags(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter MODIS pixels to exclude "cloud" (flag=1) or "high aerosol" (flag=2).
    Returns filtered DataFrame.
    """
    if df.empty:
        return df
    
    if 'quality_flag' not in df.columns:
        logger.warning("No quality_flag column found in MODIS data. Skipping flag filter.")
        return df
    
    # Keep only rows where quality_flag is NOT 1 (cloud) and NOT 2 (high aerosol)
    # Assuming flag=0 is good, and other flags (3, 4, etc.) are acceptable or handled separately
    # Spec says: exclude flag=1 and flag=2
    mask = ~df['quality_flag'].isin([MODIS_CLOUD_FLAG, MODIS_AEROSOL_FLAG])
    filtered_df = df[mask].copy()
    
    logger.info(f"Filtered MODIS data: {len(df)} -> {len(filtered_df)} rows (excluded cloud/high aerosol)")
    return filtered_df

def filter_reanalysis_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter Reanalysis anomalies.
    For this implementation, we define anomalies as:
    - Missing values in critical fields (temp, salinity)
    - Extreme outliers (e.g., temp < -2 or > 40, salinity < 0 or > 42)
    """
    if df.empty:
        return df
    
    mask = pd.Series([True] * len(df), index=df.index)
    
    # Check for missing critical values
    if 'temp' in df.columns:
        mask &= df['temp'].notna()
    if 'salinity' in df.columns:
        mask &= df['salinity'].notna()
    
    # Check for extreme outliers (physical limits)
    if 'temp' in df.columns:
        mask &= (df['temp'] >= -2.0) & (df['temp'] <= 40.0)
    if 'salinity' in df.columns:
        mask &= (df['salinity'] >= 0.0) & (df['salinity'] <= 42.0)
    
    filtered_df = df[mask].copy()
    logger.info(f"Filtered Reanalysis data: {len(df)} -> {len(filtered_df)} rows (removed anomalies)")
    return filtered_df

def filter_missing_in_situ(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude grid cells with missing in-situ data.
    For this task, we assume 'in-situ' refers to the SeaBASS data.
    We filter rows where critical in-situ variables are missing.
    """
    if df.empty:
        return df
    
    mask = pd.Series([True] * len(df), index=df.index)
    
    # Check for missing critical in-situ values
    # Depending on the specific requirements, we might need chl_a, sst, or salinity
    # For now, we require at least one of these to be present
    critical_cols = ['chl_a', 'sst', 'salinity']
    available_cols = [c for c in critical_cols if c in df.columns]
    
    if available_cols:
        mask &= df[available_cols].notna().any(axis=1)
    
    filtered_df = df[mask].copy()
    logger.info(f"Filtered In-situ data: {len(df)} -> {len(filtered_df)} rows (removed missing in-situ)")
    return filtered_df

def apply_unified_masking_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply a unified masking strategy for all missing data points.
    This function ensures that any row with missing values in critical columns is excluded.
    Critical columns are defined based on the combined dataset schema.
    """
    if df.empty:
        return df
    
    # Define critical columns for the unified dataset
    # Based on the aligned_dataset.schema.yaml: lat, lon, timestamp, basin, temp, salinity, nutrients, chlorophyll_a
    critical_cols = ['lat', 'lon', 'timestamp', 'temp', 'salinity', 'nutrients', 'chl_a']
    available_cols = [c for c in critical_cols if c in df.columns]
    
    if not available_cols:
        logger.warning("No critical columns found for unified masking. Returning original data.")
        return df
    
    # Create a mask where all critical columns are not NA
    mask = df[available_cols].notna().all(axis=1)
    
    filtered_df = df[mask].copy()
    logger.info(f"Applied unified masking: {len(df)} -> {len(filtered_df)} rows")
    return filtered_df

def main():
    """
    Main function to execute the quality flag filtering pipeline.
    1. Load MODIS, Reanalysis, and SeaBASS data.
    2. Apply specific filters for each dataset.
    3. Apply unified masking strategy.
    4. Output filtered dataset to data/raw/seabass_filtered.csv.
    """
    logger.info("Starting data ingestion and quality filtering pipeline (T015)")
    
    try:
        # Load data
        modis_df = load_modis_quality_flags()
        reanalysis_df = load_reanalysis_data()
        seabass_df = load_seabass_data()
        
        # Apply specific filters
        modis_filtered = filter_modis_flags(modis_df)
        reanalysis_filtered = filter_reanalysis_anomalies(reanalysis_df)
        seabass_filtered = filter_missing_in_situ(seabass_df)
        
        # For this task, the primary output is the filtered SeaBASS data.
        # The spec says: "Output filtered dataset to data/raw/seabass_filtered.csv"
        # We apply the unified masking strategy to the SeaBASS data.
        final_filtered_df = apply_unified_masking_strategy(seabass_filtered)
        
        # Ensure output directory exists
        output_path = DATA_DIR / "seabass_filtered.csv"
        
        # Write to CSV
        final_filtered_df.to_csv(output_path, index=False)
        logger.info(f"Filtered dataset written to {output_path}")
        
        # Log summary
        logger.info(f"Summary: Original SeaBASS rows: {len(seabass_df)}, Filtered: {len(final_filtered_df)}")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Setup logging
    setup_logging()
    main()
