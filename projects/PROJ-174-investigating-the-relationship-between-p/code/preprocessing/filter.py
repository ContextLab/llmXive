import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
import csv
from pathlib import Path

from config import load_config
from logging_config import write_quality_entry

# Configure logger
logger = logging.getLogger(__name__)

def butter_lowpass(cutoff: float, fs: float, order: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """
    Design a Butterworth lowpass filter.

    Args:
        cutoff: Cutoff frequency in Hz.
        fs: Sampling frequency in Hz.
        order: Order of the filter.

    Returns:
        Tuple of (b, a) filter coefficients.
    """
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    if normal_cutoff >= 1.0:
        raise ValueError("Cutoff frequency must be less than Nyquist frequency.")
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data: np.ndarray, cutoff: float, fs: float, order: int = 5) -> np.ndarray:
    """
    Apply a lowpass Butterworth filter to the data.

    Args:
        data: 1D array of data.
        cutoff: Cutoff frequency in Hz.
        fs: Sampling frequency in Hz.
        order: Order of the filter.

    Returns:
        Filtered data.
    """
    b, a = butter_lowpass(cutoff, fs, order)
    # Handle edge cases where data length is too short for filtfilt
    if len(data) < 2 * order:
        logger.warning(f"Data length ({len(data)}) too short for filter order {order}. Returning unfiltered data.")
        return data
    
    try:
        return filtfilt(b, a, data)
    except ValueError as e:
        logger.warning(f"Filtering failed ({e}). Returning unfiltered data.")
        return data

def interpolate_blinks(data: np.ndarray, threshold: float = 0.1, max_gap: int = 50) -> np.ndarray:
    """
    Identify and interpolate blink artifacts.
    Blinks are identified as large jumps in pupil diameter.

    Args:
        data: 1D array of pupil diameter data.
        threshold: Threshold for detecting a blink (in standard deviations or absolute units depending on logic).
        max_gap: Maximum number of samples to interpolate.

    Returns:
        Data with blinks interpolated.
    """
    if len(data) == 0:
        return data

    # Calculate differences to find sudden jumps
    diff = np.diff(data)
    
    # Simple heuristic: blinks are large sudden changes
    # We'll mark points where the change exceeds a dynamic threshold
    # Assuming data is roughly normalized or we use a fixed threshold relative to std
    std_dev = np.std(data)
    if std_dev == 0:
        return data
    
    # Threshold in terms of std deviations
    blink_threshold = threshold * std_dev
    
    # Identify indices where change is significant
    blink_indices = np.where(np.abs(diff) > blink_threshold)[0] + 1
    
    if len(blink_indices) == 0:
        return data

    # Create a mask for bad data
    bad_mask = np.zeros(len(data), dtype=bool)
    
    # Mark ranges around blink indices
    for idx in blink_indices:
        # Define a window around the blink to mark as bad
        start = max(0, idx - 5)
        end = min(len(data), idx + 10)
        bad_mask[start:end] = True

    # Check if gaps are too large
    gaps = []
    current_gap_start = None
    
    for i, is_bad in enumerate(bad_mask):
        if is_bad and current_gap_start is None:
            current_gap_start = i
        elif not is_bad and current_gap_start is not None:
            if i - current_gap_start <= max_gap:
                gaps.append((current_gap_start, i))
            current_gap_start = None
    
    if current_gap_start is not None and len(data) - current_gap_start <= max_gap:
        gaps.append((current_gap_start, len(data)))

    # Interpolate
    valid_indices = np.where(~bad_mask)[0]
    if len(valid_indices) == 0:
        logger.warning("No valid data points remaining after blink detection.")
        return data

    interp_data = np.copy(data)
    if len(gaps) > 0:
        interp_data[bad_mask] = np.interp(
            np.where(bad_mask)[0],
            valid_indices,
            data[valid_indices]
        )
    
    return interp_data

def process_pupil_data(df: pd.DataFrame, fs: float, cutoff: float = 4.0, blink_threshold: float = 3.0, max_gap: int = 50) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Process pupil data: interpolate blinks and apply lowpass filter.
    Also tracks exclusion statistics.

    Args:
        df: DataFrame with 'pupil_diameter' column.
        fs: Sampling frequency.
        cutoff: Lowpass cutoff frequency.
        blink_threshold: Threshold for blink detection.
        max_gap: Maximum gap size for interpolation.

    Returns:
        Tuple of (processed_df, exclusion_stats)
    """
    stats = {
        "blink_interpolated": 0,
        "missing_samples": 0,
        "excluded_due_to_missing": 0
    }

    if 'pupil_diameter' not in df.columns:
        logger.error("DataFrame missing 'pupil_diameter' column.")
        return df, stats

    # Count missing samples
    missing_count = df['pupil_diameter'].isna().sum()
    stats["missing_samples"] = int(missing_count)
    
    if missing_count > 0:
        # Interpolate missing values linearly first
        df['pupil_diameter'] = df['pupil_diameter'].interpolate(method='linear', limit=max_gap)
        remaining_missing = df['pupil_diameter'].isna().sum()
        if remaining_missing > 0:
            stats["excluded_due_to_missing"] = int(remaining_missing)
            # Drop rows that still have missing data
            df = df.dropna(subset=['pupil_diameter'])
            logger.warning(f"Dropped {remaining_missing} rows due to missing pupil data after interpolation.")

    # Convert to numpy for processing
    pupil_data = df['pupil_diameter'].to_numpy()
    
    # Interpolate blinks
    processed_pupil = interpolate_blinks(pupil_data, threshold=blink_threshold, max_gap=max_gap)
    
    # Count interpolated points (approximation based on difference)
    # Note: A more precise count would require tracking indices in interpolate_blinks
    # Here we approximate based on the logic that significant jumps were smoothed
    diffs = np.abs(np.diff(processed_pupil))
    # Heuristic: count large local variations that might still be artifacts as interpolated
    # This is a simplification; the actual count depends on the blink detection logic
    stats["blink_interpolated"] = int(np.sum(diffs > blink_threshold * np.std(processed_pupil)))

    # Apply lowpass filter
    filtered_pupil = lowpass_filter(processed_pupil, cutoff=cutoff, fs=fs)
    
    # Update DataFrame
    df['pupil_diameter'] = filtered_pupil

    return df, stats

def apply_filter_to_dataset(df: pd.DataFrame, config: Dict[str, Any]) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Apply filtering pipeline to a dataset.

    Args:
        df: Input DataFrame.
        config: Configuration dictionary containing filter parameters.

    Returns:
        Tuple of (filtered_df, stats)
    """
    fs = config.get('paths', {}).get('sample_rate', 1000.0) # Default 1000Hz if not specified
    cutoff = config.get('thresholds', {}).get('lowpass_cutoff', 4.0)
    blink_thresh = config.get('thresholds', {}).get('blink_threshold', 3.0)
    max_gap = config.get('thresholds', {}).get('max_blink_gap', 50)

    return process_pupil_data(df, fs, cutoff, blink_thresh, max_gap)

def write_quality_report(stats_list: List[Dict[str, Any]], output_path: str) -> None:
    """
    Write exclusion statistics to the quality report CSV.
    Appends to existing file or creates new one with headers.

    Args:
        stats_list: List of dictionaries containing exclusion stats.
        output_path: Path to the output CSV file.
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Check if file exists to determine if we need headers
    file_exists = os.path.isfile(output_path)

    with open(output_path, mode='a', newline='') as f:
        writer = csv.writer(f)
        
        if not file_exists:
            # Write header
            writer.writerow(['exclusion_type', 'count'])
            logger.info(f"Created quality report at {output_path} with headers.")

        for stats in stats_list:
            for key, value in stats.items():
                if key != 'total_rows' and key != 'subject_id': # Skip non-exclusion keys
                    writer.writerow([key, value])
    
    logger.info(f"Quality report updated at {output_path}.")

def main():
    """
    Main entry point for testing the filter module.
    """
    config = load_config()
    
    # Example usage simulation
    print("Filter module loaded successfully.")
    print(f"Config loaded: {list(config.keys())}")

if __name__ == "__main__":
    main()