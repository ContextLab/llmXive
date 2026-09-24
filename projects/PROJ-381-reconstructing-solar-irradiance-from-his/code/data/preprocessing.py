import os
import json
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import pandas as pd
import numpy as np

from config import get_tsi_proxy_value, get_gap_filling_strategy
from env_config import get_raw_data_path, get_processed_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
GAP_THRESHOLD_DAYS = 365  # 1 year
MIN_DATA_YEAR_SATELLITE = 2003
MAX_DATA_YEAR_PRE_SATELLITE = 2002
SILENCE_THRESHOLD = 1.0  # W/m^2 proxy value is handled by config

def load_raw_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load raw GSN and TSI data from the ingestion stage.
    
    Returns:
        Tuple of (gsn_df, tsi_df)
    """
    raw_path = get_raw_data_path()
    gsn_file = raw_path / "silso_gsn.csv"
    tsi_file = raw_path / "sorce_tsi.csv"
    
    if not gsn_file.exists():
        raise FileNotFoundError(f"Raw GSN data not found at {gsn_file}. Run ingestion first.")
    if not tsi_file.exists():
        raise FileNotFoundError(f"Raw TSI data not found at {tsi_file}. Run ingestion first.")
        
    logger.info(f"Loading GSN data from {gsn_file}")
    gsn_df = pd.read_csv(gsn_file)
    
    logger.info(f"Loading TSI data from {tsi_file}")
    tsi_df = pd.read_csv(tsi_file)
    
    # Ensure date columns are datetime
    if 'date' in gsn_df.columns:
        gsn_df['date'] = pd.to_datetime(gsn_df['date'], errors='coerce')
    if 'date' in tsi_df.columns:
        tsi_df['date'] = pd.to_datetime(tsi_df['date'], errors='coerce')
        
    return gsn_df, tsi_df

def detect_cycle_boundaries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect sunspot cycle boundaries based on SILSO method logic.
    This function identifies local minima and maxima to mark cycle starts/ends.
    
    Args:
        df: DataFrame with 'date' and 'gsn' columns
        
    Returns:
        DataFrame with added 'cycle_id' column
    """
    logger.info("Detecting cycle boundaries...")
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Simple peak detection logic for demonstration
    # In a full implementation, this would strictly follow SILSO's algorithm
    # identifying the smoothed monthly mean minima.
    
    # Create a temporary smoothed series for detection
    window = 13 # 13-month smoothing approx
    if len(df) > window:
        df['gsn_smooth'] = df['gsn'].rolling(window=window, center=True, min_periods=1).mean()
    else:
        df['gsn_smooth'] = df['gsn']
        
    # Identify minima (cycle start) and maxima (cycle peak)
    # We use a simple derivative approach for this implementation
    # A more robust method would use scipy.signal.find_peaks
    df['is_min'] = False
    df['is_max'] = False
    
    for i in range(1, len(df) - 1):
        if df.loc[i, 'gsn_smooth'] < df.loc[i-1, 'gsn_smooth'] and \
           df.loc[i, 'gsn_smooth'] < df.loc[i+1, 'gsn_smooth']:
            df.loc[i, 'is_min'] = True
        elif df.loc[i, 'gsn_smooth'] > df.loc[i-1, 'gsn_smooth'] and \
             df.loc[i, 'gsn_smooth'] > df.loc[i+1, 'gsn_smooth']:
            df.loc[i, 'is_max'] = True
            
    # Assign cycle IDs based on detected minima
    current_cycle = 1
    cycle_starts = df[df['is_min']].index.tolist()
    
    # Map dates to cycle IDs
    cycle_map = {}
    if cycle_starts:
        # Assign cycle ID based on the last detected minimum before the date
        for idx, row in df.iterrows():
            date = row['date']
            # Find the most recent cycle start <= current date
            valid_starts = [s for s in cycle_starts if s <= idx]
            if valid_starts:
                # Determine cycle number based on index in cycle_starts
                last_start_idx = max(valid_starts)
                # Calculate cycle number: 1 + count of starts before this one
                # This is a simplified mapping; real SILSO data has fixed cycle numbers
                # For this task, we generate a sequential ID for the detected period
                # unless we have a specific mapping from config or external source.
                # Since T015 requires official SILSO IDs, we will generate a placeholder
                # that T015 will overwrite or align with official records if available.
                # Here we just assign a sequential ID for the purpose of gap filling logic.
                cycle_map[idx] = current_cycle
                if idx in cycle_starts:
                    current_cycle += 1
            else:
                cycle_map[idx] = 0 # Before first detected cycle
                
    df['cycle_id'] = df.index.map(cycle_map)
    
    # Clean up temporary columns
    if 'gsn_smooth' in df.columns:
        df.drop(columns=['gsn_smooth'], inplace=True)
        
    logger.info(f"Detected {len(df[df['cycle_id'] > 0].drop_duplicates('cycle_id'))} cycles")
    return df

def fill_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill gaps in GSN data according to FR-002 logic.
    - Gaps < 1 year: Linear interpolation
    - Gaps >= 1 year: Use TSI proxy value (1360.5 W/m^2) mapped to GSN scale or mark as proxy.
      Note: The task description says "Apply TSI proxy value... Do NOT use GSN=0".
      Since the output is a combined TSI/GSN dataset, we will flag these rows.
      
    Args:
        df: DataFrame with 'date', 'gsn', and potentially 'tsi' columns
        
    Returns:
        DataFrame with filled gaps and a 'gap_filled' indicator
    """
    logger.info("Filling gaps in GSN data...")
    df = df.copy()
    df = df.sort_values('date').reset_index(drop=True)
    
    # Ensure GSN is numeric
    df['gsn'] = pd.to_numeric(df['gsn'], errors='coerce')
    
    # Identify gaps
    # We look for NaN values in GSN
    is_na = df['gsn'].isna()
    
    if not is_na.any():
        logger.info("No gaps found in GSN data.")
        df['gap_filled'] = False
        df['gap_type'] = 'none'
        return df
        
    # Find start and end indices of consecutive NaN blocks
    groups = (is_na != is_na.shift()).cumsum()
    na_groups = groups[is_na]
    
    gap_info = []
    
    for group_id in na_groups.unique():
        mask = na_groups == group_id
        indices = df[mask].index.tolist()
        start_idx = indices[0]
        end_idx = indices[-1]
        
        # Calculate gap duration in days
        start_date = df.loc[start_idx, 'date']
        end_date = df.loc[end_idx, 'date']
        gap_days = (end_date - start_date).days
        
        gap_info.append({
            'start_idx': start_idx,
            'end_idx': end_idx,
            'days': gap_days,
            'method': 'proxy' if gap_days >= GAP_THRESHOLD_DAYS else 'interpolate'
        })
        
    # Apply filling
    for info in gap_info:
        start_idx = info['start_idx']
        end_idx = info['end_idx']
        method = info['method']
        indices = range(start_idx, end_idx + 1)
        
        if method == 'interpolate':
            # Linear interpolation for small gaps
            logger.info(f"Interpolating gap of {info['days']} days at indices {start_idx}-{end_idx}")
            df.loc[indices, 'gsn'] = df.loc[indices, 'gsn'].interpolate(method='linear')
            df.loc[indices, 'gap_filled'] = True
            df.loc[indices, 'gap_type'] = 'interpolation'
        else:
            # Proxy for large gaps
            # We cannot directly put TSI value into GSN column without conversion.
            # However, the task says "Apply TSI proxy value... Do NOT use GSN=0".
            # In the context of the final dataset which merges GSN and TSI,
            # we might fill the TSI column if it's missing, or mark the GSN as unreliable.
            # Given the instruction "Apply TSI proxy value 1360.5 W/m^2", we assume
            # the final dataset has a TSI column. If GSN is missing for >1 year,
            # we cannot reconstruct TSI from GSN.
            # BUT, the task T014c says "Ingest and preprocess BOTH... GSN data".
            # And T014b says "Apply TSI proxy... for gaps >= 1 year".
            # This implies if GSN is missing for >1 year, we use the proxy for the TSI reconstruction
            # in that period, effectively bypassing the GSN->TSI model for those dates.
            # For the GSN column itself, we might leave it NaN or mark it.
            # Let's assume we are building a unified TSI record.
            # If GSN is missing for >1 year, we set the GSN-derived TSI to the proxy.
            # Since this function is on GSN data, we will mark the gap and set a flag.
            # The actual proxy value application happens in the merge or a specific TSI filling step.
            # However, to satisfy "Apply TSI proxy value", we will fill the 'tsi' column if it exists,
            # or create a 'tsi_proxy' column.
            
            logger.info(f"Applying TSI proxy for gap of {info['days']} days at indices {start_idx}-{end_idx}")
            
            # If TSI column exists, fill it with proxy
            tsi_proxy_val = get_tsi_proxy_value()
            if 'tsi' in df.columns:
                df.loc[indices, 'tsi'] = tsi_proxy_val
            else:
                # Create a proxy column for later use
                df.loc[indices, 'tsi_proxy'] = tsi_proxy_val
                
            df.loc[indices, 'gap_filled'] = True
            df.loc[indices, 'gap_type'] = 'tsi_proxy'
            
    # Final interpolation for any remaining small gaps (if not fully covered by loop logic)
    # The loop covers identified blocks.
    
    # Ensure gap_filled is boolean, default False
    if 'gap_filled' not in df.columns:
        df['gap_filled'] = False
    if 'gap_type' not in df.columns:
        df['gap_type'] = 'none'
        
    return df

def merge_datasets(gsn_df: pd.DataFrame, tsi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge preprocessed GSN and TSI datasets.
    
    Args:
        gsn_df: Preprocessed GSN data
        tsi_df: Preprocessed TSI data
        
    Returns:
        Merged DataFrame
    """
    logger.info("Merging GSN and TSI datasets...")
    
    # Ensure both have 'date' column
    if 'date' not in gsn_df.columns:
        gsn_df['date'] = pd.to_datetime(gsn_df.index)
    if 'date' not in tsi_df.columns:
        tsi_df['date'] = pd.to_datetime(tsi_df.index)
        
    # Sort by date
    gsn_df = gsn_df.sort_values('date')
    tsi_df = tsi_df.sort_values('date')
    
    # Outer join to keep all data points
    merged = pd.merge(
        gsn_df,
        tsi_df,
        on='date',
        how='outer',
        suffixes=('_gsn', '_tsi')
    )
    
    # If column names were suffixed, rename back or keep distinct
    # Assuming original columns were 'gsn' and 'tsi'
    # If merge created 'gsn_gsn' etc, we might need to clean.
    # But with 'on' specified, 'gsn' and 'tsi' should remain if unique.
    
    # Re-sort by date
    merged = merged.sort_values('date').reset_index(drop=True)
    
    return merged

def run_preprocessing() -> pd.DataFrame:
    """
    Main entry point for preprocessing pipeline.
    1. Load raw data.
    2. Detect cycles.
    3. Fill gaps.
    4. Merge datasets.
    5. Save to parquet.
    
    Returns:
        The final preprocessed DataFrame.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load
    gsn_df, tsi_df = load_raw_data()
    
    # 2. Detect cycles (on GSN)
    gsn_df = detect_cycle_boundaries(gsn_df)
    
    # 3. Fill gaps (on GSN, affects TSI proxy)
    gsn_df = fill_gaps(gsn_df)
    
    # 4. Merge
    final_df = merge_datasets(gsn_df, tsi_df)
    
    # 5. Atomic write to parquet
    processed_path = get_processed_data_path()
    output_file = processed_path / "preprocessed_data.parquet"
    
    logger.info(f"Saving preprocessed data to {output_file}")
    
    # Ensure directory exists
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Atomic write: write to temp, then rename
    temp_file = processed_path / "preprocessed_data.parquet.tmp"
    final_df.to_parquet(temp_file, index=False)
    temp_file.rename(output_file)
    
    logger.info(f"Preprocessing complete. Output saved to {output_file}")
    logger.info(f"Final dataset shape: {final_df.shape}")
    logger.info(f"Date range: {final_df['date'].min()} to {final_df['date'].max()}")
    
    return final_df

def main():
    """CLI entry point."""
    run_preprocessing()

if __name__ == "__main__":
    main()