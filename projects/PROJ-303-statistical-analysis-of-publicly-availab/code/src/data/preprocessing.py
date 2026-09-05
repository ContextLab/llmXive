import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import logging
import warnings
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class ExtremeEvent:
    """
    Entity mapping for an extreme weather event.
    Matches the schema: (station_id, date, magnitude, threshold_value)
    """
    station_id: str
    date: str  # ISO format YYYY-MM-DD
    magnitude: float  # The observed value (e.g., precipitation in mm)
    threshold_value: float  # The threshold that was exceeded

def calculate_missing_ratio(df: pd.DataFrame) -> float:
    """Calculate the ratio of missing values in a DataFrame."""
    return df.isna().sum().sum() / (len(df) * len(df.columns))

def find_max_contiguous_gap(df: pd.DataFrame, date_col: str = 'date') -> int:
    """Find the maximum number of contiguous missing days."""
    if date_col not in df.columns:
        raise ValueError(f"Column {date_col} not found in DataFrame")
    
    # Sort by date
    sorted_df = df.sort_values(by=date_col)
    sorted_df = sorted_df.copy()
    sorted_df['is_missing'] = sorted_df['value'].isna()
    
    # Identify groups of contiguous missing values
    sorted_df['group'] = (~sorted_df['is_missing']).cumsum()
    missing_groups = sorted_df[sorted_df['is_missing']].groupby('group')
    
    if len(missing_groups) == 0:
        return 0
    
    return missing_groups.size().max()

def filter_stations(stations_data: Dict[str, pd.DataFrame], 
                    max_missing_ratio: float = 0.15,
                    max_gap_days: int = 30) -> Tuple[Dict[str, pd.DataFrame], Dict]:
    """
    Filter stations based on missing data criteria.
    
    Args:
        stations_data: Dictionary of station_id -> DataFrame
        max_missing_ratio: Maximum allowed missing ratio (default 15%)
        max_gap_days: Maximum allowed contiguous gap in days (default 30)
        
    Returns:
      - Filtered stations data
      - Filter report dictionary
    """
    filtered_data = {}
    excluded_stations = []
    
    for station_id, df in stations_data.items():
        missing_ratio = calculate_missing_ratio(df)
        max_gap = find_max_contiguous_gap(df)
        
        if missing_ratio > max_missing_ratio:
            excluded_stations.append({
                'station_id': station_id,
                'reason': 'high_missing_ratio',
                'value': missing_ratio,
                'threshold': max_missing_ratio
            })
            logger.warning(f"Station {station_id} excluded: missing ratio {missing_ratio:.2%} > {max_missing_ratio:.2%}")
            continue
        
        if max_gap > max_gap_days:
            excluded_stations.append({
                'station_id': station_id,
                'reason': 'large_gap',
                'value': max_gap,
                'threshold': max_gap_days
            })
            logger.warning(f"Station {station_id} excluded: max gap {max_gap} days > {max_gap_days} days")
            continue
        
        filtered_data[station_id] = df
    
    filter_report = {
        'total_stations': len(stations_data),
        'included_stations': len(filtered_data),
        'excluded_stations': len(excluded_stations),
        'exclusion_details': excluded_stations
    }
    
    return filtered_data, filter_report

def generate_filter_report(report: Dict, output_path: Path) -> None:
    """Save the filter report to a JSON file."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Filter report saved to {output_path}")

def interpolate_short_gaps(df: pd.DataFrame, max_gap_size: int = 7) -> pd.DataFrame:
    """
    Interpolate short gaps in the time series.
    
    Args:
        df: DataFrame with 'date' and 'value' columns
        max_gap_size: Maximum gap size to interpolate (default 7 days)
        
    Returns:
        DataFrame with interpolated values
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')
    
    # Create a complete date range
    full_range = pd.date_range(start=df.index.min(), end=df.index.max(), freq='D')
    df = df.reindex(full_range)
    
    # Interpolate gaps up to max_gap_size
    df['value'] = df['value'].interpolate(method='time', limit=max_gap_size)
    
    # Reset index
    df = df.reset_index()
    df = df.rename(columns={'index': 'date'})
    
    return df

def calculate_thresholds(df: pd.DataFrame, percentile: float = 90, date_col: str = 'date', value_col: str = 'value') -> float:
    """
    Calculate the threshold for extreme events based on a percentile.
    Only uses non-null values.
    
    Args:
        df: DataFrame containing the time series
        percentile: Percentile to use for threshold (default 90)
        date_col: Name of the date column
        value_col: Name of the value column
        
    Returns:
        Threshold value
    """
    valid_values = df[value_col].dropna()
    if len(valid_values) == 0:
        raise ValueError("No valid values found for threshold calculation")
    
    threshold = np.percentile(valid_values, percentile)
    logger.info(f"Calculated {percentile}th percentile threshold: {threshold:.4f}")
    return threshold

def flag_extreme_events(df: pd.DataFrame, 
                        threshold: float, 
                        date_col: str = 'date', 
                        value_col: str = 'value') -> pd.DataFrame:
    """
    Flag extreme events where value > threshold.
    
    Args:
        df: DataFrame with time series data
        threshold: Threshold value for extreme events
        date_col: Name of the date column
        value_col: Name of the value column
        
    Returns:
        DataFrame with 'is_extreme' and 'magnitude' columns added
    """
    df = df.copy()
    df['is_extreme'] = df[value_col] > threshold
    df['magnitude'] = df[value_col] - threshold
    df.loc[~df['is_extreme'], 'magnitude'] = np.nan
    
    return df

def map_to_extreme_event_entity(df: pd.DataFrame, 
                                station_id: str, 
                                threshold_value: float,
                                date_col: str = 'date',
                                value_col: str = 'value') -> List[ExtremeEvent]:
    """
    Map raw data to the ExtremeEvent entity schema.
    
    This function takes a DataFrame of station data (after thresholding)
    and converts rows where an extreme event occurred into a list of 
    ExtremeEvent dataclass instances.
    
    Args:
        df: DataFrame containing time series data, must have 'is_extreme' column
        station_id: The station identifier string
        threshold_value: The threshold value used for this station
        date_col: Name of the date column in the DataFrame
        value_col: Name of the value column in the DataFrame
        
    Returns:
        List of ExtremeEvent objects representing the exceedances
    """
    if 'is_extreme' not in df.columns:
        raise ValueError("DataFrame must contain 'is_extreme' column. Run flag_extreme_events first.")
    
    extreme_rows = df[df['is_extreme']].copy()
    
    events = []
    for _, row in extreme_rows.iterrows():
        event = ExtremeEvent(
            station_id=station_id,
            date=str(pd.to_datetime(row[date_col]).date()),
            magnitude=float(row[value_col]),
            threshold_value=float(threshold_value)
        )
        events.append(event)
    
    return events

def main():
    """
    Main execution function for preprocessing pipeline.
    This is a placeholder for the full pipeline execution.
    """
    logger.info("Preprocessing module loaded. Ready for data processing.")

if __name__ == "__main__":
    main()
