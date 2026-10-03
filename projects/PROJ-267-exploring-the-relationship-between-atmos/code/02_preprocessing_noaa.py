import pandas as pd
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def load_noaa_raw_data(file_path: str) -> pd.DataFrame:
    """
    Loads the raw NOAA AR catalog data from a CSV file.
    
    Args:
        file_path (str): Path to the raw CSV file.
        
    Returns:
        pd.DataFrame: Loaded DataFrame.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If required columns are missing.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw NOAA data file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse CSV {file_path}: {e}")
    
    # Verify expected columns exist (based on typical NOAA AR Catalog structure)
    # We expect at least 'date' and an intensity metric. 
    # The task description mentions 'IWV_transport'.
    required_cols = ['date']
    if 'IWV_transport' not in df.columns:
        # Fallback check for common variations if the column name differs
        intensity_cols = [c for c in df.columns if 'iwv' in c.lower() or 'transport' in c.lower() or 'intensity' in c.lower()]
        if intensity_cols:
            logger.warning(f"Column 'IWV_transport' not found. Using '{intensity_cols[0]}' as intensity metric.")
            df = df.rename(columns={intensity_cols[0]: 'IWV_transport'})
        else:
            raise ValueError(f"Could not find an Integrated Water Vapor Transport column in {file_path}. Available columns: {list(df.columns)}")
    
    if 'date' not in df.columns:
        raise ValueError(f"Required column 'date' missing in {file_path}")
        
    return df

def aggregate_monthly_ar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates AR intensity data to monthly means.
    
    Args:
        df (pd.DataFrame): DataFrame with 'date' and 'IWV_transport' columns.
        
    Returns:
        pd.DataFrame: DataFrame with monthly aggregated data.
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # Create a 'month' period column for grouping
    df['month'] = df['date'].dt.to_period('M')
    
    # Aggregate: Mean of IWV_transport per month
    # We also keep the count to check for missing data later
    monthly = df.groupby('month').agg(
        ar_intensity=('IWV_transport', 'mean'),
        ar_count=('IWV_transport', 'count')
    ).reset_index()
    
    # Convert period back to timestamp for easier handling/saving
    monthly['date'] = monthly['month'].dt.to_timestamp()
    monthly = monthly.drop(columns=['month'])
    
    return monthly

def handle_missing_months(df: pd.DataFrame, start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """
    Logs warnings for any missing months between the start and end of the data range.
    
    Args:
        df (pd.DataFrame): The monthly aggregated DataFrame.
        start_date (pd.Timestamp): The expected start date.
        end_date (pd.Timestamp): The expected end date.
        
    Returns:
        pd.DataFrame: The original DataFrame (no modification, just logging).
    """
    # Generate full range of months
    full_range = pd.date_range(start=start_date, end=end_date, freq='MS')
    current_months = pd.to_datetime(df['date']).dt.to_period('M')
    full_range_periods = full_range.to_period('M')
    
    missing = full_range_periods.difference(current_months)
    
    if len(missing) > 0:
        logger.warning(f"Detected {len(missing)} missing months: {list(missing)}")
    else:
        logger.info("No missing months detected in the date range.")
        
    return df

def exclude_zero_ar_months(df: pd.DataFrame) -> pd.DataFrame:
    """
    Drops months where the total/mean AR intensity equals zero.
    
    Args:
        df (pd.DataFrame): DataFrame with 'ar_intensity' column.
        
    Returns:
        pd.DataFrame: Filtered DataFrame.
    """
    initial_count = len(df)
    df = df[df['ar_intensity'] > 0]
    dropped_count = initial_count - len(df)
    
    if dropped_count > 0:
        logger.info(f"Dropped {dropped_count} months with zero AR intensity.")
    else:
        logger.info("No months with zero AR intensity found.")
        
    return df

def save_processed_data(df: pd.DataFrame, output_path: str):
    """
    Saves the processed DataFrame to a CSV file.
    
    Args:
        df (pd.DataFrame): The DataFrame to save.
        output_path (str): The path where the CSV will be written.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        logger.info(f"Created directory: {output_dir}")
        
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to: {output_path}")

def main():
    # Define paths relative to project root
    # Target region input
    target_raw_path = "data/raw/noaa-ar/target/noaa_data.csv"
    # Control region input
    control_raw_path = "data/raw/noaa-ar/control/noaa_data.csv"
    
    # Output paths
    target_out_path = "data/processed/noaa_preprocessed_target.csv"
    control_out_path = "data/processed/noaa_preprocessed_control.csv"
    
    # 1. Load Target Data
    logger.info(f"Loading target data from {target_raw_path}")
    try:
        target_df = load_noaa_raw_data(target_raw_path)
    except Exception as e:
        logger.error(f"Failed to load target data: {e}")
        sys.exit(1)
        
    # 2. Load Control Data
    logger.info(f"Loading control data from {control_raw_path}")
    try:
        control_df = load_noaa_raw_data(control_raw_path)
    except Exception as e:
        logger.error(f"Failed to load control data: {e}")
        sys.exit(1)
    
    # 3. Aggregate to Monthly Means
    logger.info("Aggregating target data to monthly means...")
    target_monthly = aggregate_monthly_ar(target_df)
    
    logger.info("Aggregating control data to monthly means...")
    control_monthly = aggregate_monthly_ar(control_df)
    
    # 4. Handle Missing Months
    # Determine global range to check for gaps
    if not target_monthly.empty and not control_monthly.empty:
        global_start = min(target_monthly['date'].min(), control_monthly['date'].min())
        global_end = max(target_monthly['date'].max(), control_monthly['date'].max())
        handle_missing_months(target_monthly, global_start, global_end)
        handle_missing_months(control_monthly, global_start, global_end)
    else:
        logger.warning("One or both datasets are empty; skipping missing month analysis.")
    
    # 5. Drop Zero Intensity Months
    logger.info("Filtering out months with zero AR intensity...")
    target_monthly = exclude_zero_ar_months(target_monthly)
    control_monthly = exclude_zero_ar_months(control_monthly)
    
    # 6. Save Outputs
    logger.info("Saving processed target data...")
    save_processed_data(target_monthly, target_out_path)
    
    logger.info("Saving processed control data...")
    save_processed_data(control_monthly, control_out_path)
    
    logger.info("NOAA preprocessing complete.")

if __name__ == "__main__":
    main()