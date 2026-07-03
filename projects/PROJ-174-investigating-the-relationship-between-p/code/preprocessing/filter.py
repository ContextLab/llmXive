import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
import csv
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('code/logs/preprocess.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def butter_lowpass(cutoff: float, fs: float, order: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Design a Butterworth lowpass filter.
    
    Args:
        cutoff: Cutoff frequency (Hz)
        fs: Sampling frequency (Hz)
        order: Order of the filter
        
    Returns:
        Tuple of (b, a) filter coefficients
    """
    nyq = 0.5 * fs
    normalized_cutoff = cutoff / nyq
    if normalized_cutoff >= 1.0:
        raise ValueError(f"Cutoff frequency ({cutoff}Hz) must be less than Nyquist frequency ({0.5 * fs}Hz)")
    
    b, a = butter(order, normalized_cutoff, btype='low')
    return b, a

def lowpass_filter(data: np.ndarray, fs: float, cutoff: float = 4.0, order: int = 5) -> np.ndarray:
    """
    Apply a lowpass filter to the data.
    
    Args:
        data: Input data array
        fs: Sampling frequency (Hz)
        cutoff: Cutoff frequency (Hz)
        order: Order of the filter
        
    Returns:
        Filtered data array
    """
    b, a = butter_lowpass(cutoff, fs, order)
    # Handle edge cases where data is too short for filtfilt
    if len(data) < 2 * order + 1:
        logger.warning(f"Data length ({len(data)}) too short for filter order {order}. Returning original data.")
        return data
    
    try:
        filtered = filtfilt(b, a, data, padlen=3 * max(len(b), len(a)))
        return filtered
    except ValueError as e:
        logger.warning(f"Filtering failed: {e}. Returning original data.")
        return data

def interpolate_blinks(data: np.ndarray, threshold: float = 0.05, max_gap: int = 50) -> Tuple[np.ndarray, List[int]]:
    """
    Identify and interpolate blink artifacts in pupil data.
    
    Args:
        data: Pupil diameter time series
        threshold: Threshold for blink detection (fraction of median)
        max_gap: Maximum gap size to interpolate (in samples)
        
    Returns:
        Tuple of (interpolated_data, blink_indices)
    """
    if len(data) == 0:
        return data, []
    
    median_val = np.nanmedian(data)
    if median_val == 0:
        logger.warning("Median pupil diameter is zero. Skipping blink interpolation.")
        return data, []
    
    # Detect blinks (values significantly below median, often near zero)
    blink_mask = data < (median_val * threshold)
    blink_indices = np.where(blink_mask)[0].tolist()
    
    if not blink_indices:
        return data, []
    
    # Create a copy for interpolation
    interpolated = data.copy()
    
    # Group consecutive blink indices
    blink_groups = []
    if blink_indices:
        current_group = [blink_indices[0]]
        for i in range(1, len(blink_indices)):
            if blink_indices[i] == blink_indices[i-1] + 1:
                current_group.append(blink_indices[i])
            else:
                blink_groups.append(current_group)
                current_group = [blink_indices[i]]
        blink_groups.append(current_group)
    
    # Interpolate valid groups
    for group in blink_groups:
        if len(group) > max_gap:
            # Mark as NaN if gap is too large
            for idx in group:
                if idx < len(interpolated):
                    interpolated[idx] = np.nan
        else:
            start_idx = group[0]
            end_idx = group[-1]
            
            # Find valid neighbors
            left_valid = start_idx - 1
            while left_valid >= 0 and np.isnan(interpolated[left_valid]):
                left_valid -= 1
            
            right_valid = end_idx + 1
            while right_valid < len(interpolated) and np.isnan(interpolated[right_valid]):
                right_valid += 1
            
            if left_valid >= 0 and right_valid < len(interpolated):
                # Linear interpolation
                interp_values = np.interp(
                    np.arange(start_idx, end_idx + 1),
                    [left_valid, right_valid],
                    [interpolated[left_valid], interpolated[right_valid]]
                )
                interpolated[start_idx:end_idx+1] = interp_values
            else:
                # Fill with NaN if we can't interpolate
                for idx in group:
                    if idx < len(interpolated):
                        interpolated[idx] = np.nan
    
    return interpolated, blink_indices

def process_pupil_data(df: pd.DataFrame, fs: float = 1000.0, cutoff: float = 4.0) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Process pupil data: interpolate blinks and apply lowpass filter.
    
    Args:
        df: DataFrame with 'pupil_diameter' column
        fs: Sampling frequency (Hz)
        cutoff: Cutoff frequency for lowpass filter (Hz)
        
    Returns:
        Tuple of (processed_df, exclusion_stats)
    """
    if 'pupil_diameter' not in df.columns:
        raise ValueError("DataFrame must contain 'pupil_diameter' column")
    
    stats = {
        'blink_interpolated': 0,
        'lowpass_applied': 0,
        'excluded_high_missing': 0
    }
    
    # Convert to numpy for processing
    pupil_data = df['pupil_diameter'].values.copy()
    
    # Interpolate blinks
    processed_data, blink_indices = interpolate_blinks(pupil_data)
    stats['blink_interpolated'] = len(blink_indices)
    
    # Count missing values after interpolation
    missing_count = np.sum(np.isnan(processed_data))
    missing_ratio = missing_count / len(processed_data) if len(processed_data) > 0 else 0
    
    # Exclude if too many missing samples (>30%)
    if missing_ratio > 0.30:
        stats['excluded_high_missing'] = 1
        logger.warning(f"Excluding dataset: {missing_ratio:.2%} missing samples after blink interpolation.")
        # Return empty or mark as excluded
        df['processed_pupil_diameter'] = np.nan
        return df, stats
    
    # Apply lowpass filter
    filtered_data = lowpass_filter(processed_data, fs, cutoff)
    stats['lowpass_applied'] = 1
    
    # Update dataframe
    df['processed_pupil_diameter'] = filtered_data
    
    return df, stats

def apply_filter_to_dataset(df: pd.DataFrame, fs: float = 1000.0, cutoff: float = 4.0) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Apply full filtering pipeline to a dataset.
    
    Args:
        df: Input DataFrame
        fs: Sampling frequency (Hz)
        cutoff: Cutoff frequency (Hz)
        
    Returns:
        Tuple of (processed_df, stats)
    """
    return process_pupil_data(df, fs, cutoff)

def write_quality_report(stats_list: List[Dict[str, Any]], output_path: str = "results/quality_report.csv") -> None:
    """
    Write quality report to CSV, appending to existing headers if file exists.
    
    Args:
        stats_list: List of dictionaries containing exclusion statistics
        output_path: Path to output CSV file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define columns
    columns = ['exclusion_type', 'count']
    
    # Check if file exists to determine if headers need to be written
    write_headers = not path.exists()
    
    with open(path, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        if write_headers:
            writer.writerow(columns)
        
        for stats in stats_list:
            for exclusion_type, count in stats.items():
                if count > 0:
                    writer.writerow([exclusion_type, count])
    
    logger.info(f"Quality report appended to {output_path}")

def main():
    """
    Main function to demonstrate quality report generation.
    This function is intended to be called by the main pipeline orchestrator.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate quality report for preprocessing")
    parser.add_argument("--stats-json", type=str, help="JSON string of stats to append", default='[]')
    parser.add_argument("--output", type=str, default="results/quality_report.csv", help="Output CSV path")
    
    args = parser.parse_args()
    
    import json
    stats_list = json.loads(args.stats_json)
    
    write_quality_report(stats_list, args.output)
    logger.info("Quality report generation complete.")

if __name__ == "__main__":
    main()