"""
NOAA AR Data Preprocessing Script (T017b)

This script aggregates NOAA Atmospheric River catalog data into monthly means
of Integrated Water Vapor Transport (IWVT). It handles missing months by logging
warnings and skipping them, and excludes months with zero AR events from the
final output to prevent bias in correlation calculations.

Dependencies:
    - pandas
    - numpy
    - logging
    - pathlib
    - json
"""

import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "noaa-ar"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_FILE = PROCESSED_DATA_DIR / "noaa_monthly_aggregated.csv"

# Region filter parameters (West Coast NA)
# Latitude: 35°N - 50°N
# Longitude: 120°W - 125°W (stored as negative in most datasets, or 235°E - 240°E)
LAT_MIN, LAT_MAX = 35.0, 50.0
LON_MIN, LON_MAX = -125.0, -120.0  # Adjust if source uses 0-360

def load_noaa_raw_data(input_dir: Path) -> pd.DataFrame:
    """
    Loads raw NOAA AR catalog data from the specified directory.
    Expects CSV files containing AR event data with columns like:
    'date', 'lat', 'lon', 'iwvt' (Integrated Water Vapor Transport), etc.
    """
    if not input_dir.exists():
        raise FileNotFoundError(f"Raw NOAA data directory not found: {input_dir}")

    csv_files = list(input_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {input_dir}")

    logger.info(f"Loading {len(csv_files)} CSV files from {input_dir}")
    dfs = []
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            dfs.append(df)
            logger.debug(f"Loaded {file_path.name}: {len(df)} rows")
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            raise

    combined_df = pd.concat(dfs, ignore_index=True)
    logger.info(f"Total raw rows loaded: {len(combined_df)}")
    return combined_df

def filter_region(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the dataframe to the West Coast NA region.
    Handles potential coordinate system differences (e.g., 0-360 vs -180-180).
    """
    logger.info("Filtering data to West Coast NA region (35°N-50°N, 120°W-125°W)")

    # Normalize longitude to -180 to 180 if necessary
    # If LON_MIN/LON_MAX are negative, assume data might be 0-360
    if LON_MIN < 0 and 'lon' in df.columns:
        # Check if values are > 180 (indicating 0-360 system)
        if df['lon'].max() > 180:
            logger.info("Detected 0-360 longitude system, converting to -180 to 180")
            df = df.copy()
            df['lon'] = df['lon'].apply(lambda x: x - 360 if x > 180 else x)

    # Apply filters
    mask = (
        (df['lat'] >= LAT_MIN) &
        (df['lat'] <= LAT_MAX) &
        (df['lon'] >= LON_MIN) &
        (df['lon'] <= LON_MAX)
    )

    filtered_df = df[mask].copy()
    logger.info(f"Filtered rows: {len(filtered_df)} ({len(df) - len(filtered_df)} removed)")
    return filtered_df

def aggregate_monthly_ar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates AR data to monthly mean IWVT.
    
    Steps:
    1. Ensure 'date' is datetime.
    2. Extract 'year' and 'month'.
    3. Group by year/month.
    4. Calculate mean IWVT.
    5. Count events per month.
    6. Filter out months with zero events (handled by count > 0 naturally, 
       but we explicitly exclude rows where count is 0 if they exist).
    """
    logger.info("Aggregating to monthly resolution")

    if 'date' not in df.columns:
        raise ValueError("Input dataframe must contain a 'date' column.")
    
    if 'iwvt' not in df.columns:
        # Try common aliases
        if 'integrated_water_vapor_transport' in df.columns:
            df = df.rename(columns={'integrated_water_vapor_transport': 'iwvt'})
        else:
            raise ValueError("Input dataframe must contain an 'iwvt' or 'integrated_water_vapor_transport' column.")

    df['date'] = pd.to_datetime(df['date'])
    df['year_month'] = df['date'].dt.to_period('M')
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month

    # Aggregate
    monthly_stats = df.groupby(['year', 'month', 'year_month']).agg(
        ar_intensity_mean=('iwvt', 'mean'),
        ar_intensity_std=('iwvt', 'std'),
        event_count=('iwvt', 'count')
    ).reset_index()

    # Ensure event_count is integer
    monthly_stats['event_count'] = monthly_stats['event_count'].astype(int)

    # Exclude months with zero AR events (though groupby naturally only includes existing months)
    # If the dataset has gaps where no events occurred, they won't be in the dataframe.
    # This step ensures we don't accidentally include rows with count=0 if they were injected.
    monthly_stats = monthly_stats[monthly_stats['event_count'] > 0].copy()

    logger.info(f"Aggregated to {len(monthly_stats)} months with AR events")
    return monthly_stats

def handle_missing_months(monthly_df: pd.DataFrame, start_year: int = 2018, end_year: int = 2024) -> pd.DataFrame:
    """
    Identifies missing months in the sequence.
    Logs warnings for missing months but does not fill them with NaN to avoid
    biasing the correlation calculation (as per task requirements).
    Returns the dataframe as is, but logs the gaps.
    """
    logger.info("Checking for missing months in the time series")
    
    # Create a full range of expected months
    date_range = pd.date_range(
        start=f'{start_year}-01-01',
        end=f'{end_year}-12-01',
        freq='MS'
    )
    
    expected_months = date_range.to_period('M')
    actual_months = monthly_df['year_month'].astype(str)
    
    missing = []
    for month in expected_months:
        if str(month) not in actual_months:
            missing.append(str(month))
    
    if missing:
        logger.warning(f"Found {len(missing)} missing months: {missing[:10]}{'...' if len(missing) > 10 else ''}")
    else:
        logger.info("No missing months detected in the range.")
    
    # Return original dataframe (missing months are simply excluded from correlation)
    return monthly_df

def save_processed_data(df: pd.DataFrame, output_path: Path):
    """
    Saves the processed dataframe to CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format date column for output
    df_out = df.copy()
    df_out['date'] = df_out['year_month'].dt.to_timestamp().dt.strftime('%Y-%m-%d')
    df_out = df_out.drop(columns=['year', 'month', 'year_month'])
    
    # Reorder columns
    cols = ['date', 'ar_intensity_mean', 'ar_intensity_std', 'event_count']
    df_out = df_out[cols]
    
    df_out.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")

def main():
    """
    Main execution flow for T017b.
    """
    try:
        # 1. Load Raw Data
        raw_df = load_noaa_raw_data(RAW_DATA_DIR)
        
        # 2. Filter Region
        filtered_df = filter_region(raw_df)
        
        if filtered_df.empty:
            logger.error("No data found in the target region. Exiting.")
            sys.exit(1)
        
        # 3. Aggregate Monthly
        monthly_df = aggregate_monthly_ar(filtered_df)
        
        # 4. Handle Missing Months (Logging only)
        final_df = handle_missing_months(monthly_df)
        
        # 5. Save Output
        save_processed_data(final_df, OUTPUT_FILE)
        
        logger.info("T017b completed successfully.")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()