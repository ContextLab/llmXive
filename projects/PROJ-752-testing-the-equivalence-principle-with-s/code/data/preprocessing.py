import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict
from datetime import timedelta
import logging
import sys
import os

# Configure logging for the module
logger = logging.getLogger(__name__)

def filter_residuals(df: pd.DataFrame, threshold_m: float = 0.02) -> pd.DataFrame:
    """
    Vectorized filtering of SLR data based on residual magnitude.
    
    Removes rows where the residual (range residual) exceeds the threshold.
    Uses numpy boolean indexing for performance.
    
    Args:
        df: DataFrame containing SLR data with a 'residual' column (meters).
        threshold_m: Maximum allowed residual in meters (default 0.02m = 2cm).
        
    Returns:
        Filtered DataFrame.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to filter_residuals.")
        return df
        
    if 'residual' not in df.columns:
        raise KeyError("DataFrame must contain a 'residual' column.")
        
    # Vectorized boolean mask
    mask = np.abs(df['residual'].values) <= threshold_m
    filtered_df = df[mask].copy()
    
    removed_count = len(df) - len(filtered_df)
    if removed_count > 0:
        logger.info(f"Filtered {removed_count} rows with residuals > {threshold_m}m.")
        
    return filtered_df

def handle_sparse_satellites(df: pd.DataFrame, min_days: int = 30) -> Tuple[pd.DataFrame, List[str]]:
    """
    Identify and exclude satellites with insufficient arc length (< min_days).
    
    Uses vectorized datetime operations to count unique dates per satellite.
    
    Args:
        df: DataFrame with 'satellite_id' and 'timestamp' columns.
        min_days: Minimum number of unique days required (default 30).
        
    Returns:
        Tuple of (Filtered DataFrame with sufficient satellites, List of excluded satellite IDs).
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to handle_sparse_satellites.")
        return df, []
        
    if 'satellite_id' not in df.columns or 'timestamp' not in df.columns:
        raise KeyError("DataFrame must contain 'satellite_id' and 'timestamp' columns.")
        
    # Ensure timestamp is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
    # Extract date (vectorized)
    df['date'] = df['timestamp'].dt.date
    
    # Count unique dates per satellite using groupby (optimized in pandas)
    # Using size() is faster than count() for this purpose
    date_counts = df.groupby('satellite_id')['date'].nunique()
    
    excluded_ids = date_counts[date_counts < min_days].index.tolist()
    
    if excluded_ids:
        logger.warning(f"Excluding {len(excluded_ids)} satellites with < {min_days} days of data: {excluded_ids}")
        # Filter out excluded satellites
        mask = ~df['satellite_id'].isin(excluded_ids)
        filtered_df = df[mask].copy()
    else:
        filtered_df = df.copy()
        
    # Drop the temporary 'date' column if it wasn't there originally
    if 'date' in filtered_df.columns and 'date' not in df.columns:
        filtered_df.drop(columns=['date'], inplace=True)
        
    return filtered_df, excluded_ids

def align_time_series(df: pd.DataFrame, time_window_sec: float = 60.0) -> pd.DataFrame:
    """
    Align multi-satellite time series by binning timestamps into fixed windows.
    
    This vectorizes the alignment process by converting timestamps to bin edges
    and using groupby on the bin labels.
    
    Args:
        df: DataFrame with 'timestamp', 'satellite_id', and 'range' (or similar) columns.
        time_window_sec: Size of the time bin in seconds.
        
    Returns:
        DataFrame with aligned timestamps (bin centers) and averaged measurements.
    """
    if df.empty:
        logger.warning("Empty DataFrame passed to align_time_series.")
        return df
        
    if 'timestamp' not in df.columns:
        raise KeyError("DataFrame must contain a 'timestamp' column.")
        
    # Convert to numpy timestamps for vectorized arithmetic
    timestamps = df['timestamp'].values.astype('datetime64[ns]').astype(np.int64)
    window_ns = int(time_window_sec * 1e9)
    
    # Calculate bin edges (floor to window)
    # We align to the start of the window
    bin_edges = (timestamps // window_ns) * window_ns
    
    df['bin_edge'] = pd.to_datetime(bin_edges)
    
    # Group by satellite and bin, then aggregate (mean of numerical columns)
    # This is significantly faster than iterating rows
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Ensure 'range' or similar is in numeric cols, if not, handle explicitly
    # Assuming 'range' is the primary measurement
    agg_dict = {col: 'mean' for col in numeric_cols}
    
    # Group by satellite and bin
    grouped = df.groupby(['satellite_id', 'bin_edge'])
    aligned_df = grouped.agg(agg_dict).reset_index()
    
    # Rename bin_edge to timestamp
    aligned_df.rename(columns={'bin_edge': 'timestamp'}, inplace=True)
    
    logger.info(f"Aligned time series: {len(df)} rows -> {len(aligned_df)} bins.")
    
    return aligned_df

def merge_multi_satellite_datasets(df_list: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple satellite DataFrames into a single wide-format DataFrame
    aligned by timestamp and satellite_id.
    
    Uses vectorized merge operations.
    
    Args:
        df_list: List of DataFrames, each representing one satellite's data.
        
    Returns:
        Merged DataFrame.
    """
    if not df_list:
        logger.warning("Empty list of DataFrames passed to merge_multi_satellite_datasets.")
        return pd.DataFrame()
        
    # Filter out empty DataFrames
    valid_dfs = [df for df in df_list if not df.empty]
    
    if not valid_dfs:
        return pd.DataFrame()
        
    # Concatenate along rows (axis=0) is usually faster than iterative merging
    # if the goal is a long-format table. If wide-format is needed, we pivot.
    # Assuming we want a unified long-format table for downstream analysis
    combined_df = pd.concat(valid_dfs, ignore_index=True)
    
    logger.info(f"Merged {len(valid_dfs)} satellite datasets into {len(combined_df)} rows.")
    
    return combined_df

def preprocess_slr_data(input_path: str, output_path: str, 
                        residual_threshold_m: float = 0.02, 
                        min_arc_days: int = 30,
                        time_window_sec: float = 60.0) -> None:
    """
    Main entry point for the preprocessing pipeline.
    Orchestrates filtering, sparse handling, alignment, and merging.
    
    Args:
        input_path: Path to the raw/processed CSV input.
        output_path: Path to save the cleaned CSV output.
        residual_threshold_m: Threshold for residual filtering (meters).
        min_arc_days: Minimum days of arc length.
        time_window_sec: Time binning window for alignment.
    """
    logger.info(f"Starting preprocessing pipeline for {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
        
    # Load data
    logger.info("Loading data...")
    df = pd.read_csv(input_path)
    
    # Step 1: Filter residuals
    logger.info("Filtering residuals...")
    df = filter_residuals(df, threshold_m=residual_threshold_m)
    
    # Step 2: Handle sparse satellites
    logger.info("Handling sparse satellites...")
    df, excluded = handle_sparse_satellites(df, min_days=min_arc_days)
    
    # Step 3: Align time series
    logger.info("Aligning time series...")
    df = align_time_series(df, time_window_sec=time_window_sec)
    
    # Step 4: Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save output
    logger.info(f"Saving preprocessed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    logger.info("Preprocessing pipeline completed successfully.")

def main():
    """
    CLI entry point for preprocessing.
    Expects environment variables or default paths.
    """
    # Default paths relative to project structure
    input_file = os.getenv('SLR_INPUT_PATH', 'data/processed/raw_slr_data.csv')
    output_file = os.getenv('SLR_OUTPUT_PATH', 'data/processed/cleaned_slr_data.csv')
    
    # Initialize logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/logs/preprocessing.log')
        ]
    )
    
    try:
        preprocess_slr_data(input_file, output_file)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()