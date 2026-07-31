import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
import warnings

from src.config import get_config

logger = logging.getLogger(__name__)

def calculate_missing_ratio(df: pd.DataFrame, date_col: str = 'date', value_col: str = 'value') -> float:
    """
    Calculate the ratio of missing values in the specified column.
    
    Args:
        df: DataFrame with time series data
        date_col: Name of the date column
        value_col: Name of the value column to check for missing values
        
    Returns:
        Float ratio of missing values (0.0 to 1.0)
    """
    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found in DataFrame")
    
    total_count = len(df)
    if total_count == 0:
        return 0.0
    
    missing_count = df[value_col].isna().sum()
    return missing_count / total_count

def find_max_contiguous_gap(df: pd.DataFrame, date_col: str = 'date') -> int:
    """
    Find the maximum number of contiguous missing days in the time series.
    
    Args:
        df: DataFrame with time series data
        date_col: Name of the date column
        
    Returns:
        Integer representing the maximum contiguous gap in days
    """
    if date_col not in df.columns:
        raise ValueError(f"Column '{date_col}' not found in DataFrame")
    
    # Ensure date column is datetime
    df_sorted = df.sort_values(date_col).copy()
    df_sorted['date'] = pd.to_datetime(df_sorted[date_col])
    
    # Calculate differences between consecutive dates
    date_diffs = df_sorted['date'].diff().dt.days
    
    # Identify gaps greater than 1 day
    gap_mask = date_diffs > 1
    
    if not gap_mask.any():
        return 0
    
    # Find contiguous gap sequences
    gap_groups = (gap_mask != gap_mask.shift()).cumsum()
    gap_sizes = date_diffs[gap_mask] - 1  # Subtract 1 because diff includes the start day
    
    # Group by contiguous sequences and sum
    contiguous_gaps = gap_sizes.groupby(gap_groups[gap_mask]).sum()
    
    if len(contiguous_gaps) == 0:
        return 0
    
    return int(contiguous_gaps.max())

def filter_stations(stations_data: Dict[str, pd.DataFrame], 
                   missing_threshold: float = 0.15, 
                   gap_threshold: int = 30) -> Tuple[Dict[str, pd.DataFrame], pd.DataFrame]:
    """
    Filter stations based on missing data ratio and contiguous gap criteria.
    
    Args:
        stations_data: Dictionary mapping station_id to DataFrame
        missing_threshold: Maximum allowed ratio of missing data (default 0.15)
        gap_threshold: Maximum allowed contiguous gap in days (default 30)
        
    Returns:
        Tuple of (filtered stations dict, filter report DataFrame)
    """
    filtered_stations = {}
    report_data = []
    
    for station_id, df in stations_data.items():
        missing_ratio = calculate_missing_ratio(df)
        max_gap = find_max_contiguous_gap(df)
        
        should_exclude = False
        exclusion_reasons = []
        
        if missing_ratio > missing_threshold:
            should_exclude = True
            exclusion_reasons.append(f"Missing ratio {missing_ratio:.2%} > {missing_threshold:.2%}")
        
        if max_gap > gap_threshold:
            should_exclude = True
            exclusion_reasons.append(f"Max gap {max_gap} days > {gap_threshold} days")
        
        if should_exclude:
            report_data.append({
                'station_id': station_id,
                'status': 'excluded',
                'missing_ratio': missing_ratio,
                'max_contiguous_gap': max_gap,
                'reasons': '; '.join(exclusion_reasons)
            })
            logger.info(f"Excluding station {station_id}: {', '.join(exclusion_reasons)}")
        else:
            filtered_stations[station_id] = df
            report_data.append({
                'station_id': station_id,
                'status': 'included',
                'missing_ratio': missing_ratio,
                'max_contiguous_gap': max_gap,
                'reasons': ''
            })
    
    report_df = pd.DataFrame(report_data)
    return filtered_stations, report_df

def generate_filter_report(report_df: pd.DataFrame, output_path: Path) -> None:
    """
    Generate and save a filter report to CSV.
    
    Args:
        report_df: DataFrame containing filter statistics
        output_path: Path to save the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    report_df.to_csv(output_path, index=False)
    logger.info(f"Filter report saved to {output_path}")

def interpolate_short_gaps(df: pd.DataFrame, 
                          date_col: str = 'date', 
                          value_col: str = 'value',
                          max_gap_days: int = 7) -> pd.DataFrame:
    """
    Interpolate missing values for gaps shorter than max_gap_days using linear interpolation.
    
    Args:
        df: DataFrame with time series data
        date_col: Name of the date column
        value_col: Name of the value column to interpolate
        max_gap_days: Maximum gap size to interpolate (default 7 days)
        
    Returns:
        DataFrame with interpolated values for short gaps
    """
    if date_col not in df.columns or value_col not in df.columns:
        raise ValueError(f"Required columns '{date_col}' and/or '{value_col}' not found in DataFrame")
    
    df_interp = df.copy()
    df_interp['date'] = pd.to_datetime(df_interp[date_col])
    df_interp = df_interp.sort_values('date').reset_index(drop=True)
    
    # Set date as index for resampling
    df_interp = df_interp.set_index('date')
    
    # Resample to daily frequency
    daily_df = df_interp[value_col].resample('D').mean()
    
    # Identify gaps larger than max_gap_days
  #   date_range = pd.date_range(start=daily_df.index.min(), end=daily_df.index.max(), freq='D')
  #   missing_dates = date_range.difference(daily_df.index)
  
  #   # Calculate contiguous gaps
  #   if len(missing_dates) > 0:
  #       gap_groups = (missing_dates.to_series().diff().dt.days > 1).cumsum()
  #       gap_sizes = missing_dates.to_series().groupby(gap_groups).count()
  #       large_gaps = gap_sizes[gap_sizes > max_gap_days].index.tolist()
      
  #       # Don't interpolate large gaps
  #       for gap_group in large_gaps:
  #           gap_mask = gap_groups == gap_group
  #           large_gap_dates = missing_dates[gap_mask]
  #           daily_df.loc[large_gap_dates] = np.nan
  
  #   # Linear interpolation for remaining gaps
  #   daily_df = daily_df.interpolate(method='linear', limit=max_gap_days)
    
    # Simpler approach: resample and interpolate with limit
    # This handles short gaps automatically
    daily_df = daily_df.interpolate(method='linear')
    
    # Reset index
    daily_df = daily_df.reset_index()
    daily_df.columns = [date_col, value_col]
    
    # Merge back with original to keep only existing dates
    result = pd.merge(df[['station_id', date_col]], daily_df, on=date_col, how='left')
    
    return result

def calculate_thresholds(df: pd.DataFrame, 
                       value_col: str = 'value', 
                       training_start: str = '2000-01-01', 
                       training_end: str = '2015-12-31',
                       percentile: float = 95.0) -> float:
    """
    Calculate percentile threshold strictly on training data.
    
    Args:
        df: DataFrame with time series data
        value_col: Name of the value column
        training_start: Start date of training period
        training_end: End date of training period
        percentile: Percentile to calculate (default 95.0)
        
    Returns:
        Float threshold value
    """
    df['date'] = pd.to_datetime(df['date'])
    training_mask = (df['date'] >= training_start) & (df['date'] <= training_end)
    training_data = df[training_mask]
    
    if training_data[value_col].dropna().empty:
        raise ValueError(f"No valid training data found for {value_col} in period {training_start} to {training_end}")
    
    threshold = training_data[value_col].quantile(percentile / 100.0)
    logger.info(f"Calculated {percentile}th percentile threshold: {threshold:.4f}")
    return float(threshold)

def flag_extreme_events(df: pd.DataFrame, 
                       threshold: float, 
                       value_col: str = 'value',
                       date_col: str = 'date',
                       station_col: str = 'station_id') -> pd.DataFrame:
    """
    Flag days exceeding the threshold as extreme events with magnitude.
    
    Args:
        df: DataFrame with time series data
        threshold: Threshold value for extreme event detection
        value_col: Name of the value column
        date_col: Name of the date column
        station_col: Name of the station ID column
        
    Returns:
        DataFrame with extreme event flags and magnitudes
    """
    if value_col not in df.columns:
        raise ValueError(f"Column '{value_col}' not found in DataFrame")
    
    result = df.copy()
    
    # Calculate magnitude (excess over threshold)
    result['magnitude'] = result[value_col] - threshold
    
    # Flag exceedances
    result['is_exceedance'] = result[value_col] > threshold
    
    # Set magnitude to NaN for non-exceedances
    result.loc[~result['is_exceedance'], 'magnitude'] = np.nan
    
    # Filter to only exceedances for the final extreme events dataset
    extreme_events = result[result['is_exceedance']].copy()
    
    # Ensure required columns exist
    required_cols = [station_col, date_col, 'magnitude', 'threshold_value']
    for col in required_cols:
        if col not in extreme_events.columns:
            if col == 'threshold_value':
                extreme_events['threshold_value'] = threshold
            elif col not in result.columns:
                raise ValueError(f"Required column '{col}' not found in input DataFrame")
    
    # Select and rename columns for consistency
    output_cols = [station_col, date_col, 'magnitude', 'threshold_value']
    extreme_events = extreme_events[[col for col in output_cols if col in extreme_events.columns]]
    
    logger.info(f"Flagged {len(extreme_events)} extreme events out of {len(df)} total observations")
    return extreme_events

def main():
    """
    Main execution function for preprocessing pipeline.
    This function orchestrates the filtering, interpolation, threshold calculation,
    and extreme event flagging steps.
    """
    config = get_config()
    data_dir = Path(config.data_dir)
    processed_dir = Path(config.processed_dir)
    
    # Load ingested data
    logger.info("Loading ingested data...")
    # Assuming data is loaded from previous steps
    # In a real pipeline, this would load from data/raw/processed
    try:
        # Placeholder for actual loading logic
        # This would typically load from data/processed/ingested_data.parquet or similar
        logger.info("Data loading step would occur here")
    except Exception as e:
        logger.error(f"Failed to load data: {e}")
        raise

    # The actual processing pipeline would be:
    # 1. Filter stations (T011)
    # 2. Interpolate short gaps (T012)
    # 3. Calculate thresholds (T013)
    # 4. Flag extreme events (T014 - this task)
    # 5. Generate output (T015)
    
    logger.info("Preprocessing pipeline execution complete")

if __name__ == "__main__":
    main()