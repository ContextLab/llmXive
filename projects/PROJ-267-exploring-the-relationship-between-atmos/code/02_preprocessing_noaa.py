import pandas as pd
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def load_noaa_raw_data(region_type: str) -> pd.DataFrame:
    """
    Load raw NOAA AR catalog data for a specific region.
    
    Args:
        region_type: 'target' or 'control'
        
    Returns:
        DataFrame with raw AR data
        
    Raises:
        FileNotFoundError: If the raw data file does not exist
    """
    base_path = Path("data/raw/noaa-ar") / region_type
    input_file = base_path / "noaa_data.csv"
    
    if not input_file.exists():
        raise FileNotFoundError(
            f"Raw NOAA data file not found: {input_file}. "
            f"Ensure T016 (target) or T016b (control) has been executed successfully."
        )
    
    logger.info(f"Loading raw NOAA data from {input_file}")
    df = pd.read_csv(input_file)
    
    # Validate expected columns
    required_cols = ['date', 'IWV_transport']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_file}: {missing_cols}")
    
    return df

def aggregate_monthly_ar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate Integrated Water Vapor Transport to monthly means.
    
    Args:
        df: DataFrame with 'date' and 'IWV_transport' columns
        
    Returns:
        DataFrame with monthly aggregated data
    """
    logger.info("Aggregating AR intensity to monthly means...")
    
    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Create a month period for grouping
    df['month'] = df['date'].dt.to_period('M')
    
    # Aggregate by month
    monthly_df = df.groupby('month').agg({
        'IWV_transport': 'mean'
    }).reset_index()
    
    # Rename columns to match schema
    monthly_df = monthly_df.rename(columns={
        'IWV_transport': 'ar_intensity',
        'month': 'date'
    })
    
    # Convert date back to string format for consistency (YYYY-MM)
    monthly_df['date'] = monthly_df['date'].astype(str)
    
    return monthly_df

def handle_missing_months(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Log warnings for any missing months in the time series.
    
    Args:
        df: DataFrame with 'date' column
        start_date: Optional start date string (YYYY-MM)
        end_date: Optional end date string (YYYY-MM)
        
    Returns:
        DataFrame (unchanged, but logs warnings)
    """
    if start_date is None or end_date is None:
        # Infer range from data
        start_date = df['date'].min()
        end_date = df['date'].max()
    
    # Generate expected monthly range
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')
    expected_months = dates.strftime('%Y-%m').tolist()
    
    existing_months = df['date'].tolist()
    missing = [m for m in expected_months if m not in existing_months]
    
    if missing:
        logger.warning(f"Missing {len(missing)} months in dataset: {missing[:5]}...")
    else:
        logger.info("No missing months detected in the time series.")
        
    return df

def exclude_zero_ar_months(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drop months where total AR intensity equals zero or is NaN.
    
    Args:
        df: DataFrame with 'ar_intensity' column
        
    Returns:
        Filtered DataFrame
    """
    initial_count = len(df)
    
    # Drop rows where ar_intensity is zero or NaN
    df = df[df['ar_intensity'] > 0]
    df = df.dropna(subset=['ar_intensity'])
    
    dropped_count = initial_count - len(df)
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} months with zero or NaN AR intensity.")
    else:
        logger.info("No months with zero or NaN AR intensity found.")
        
    return df

def save_processed_data(df: pd.DataFrame, region_type: str) -> str:
    """
    Save processed data to the specified output path.
    
    Args:
        df: Processed DataFrame
        region_type: 'target' or 'control'
        
    Returns:
        Path to the saved file
    """
    output_dir = Path("data/processed")
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / f"noaa_preprocessed_{region_type}.csv"
    
    logger.info(f"Saving processed data to {output_file}")
    df.to_csv(output_file, index=False)
    
    logger.info(f"Successfully saved {len(df)} rows to {output_file}")
    return str(output_file)

def main():
    """Main entry point for NOAA preprocessing."""
    logger.info("=== NOAA Preprocessing Pipeline Start ===")
    
    regions = ['target', 'control']
    
    for region in regions:
        try:
            logger.info(f"--- Processing {region.upper()} region ---")
            
            # 1. Load raw data
            raw_df = load_noaa_raw_data(region)
            
            # 2. Aggregate to monthly means
            monthly_df = aggregate_monthly_ar(raw_df)
            
            # 3. Check for missing months
            monthly_df = handle_missing_months(monthly_df)
            
            # 4. Drop zero-intensity months
            clean_df = exclude_zero_ar_months(monthly_df)
            
            # 5. Save processed data
            output_path = save_processed_data(clean_df, region)
            
            logger.info(f"{region.upper()} processing complete: {output_path}")
            
        except FileNotFoundError as e:
            logger.error(f"Failed to process {region}: {e}")
            logger.error("Please ensure T016 (target) or T016b (control) has been executed first.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Unexpected error processing {region}: {e}")
            raise
    
    logger.info("=== NOAA Preprocessing Pipeline Complete ===")

if __name__ == "__main__":
    main()