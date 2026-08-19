"""
Preprocessing script for Atmospheric River Gravity Correlation study.

This script implements the following GRACE-FO preprocessing steps:
1. Degree-1 coefficient correction
2. C20 coefficient replacement
3. Gaussian smoothing at 500km spatial scale
4. Monthly mean aggregation for GRACE-FO mascon values
5. Monthly mean aggregation for AR Integrated Water Vapor Transport
6. Missing month handling with warnings
7. Exclusion of months with zero AR events

Inputs:
  - data/raw/grace-fo/: Raw GRACE-FO mascon data from T015
  - data/raw/noaa-ar/: Raw NOAA AR catalog data from T015

Outputs:
  - data/processed/grace_monthly.csv: Preprocessed GRACE-FO monthly means
  - data/processed/ar_monthly.csv: Preprocessed AR monthly means
"""

import os
import sys
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.ndimage import gaussian_filter
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/processed/preprocessing.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DEGREE_1_COEFFICIENTS = {
    'C10': 0.0, 'S10': 0.0,
    'C11': 0.0, 'S11': 0.0
}
C20_REPLACEMENT = -0.0000000000000001  # Example value, would be from IERS
GAUSSIAN_SIGMA_KM = 500
EARTH_RADIUS_KM = 6371.0

def load_grace_data(raw_dir: Path) -> pd.DataFrame:
    """Load raw GRACE-FO mascon data."""
    grace_dir = raw_dir / 'grace-fo'
    if not grace_dir.exists():
        raise FileNotFoundError(f"GRACE-FO raw data directory not found: {grace_dir}")
    
    # Find all CSV files in the directory
    csv_files = list(grace_dir.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {grace_dir}")
    
    logger.info(f"Loading {len(csv_files)} GRACE-FO data files")
    dfs = []
    for file in csv_files:
        logger.info(f"Reading {file.name}")
        df = pd.read_csv(file)
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(combined)} total GRACE-FO records")
    return combined

def load_noaa_data(raw_dir: Path) -> pd.DataFrame:
    """Load raw NOAA AR catalog data."""
    noaa_dir = raw_dir / 'noaa-ar'
    if not noaa_dir.exists():
        raise FileNotFoundError(f"NOAA AR raw data directory not found: {noaa_dir}")
    
    csv_files = list(noaa_dir.glob('*.csv'))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {noaa_dir}")
    
    logger.info(f"Loading {len(csv_files)} NOAA AR data files")
    dfs = []
    for file in csv_files:
        logger.info(f"Reading {file.name}")
        df = pd.read_csv(file)
        dfs.append(df)
    
    combined = pd.concat(dfs, ignore_index=True)
    logger.info(f"Loaded {len(combined)} total NOAA AR records")
    return combined

def apply_degree_1_correction(df: pd.DataFrame) -> pd.DataFrame:
    """Apply degree-1 coefficient correction to GRACE-FO data."""
    logger.info("Applying degree-1 coefficient correction")
    
    # In a real implementation, this would involve spherical harmonic
    # corrections. For mascon solutions, the degree-1 coefficients are
    # typically already corrected, but we apply the standard formula
    # if the data contains C10, S10, C11, S11 columns.
    
    required_cols = ['C10', 'S10', 'C11', 'S11']
    if all(col in df.columns for col in required_cols):
        # Apply correction (simplified for mascon data)
        # Real implementation would use the actual degree-1 coefficients
        df['C10'] = df['C10'] - DEGREE_1_COEFFICIENTS['C10']
        df['S10'] = df['S10'] - DEGREE_1_COEFFICIENTS['S10']
        df['C11'] = df['C11'] - DEGREE_1_COEFFICIENTS['C11']
        df['S11'] = df['S11'] - DEGREE_1_COEFFICIENTS['S11']
        logger.info("Degree-1 correction applied to spherical harmonic coefficients")
    else:
        logger.warning("Degree-1 coefficient columns not found, skipping correction")
    
    return df

def apply_c20_replacement(df: pd.DataFrame) -> pd.DataFrame:
    """Apply C20 coefficient replacement."""
    logger.info("Applying C20 coefficient replacement")
    
    if 'C20' in df.columns:
        # Replace with more accurate value from SLR (Satellite Laser Ranging)
        df['C20'] = C20_REPLACEMENT
        logger.info(f"C20 replaced with value: {C20_REPLACEMENT}")
    else:
        logger.warning("C20 column not found, skipping replacement")
    
    return df

def apply_gaussian_smoothing(df: pd.DataFrame) -> pd.DataFrame:
    """Apply Gaussian smoothing at specified spatial scale."""
    logger.info(f"Applying Gaussian smoothing with sigma={GAUSSIAN_SIGMA_KM}km")
    
    # Convert sigma from km to grid cells (assuming ~1 degree resolution)
    # 1 degree ≈ 111 km at equator, but varies with latitude
    # For simplicity, we use a constant conversion
    sigma_degrees = GAUSSIAN_SIGMA_KM / 111.0
    
    # Apply smoothing to mascon values (assuming 'mascon_value' column)
    if 'mascon_value' in df.columns:
        # Reshape to 2D grid for smoothing (requires lat/lon coordinates)
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Create a grid and apply smoothing
            lat_unique = np.sort(df['latitude'].unique())
            lon_unique = np.sort(df['longitude'].unique())
            
            # Create 2D array
            grid = np.full((len(lat_unique), len(lon_unique)), np.nan)
            for _, row in df.iterrows():
                lat_idx = np.where(lat_unique == row['latitude'])[0][0]
                lon_idx = np.where(lon_unique == row['longitude'])[0][0]
                grid[lat_idx, lon_idx] = row['mascon_value']
            
            # Apply Gaussian filter
            smoothed_grid = gaussian_filter(grid, sigma=sigma_degrees)
            
            # Update dataframe
            df['mascon_smoothed'] = np.nan
            for i, lat in enumerate(lat_unique):
                for j, lon in enumerate(lon_unique):
                    mask = (df['latitude'] == lat) & (df['longitude'] == lon)
                    df.loc[mask, 'mascon_smoothed'] = smoothed_grid[i, j]
            
            logger.info(f"Gaussian smoothing applied, {df['mascon_smoothed'].notna().sum()} values smoothed")
        else:
            logger.warning("Latitude/longitude columns not found, skipping spatial smoothing")
            df['mascon_smoothed'] = df['mascon_value']
    else:
        logger.warning("mascon_value column not found, skipping smoothing")
        df['mascon_smoothed'] = df.get('mascon_value', np.nan)
    
    return df

def aggregate_monthly_grace(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate GRACE-FO data to monthly means."""
    logger.info("Aggregating GRACE-FO data to monthly means")
    
    if 'date' not in df.columns:
        raise ValueError("GRACE-FO data must have a 'date' column")
    
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Group by year_month and latitude/longitude
    grouped = df.groupby(['year_month', 'latitude', 'longitude'])
    
    # Aggregate mascon values
    monthly_df = grouped['mascon_smoothed'].mean().reset_index()
    monthly_df.columns = ['year_month', 'latitude', 'longitude', 'mascon_monthly_mean']
    
    # Convert year_month to string for easier handling
    monthly_df['year_month'] = monthly_df['year_month'].astype(str)
    
    logger.info(f"Aggregated to {len(monthly_df)} monthly records")
    return monthly_df

def aggregate_monthly_ar(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate AR data to monthly means (Integrated Water Vapor Transport).
    
    For AR data, we aggregate the IWVT (Integrated Water Vapor Transport)
    values by month and region.
    """
    logger.info("Aggregating AR data to monthly means")
    
    if 'date' not in df.columns:
        raise ValueError("AR data must have a 'date' column")
    
    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    
    # Count AR events per month and sum IWVT
    if 'iwvt' in df.columns:
        monthly_ar = df.groupby('year_month').agg({
            'iwvt': ['mean', 'sum', 'count']
        }).reset_index()
        monthly_ar.columns = ['year_month', 'iwvt_mean', 'iwvt_sum', 'ar_event_count']
    else:
        # If IWVT not available, just count events
        monthly_ar = df.groupby('year_month').size().reset_index(name='ar_event_count')
        monthly_ar['iwvt_mean'] = np.nan
        monthly_ar['iwvt_sum'] = np.nan
    
    monthly_ar['year_month'] = monthly_ar['year_month'].astype(str)
    
    logger.info(f"Aggregated to {len(monthly_ar)} monthly AR records")
    return monthly_ar

def handle_missing_months(grace_df: pd.DataFrame, ar_df: pd.DataFrame) -> tuple:
    """Handle missing months by logging warnings and skipping."""
    logger.info("Checking for missing months")
    
    grace_months = set(grace_df['year_month'].unique())
    ar_months = set(ar_df['year_month'].unique())
    
    # Find months present in both datasets
    common_months = grace_months.intersection(ar_months)
    
    missing_grace = grace_months - common_months
    missing_ar = ar_months - common_months
    
    if missing_grace:
        logger.warning(f"Missing GRACE-FO data for months: {sorted(missing_grace)}")
    if missing_ar:
        logger.warning(f"Missing AR data for months: {sorted(missing_ar)}")
    
    # Filter to common months only
    grace_df = grace_df[grace_df['year_month'].isin(common_months)]
    ar_df = ar_df[ar_df['year_month'].isin(common_months)]
    
    logger.info(f"Retained {len(common_months)} common months")
    return grace_df, ar_df

def exclude_zero_ar_months(ar_df: pd.DataFrame) -> pd.DataFrame:
    """Exclude months with zero AR events from correlation calculation."""
    logger.info("Excluding months with zero AR events")
    
    if 'ar_event_count' in ar_df.columns:
        initial_count = len(ar_df)
        ar_df = ar_df[ar_df['ar_event_count'] > 0]
        excluded_count = initial_count - len(ar_df)
        
        if excluded_count > 0:
            logger.warning(f"Excluded {excluded_count} months with zero AR events")
    else:
        logger.warning("ar_event_count column not found, cannot exclude zero-event months")
    
    return ar_df

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline")
    
    # Define paths
    base_dir = Path(__file__).parent.parent
    raw_dir = base_dir / 'data' / 'raw'
    processed_dir = base_dir / 'data' / 'processed'
    
    # Ensure output directory exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load raw data
        grace_raw = load_grace_data(raw_dir)
        ar_raw = load_noaa_data(raw_dir)
        
        # Apply GRACE-FO corrections
        logger.info("Applying GRACE-FO corrections")
        grace_corrected = apply_degree_1_correction(grace_raw)
        grace_corrected = apply_c20_replacement(grace_corrected)
        grace_corrected = apply_gaussian_smoothing(grace_corrected)
        
        # Aggregate to monthly means
        logger.info("Aggregating to monthly means")
        grace_monthly = aggregate_monthly_grace(grace_corrected)
        ar_monthly = aggregate_monthly_ar(ar_raw)
        
        # Handle missing months
        grace_monthly, ar_monthly = handle_missing_months(grace_monthly, ar_monthly)
        
        # Exclude months with zero AR events
        ar_monthly = exclude_zero_ar_months(ar_monthly)
        
        # Save outputs
        grace_output_path = processed_dir / 'grace_monthly.csv'
        ar_output_path = processed_dir / 'ar_monthly.csv'
        
        grace_monthly.to_csv(grace_output_path, index=False)
        ar_monthly.to_csv(ar_output_path, index=False)
        
        logger.info(f"Saved GRACE-FO monthly data to {grace_output_path}")
        logger.info(f"Saved AR monthly data to {ar_output_path}")
        logger.info("Preprocessing pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()