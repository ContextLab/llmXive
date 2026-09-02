import os
import sys
import logging
import json
from pathlib import Path
import pandas as pd
import glob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
RAW_TARGET_DIR = PROJECT_ROOT / "data" / "raw" / "noaa-ar" / "target"
RAW_CONTROL_DIR = PROJECT_ROOT / "data" / "raw" / "noaa-ar" / "control"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

def load_noaa_raw_data(region: str) -> pd.DataFrame:
    """
    Loads raw NOAA AR catalog CSV files for a specific region.
    Expects files in data/raw/noaa-ar/<region>/*.csv
    """
    if region == "target":
        base_dir = RAW_TARGET_DIR
    elif region == "control":
        base_dir = RAW_CONTROL_DIR
    else:
        raise ValueError(f"Invalid region: {region}. Must be 'target' or 'control'.")

    if not base_dir.exists():
        raise FileNotFoundError(f"Raw data directory not found: {base_dir}")

    csv_files = glob.glob(str(base_dir / "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {base_dir}")

    logger.info(f"Loading {len(csv_files)} CSV files from {base_dir}...")
    dfs = []
    for f in csv_files:
        df = pd.read_csv(f)
        dfs.append(df)

    combined = pd.concat(dfs, ignore_index=True)
    
    # Ensure date column is parsed if it exists
    date_cols = [c for c in combined.columns if 'date' in c.lower() or 'time' in c.lower()]
    if date_cols:
        # Prefer 'date' or 'datetime' if available
        target_col = next((c for c in date_cols if c.lower() in ['date', 'datetime']), date_cols[0])
        combined[target_col] = pd.to_datetime(combined[target_col], errors='coerce')
        combined['date'] = combined[target_col].dt.to_period('M').dt.to_timestamp()
    else:
        # Fallback: assume first column is date-like or create a placeholder if data is missing
        # In a real scenario, the ingestion script ensures this column exists
        if not combined.empty:
            logger.warning("No date column detected. Attempting to infer or failing if data is empty.")
            # If ingestion worked, there should be a date. If not, we fail loudly.
            raise ValueError("No date column found in raw NOAA data. Ensure ingestion scripts ran correctly.")
        
    return combined

def filter_region(df: pd.DataFrame, region: str) -> pd.DataFrame:
    """
    Filters the dataframe to ensure it matches the requested region.
    Assumes the ingestion script already filtered, but we double-check if a region column exists.
    """
    if 'region' in df.columns:
        df = df[df['region'] == region]
    return df

def aggregate_monthly_ar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates Integrated Water Vapor Transport (IWVT) to monthly means.
    Expects a 'date' column (datetime) and an 'iwvt' or similar intensity column.
    """
    if df.empty:
        return df

    # Identify intensity column
    intensity_cols = [c for c in df.columns if 'iwvt' in c.lower() or 'intensity' in c.lower() or 'transport' in c.lower()]
    if not intensity_cols:
        raise ValueError("Could not find an Integrated Water Vapor Transport (IWVT) intensity column in the data.")
    
    intensity_col = intensity_cols[0]
    logger.info(f"Aggregating column '{intensity_col}' to monthly means.")

    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])

    # Extract year-month for grouping
    df['month'] = df['date'].dt.to_period('M')
    
    # Group by month and aggregate
    # We take the mean of the intensity. If multiple events per month, we average them.
    # The spec says "aggregates Integrated Water Vapor Transport to monthly means"
    monthly_df = df.groupby('month').agg({
        intensity_col: 'mean',
        'date': 'first' # Keep the first date of the month as the representative date
    }).reset_index()

    # Rename columns to match data model
    monthly_df = monthly_df.rename(columns={intensity_col: 'ar_intensity'})
    
    # Ensure 'date' is the first day of the month for consistency
    monthly_df['date'] = monthly_df['date'].dt.to_period('M').dt.to_timestamp()
    
    # Drop the temporary month column
    monthly_df = monthly_df.drop(columns=['month'])

    return monthly_df

def handle_missing_months(df: pd.DataFrame, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Logs warnings for missing months within the range of the data.
    Does not fill them, just reports.
    """
    if df.empty:
        return df

    if start_date is None:
        start_date = df['date'].min()
    if end_date is None:
        end_date = df['date'].max()

    # Generate full date range
    full_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    existing_dates = set(df['date'].dt.to_period('M'))
    
    missing = []
    for dt in full_range:
        if dt.to_period('M') not in existing_dates:
            missing.append(dt)

    if missing:
        logger.warning(f"Found {len(missing)} missing months: {[str(m) for m in missing]}")
    else:
        logger.info("No missing months detected in the date range.")

    return df

def exclude_zero_ar_months(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops months where total AR intensity equals zero.
    """
    initial_count = len(df)
    if 'ar_intensity' not in df.columns:
        logger.warning("No 'ar_intensity' column found. Skipping zero-intensity filter.")
        return df

    df = df[df['ar_intensity'] != 0]
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.info(f"Dropped {dropped} months where AR intensity was zero.")
    else:
        logger.info("No months with zero AR intensity found.")
    
    return df

def save_processed_data(df: pd.DataFrame, region: str) -> str:
    """
    Saves the processed dataframe to data/processed/noaa_preprocessed_<region>.csv
    """
    if df.empty:
        logger.warning(f"Processed data for {region} is empty. Saving empty file.")
    
    output_path = PROCESSED_DIR / f"noaa_preprocessed_{region}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data for {region} to {output_path}")
    return str(output_path)

def main():
    logger.info("=== NOAA AR Preprocessing Pipeline Start ===")
    
    regions = ["target", "control"]
    
    for region in regions:
        logger.info(f"Processing {region} region...")
        try:
            # 1. Load raw data
            df = load_noaa_raw_data(region)
            logger.info(f"Loaded {len(df)} rows for {region}.")
            
            # 2. Filter region (safety check)
            df = filter_region(df, region)
            
            if df.empty:
                logger.warning(f"No data found for {region} after filtering. Creating empty output.")
                save_processed_data(pd.DataFrame(columns=['date', 'ar_intensity']), region)
                continue

            # 3. Aggregate to monthly means
            monthly_df = aggregate_monthly_ar(df)
            
            # 4. Log missing months
            monthly_df = handle_missing_months(monthly_df)
            
            # 5. Drop zero intensity months
            monthly_df = exclude_zero_ar_months(monthly_df)
            
            # 6. Save
            save_processed_data(monthly_df, region)
            
        except Exception as e:
            logger.critical(f"Failed to process {region}: {e}")
            raise

    logger.info("=== NOAA AR Preprocessing Complete ===")

if __name__ == "__main__":
    main()