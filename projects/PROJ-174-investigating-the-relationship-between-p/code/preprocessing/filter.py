import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
import csv
from pathlib import Path

# Import logging utilities from the shared logging module
# This ensures the quality report is initialized and written to the correct location
try:
    from logging_config import initialize_quality_report, write_quality_entry, get_logger
except ImportError:
    # Fallback if running in isolation, though project structure should allow import
    def initialize_quality_report(path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        if not os.path.exists(path):
            with open(path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['exclusion_type', 'count'])

    def write_quality_entry(path: str, exclusion_type: str, count: int) -> None:
        with open(path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([exclusion_type, count])

    def get_logger(name: str):
        return logging.getLogger(name)

logger = get_logger(__name__)

# Constants for filtering
DEFAULT_CUTOFF_HZ = 4.0
DEFAULT_EXCLUSION_THRESHOLD = 0.30  # 30% missing samples triggers exclusion
DEFAULT_MISSING_VALUE = np.nan

def butter_lowpass(cutoff: float, fs: float, order: int = 4) -> Tuple[np.ndarray, np.ndarray]:
    """
    Design a Butterworth lowpass filter.

    Args:
        cutoff (float): Cutoff frequency in Hz.
        fs (float): Sampling frequency in Hz.
        order (int): Order of the filter.

    Returns:
        Tuple of (b, a) filter coefficients.
    """
    nyquist = 0.5 * fs
    normalized_cutoff = cutoff / nyquist
    if normalized_cutoff >= 1.0:
        logger.warning(f"Cutoff frequency {cutoff} Hz is >= Nyquist {fs/2} Hz. Setting to 0.99 * Nyquist.")
        normalized_cutoff = 0.99
    
    b, a = butter(order, normalized_cutoff, btype='low')
    return b, a

def lowpass_filter(data: np.ndarray, fs: float, cutoff: float = DEFAULT_CUTOFF_HZ) -> np.ndarray:
    """
    Apply a low-pass Butterworth filter to the data.

    Args:
        data (np.ndarray): Input data array.
        fs (float): Sampling frequency in Hz.
        cutoff (float): Cutoff frequency in Hz.

    Returns:
        np.ndarray: Filtered data.
    """
    b, a = butter_lowpass(cutoff, fs)
    # Handle edge cases where data is too short for filtfilt
    if len(data) < len(a) * 2:
        logger.warning("Data length too short for filtfilt, returning original data.")
        return data
    
    try:
        filtered_data = filtfilt(b, a, data)
    except ValueError as e:
        logger.error(f"Filtering failed: {e}. Returning original data.")
        return data
    
    return filtered_data

def interpolate_blinks(pupil_data: np.ndarray, threshold: float = 50.0) -> np.ndarray:
    """
    Identify blinks (rapid changes or flatlines) and interpolate them.
    
    This is a simplified heuristic:
    1. Identify gaps (NaNs) as potential blink regions or missing data.
    2. Identify sudden jumps > threshold as blink artifacts.
    
    Args:
        pupil_data (np.ndarray): Raw pupil diameter data.
        threshold (float): Threshold for detecting blink artifacts (units of pupil diameter).

    Returns:
        np.ndarray: Data with blink artifacts interpolated.
    """
    # Work on a copy
    clean_data = pupil_data.copy()
    
    # Identify NaNs as missing (blinks often result in lost tracking)
    missing_mask = np.isnan(clean_data)
    
    # Identify sudden jumps (blinks often have sharp onset/offset)
    # Calculate differences
    diffs = np.diff(clean_data)
    # Detect jumps larger than threshold
    jump_mask = np.abs(diffs) > threshold
    # Expand jump mask to include the point before and after the jump
    blink_indices = set()
    for i, is_jump in enumerate(jump_mask):
        if is_jump:
            blink_indices.add(i)
            blink_indices.add(i+1)
            if i > 0:
                blink_indices.add(i-1)
    
    # Combine missing and jump masks
    for idx in blink_indices:
        if 0 <= idx < len(clean_data):
            clean_data[idx] = np.nan
    
    # Interpolate missing values
    # Using pandas for convenient interpolation
    series = pd.Series(clean_data)
    interpolated_series = series.interpolate(method='linear', limit_direction='both')
    
    # If interpolation leaves NaNs at edges, forward/backward fill
    final_data = interpolated_series.ffill().bfill().values
    
    return final_data

def process_pupil_data(
    data: pd.DataFrame, 
    fs: float = 250.0, 
    blink_threshold: float = 50.0,
    missing_threshold: float = DEFAULT_EXCLUSION_THRESHOLD
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Process a single subject's pupil data: interpolate blinks, filter, and check quality.

    Args:
        data (pd.DataFrame): DataFrame with columns 'timestamp' and 'pupil_diameter'.
        fs (float): Sampling frequency in Hz.
        blink_threshold (float): Threshold for blink detection.
        missing_threshold (float): Fraction of missing data that triggers exclusion.

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Processed DataFrame and quality metrics.
    """
    metrics = {
        'total_samples': len(data),
        'missing_samples': 0,
        'excluded': False,
        'exclusion_reason': None,
        'blink_interpolated': 0,
        'filtered': True
    }

    if 'pupil_diameter' not in data.columns:
        logger.error("Missing 'pupil_diameter' column in input data.")
        metrics['excluded'] = True
        metrics['exclusion_reason'] = 'Missing column: pupil_diameter'
        return data, metrics

    pupil_series = data['pupil_diameter'].values
    
    # Count initial missing
    initial_missing = np.sum(np.isnan(pupil_series))
    metrics['missing_samples'] = int(initial_missing)

    # Check exclusion threshold before processing
    if initial_missing > 0:
        missing_ratio = initial_missing / len(pupil_series)
        if missing_ratio > missing_threshold:
            logger.warning(f"Missing data ratio ({missing_ratio:.2%}) exceeds threshold ({missing_threshold}). Excluding subject.")
            metrics['excluded'] = True
            metrics['exclusion_reason'] = f'Missing data ratio {missing_ratio:.2%} > {missing_threshold}'
            return data, metrics

    # Interpolate blinks
    interpolated_data = interpolate_blinks(pupil_series, threshold=blink_threshold)
    
    # Count how many were interpolated (difference between original NaNs and final NaNs)
    final_missing = np.sum(np.isnan(interpolated_data))
    # Note: interpolate_blinks sets blinks to NaN then fills, so final_missing should be 0 if successful
    # unless edges couldn't be filled.
    metrics['blink_interpolated'] = int(initial_missing - final_missing)
    
    # Apply low-pass filter
    filtered_data = lowpass_filter(interpolated_data, fs=fs)
    
    # Update DataFrame
    processed_data = data.copy()
    processed_data['pupil_diameter_processed'] = filtered_data
    
    return processed_data, metrics

def apply_filter_to_dataset(
    input_path: str, 
    output_path: str, 
    fs: float = 250.0
) -> List[Dict[str, Any]]:
    """
    Apply the full preprocessing pipeline to a dataset file.
    
    Args:
        input_path (str): Path to input CSV.
        output_path (str): Path to output CSV.
        fs (float): Sampling frequency.

    Returns:
        List[Dict[str, Any]]: List of quality metrics for each subject/row processed.
    """
    logger.info(f"Processing file: {input_path}")
    df = pd.read_csv(input_path)
    
    # Assume the file contains multiple subjects or trials. 
    # For this implementation, we assume the file is already split or we process row-by-row if simple.
    # However, standard format is usually one subject per file or a 'subject_id' column.
    # Let's assume 'subject_id' column exists if multiple subjects in one file.
    
    quality_metrics = []
    
    if 'subject_id' in df.columns:
        subjects = df['subject_id'].unique()
        for sub in subjects:
            sub_df = df[df['subject_id'] == sub].copy()
            processed_sub_df, metrics = process_pupil_data(sub_df, fs=fs)
            quality_metrics.append(metrics)
            
            # Save processed data for this subject if needed, or accumulate
            # For now, we update the main df
            df.loc[df['subject_id'] == sub, 'pupil_diameter_processed'] = processed_sub_df['pupil_diameter_processed']
    else:
        # Single subject or trial file
        processed_df, metrics = process_pupil_data(df, fs=fs)
        quality_metrics.append(metrics)
        df = processed_df

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to: {output_path}")
    
    return quality_metrics

def write_quality_report(
    metrics_list: List[Dict[str, Any]], 
    report_path: str = "results/quality_report.csv"
) -> None:
    """
    Aggregate quality metrics and write to the quality report CSV.
    This function appends counts to the existing report file.

    Args:
        metrics_list (List[Dict[str, Any]]): List of quality metric dictionaries.
        report_path (str): Path to the output CSV file.
    """
    # Initialize the report file with headers if it doesn't exist
    # The task T005 ensures headers are initialized, but we ensure it here for robustness
    report_path_obj = Path(report_path)
    if not report_path_obj.exists():
        report_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['exclusion_type', 'count'])
    
    # Aggregate counts
    exclusion_counts = {}
    
    for metrics in metrics_list:
        if metrics.get('excluded', False):
            reason = metrics.get('exclusion_reason', 'Unknown')
            # Normalize reason to a category
            if 'Missing data ratio' in reason:
                category = 'missing_data_threshold'
            elif 'Missing column' in reason:
                category = 'missing_column'
            else:
                category = reason
            
            exclusion_counts[category] = exclusion_counts.get(category, 0) + 1
        
        # Track other metrics if needed, but the task specifically asks for exclusion counts
        # We can log blink interpolation stats to logger if needed

    # Append to CSV
    with open(report_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for exclusion_type, count in exclusion_counts.items():
            writer.writerow([exclusion_type, count])
    
    logger.info(f"Quality report updated at: {report_path}")

def main():
    """
    Main entry point for running the filter module as a script.
    Expects command line arguments or uses defaults.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess pupil data: filter and generate quality report.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file.")
    parser.add_argument("--report", type=str, default="results/quality_report.csv", help="Path to quality report CSV.")
    parser.add_argument("--fs", type=float, default=250.0, help="Sampling frequency in Hz.")
    parser.add_argument("--blink-threshold", type=float, default=50.0, help="Blink detection threshold.")
    
    args = parser.parse_args()
    
    # Setup logging
    # Assuming logging_config is set up elsewhere, but we can initialize here if needed
    # For now, rely on the module-level logger
    
    metrics = apply_filter_to_dataset(args.input, args.output, fs=args.fs)
    write_quality_report(metrics, args.report)
    
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    main()