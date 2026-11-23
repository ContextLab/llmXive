import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt
from typing import Tuple, Optional, List, Dict, Any
import logging
import os
import sys
from pathlib import Path

# Import LoggingContext from the established utility module
from utils.logging_config import LoggingContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def butter_lowpass(cutoff: float, fs: float, order: int = 5) -> Tuple[Any, Any]:
    """
    Design a lowpass Butterworth filter.

    Args:
        cutoff (float): Cutoff frequency in Hz.
        fs (float): Sampling frequency in Hz.
        order (int): Order of the filter.

    Returns:
        Tuple of filter coefficients (b, a).
    """
    nyq = 0.5 * fs
    normalized_cutoff = cutoff / nyq
    if normalized_cutoff >= 1.0:
        logger.warning(f"Normalized cutoff {normalized_cutoff} >= 1.0, clamping to 0.99")
        normalized_cutoff = 0.99
    b, a = butter(order, normalized_cutoff, btype='low', analog=False)
    return b, a

def lowpass_filter(data: np.ndarray, cutoff: float, fs: float, order: int = 5) -> np.ndarray:
    """
    Apply a lowpass Butterworth filter to the data.

    Args:
        data (np.ndarray): Input data array.
        cutoff (float): Cutoff frequency in Hz.
        fs (float): Sampling frequency in Hz.
        order (int): Order of the filter.

    Returns:
        np.ndarray: Filtered data.
    """
    b, a = butter_lowpass(cutoff, fs, order)
    # Handle edge cases where data length is too short for filtfilt
    if len(data) < 2 * len(b):
        logger.warning(f"Data length {len(data)} too short for filtfilt with filter length {len(b)}. Returning unfiltered data.")
        return data
    try:
        filtered_data = filtfilt(b, a, data, padlen=3 * max(len(a), len(b)))
    except ValueError as e:
        logger.warning(f"filtfilt failed: {e}. Returning unfiltered data.")
        return data
    return filtered_data

def interpolate_blinks(data: np.ndarray, blink_threshold: float = 0.0, max_gap: int = 10) -> np.ndarray:
    """
    Interpolate blink artifacts in pupil data.

    Args:
        data (np.ndarray): Input pupil diameter data.
        blink_threshold (float): Threshold for detecting blinks (e.g., rate of change or absolute value).
        max_gap (int): Maximum gap size to interpolate.

    Returns:
        np.ndarray: Data with interpolated blink artifacts.
    """
    # Simple blink detection: large jumps in pupil diameter
    # Assuming blinks cause a sudden drop to near zero or a large spike
    # Here we detect values that are significantly lower than the local median or zero
    # A more robust method might use velocity thresholds, but this is a baseline.
    
    # Detect zeros or near-zeros as potential blinks
    is_blink = np.abs(data) < blink_threshold
    
    # Find indices of blinks
    blink_indices = np.where(is_blink)[0]
    
    if len(blink_indices) == 0:
        return data.copy()

    interpolated_data = data.copy()
    gaps = []
    
    # Identify contiguous gaps
    if len(blink_indices) > 0:
        gaps_start = [blink_indices[0]]
        gaps_end = [blink_indices[0]]
        
        for i in range(1, len(blink_indices)):
            if blink_indices[i] == blink_indices[i-1] + 1:
                gaps_end[-1] = blink_indices[i]
            else:
                gaps_start.append(blink_indices[i])
                gaps_end.append(blink_indices[i])
        
        for start, end in zip(gaps_start, gaps_end):
            if (end - start + 1) <= max_gap:
                # Linear interpolation
                # Find valid neighbors
                left_idx = start - 1 if start > 0 else None
                right_idx = end + 1 if end < len(data) - 1 else None
                
                if left_idx is not None and right_idx is not None:
                    y0 = data[left_idx]
                    y1 = data[right_idx]
                    x0, x1 = left_idx, right_idx
                    x_interp = np.arange(start, end + 1)
                    y_interp = np.interp(x_interp, [x0, x1], [y0, y1])
                    interpolated_data[start:end+1] = y_interp
                elif left_idx is not None:
                    interpolated_data[start:end+1] = data[left_idx]
                elif right_idx is not None:
                    interpolated_data[start:end+1] = data[right_idx]
            else:
                # Gap too large, mark as NaN or keep as is (depending on policy)
                # For now, we leave it as is but could mark as NaN for exclusion later
                pass
                
    return interpolated_data

def process_pupil_data(
    df: pd.DataFrame,
    pupil_col: str = 'pupil_diameter',
    fs: float = 1000.0,
    cutoff: float = 4.0,
    blink_threshold: float = 0.0,
    max_blink_gap: int = 10,
    exclusion_threshold: float = 0.30
) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Process pupil data: interpolate blinks, apply lowpass filter, and track exclusions.

    Args:
        df (pd.DataFrame): Input DataFrame with pupil data.
        pupil_col (str): Name of the pupil diameter column.
        fs (float): Sampling frequency in Hz.
        cutoff (float): Lowpass filter cutoff frequency in Hz.
        blink_threshold (float): Threshold for blink detection.
        max_blink_gap (int): Maximum gap size for blink interpolation.
        exclusion_threshold (float): Threshold for missing data exclusion (fraction).

    Returns:
        Tuple[pd.DataFrame, Dict[str, int]]: Processed DataFrame and exclusion counts.
    """
    exclusion_counts = {
        'blink_interpolated': 0,
        'missing_data_excluded': 0,
        'filter_applied': 0
    }
    
    if pupil_col not in df.columns:
        logger.error(f"Pupil column '{pupil_col}' not found in DataFrame.")
        return df, exclusion_counts

    # Convert to numpy for processing
    pupil_data = df[pupil_col].values.copy()
    
    # 1. Blink Interpolation
    # Count blinks before interpolation
    is_blink_before = np.abs(pupil_data) < blink_threshold
    blink_count = np.sum(is_blink_before)
    exclusion_counts['blink_interpolated'] = blink_count
    
    interpolated_data = interpolate_blinks(pupil_data, blink_threshold, max_blink_gap)
    
    # 2. Lowpass Filter
    filtered_data = lowpass_filter(interpolated_data, cutoff, fs)
    exclusion_counts['filter_applied'] = len(filtered_data)
    
    # 3. Missing Data Exclusion Check
    # Identify NaNs or invalid values (if any remain)
    missing_mask = ~np.isfinite(filtered_data)
    missing_ratio = np.sum(missing_mask) / len(filtered_data)
    
    if missing_ratio > exclusion_threshold:
        exclusion_counts['missing_data_excluded'] = int(missing_ratio * 100) # Store as percentage or count? Task says count.
        # Actually, the task says "missing samples (>30% exclusion)". 
        # If the ratio is > 30%, we might exclude the *trial* or *subject* entirely.
        # For this function, we return the counts. The caller decides to drop rows.
        # Let's store the count of missing samples that triggered the threshold.
        exclusion_counts['missing_data_excluded'] = int(np.sum(missing_mask))
        logger.warning(f"Missing data ratio {missing_ratio:.2%} exceeds threshold {exclusion_threshold:.2%}.")
    else:
        # Update the column with processed data
        df[pupil_col] = filtered_data
        
    return df, exclusion_counts

def apply_filter_to_dataset(
    input_path: str,
    output_path: str,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Apply preprocessing filters to a dataset file and write the quality report.

    Args:
        input_path (str): Path to input CSV file.
        output_path (str): Path to output CSV file.
        config (Optional[Dict[str, Any]]): Configuration dictionary.
    """
    if config is None:
        config = {
            'fs': 1000.0,
            'cutoff': 4.0,
            'blink_threshold': 0.0,
            'max_blink_gap': 10,
            'exclusion_threshold': 0.30
        }
    
    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        logger.error(f"Input file {input_path} not found.")
        raise
    
    logger.info("Processing pupil data...")
    df, exclusion_counts = process_pupil_data(
        df,
        pupil_col='pupil_diameter',
        fs=config.get('fs', 1000.0),
        cutoff=config.get('cutoff', 4.0),
        blink_threshold=config.get('blink_threshold', 0.0),
        max_blink_gap=config.get('max_blink_gap', 10),
        exclusion_threshold=config.get('exclusion_threshold', 0.30)
    )
    
    logger.info(f"Saving processed data to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Write quality report
    write_quality_report(exclusion_counts)

def write_quality_report(exclusion_counts: Dict[str, int]) -> None:
    """
    Write exclusion counts to the quality report CSV using LoggingContext.

    Args:
        exclusion_counts (Dict[str, int]): Dictionary of exclusion types and counts.
    """
    # Initialize LoggingContext
    logger.info("Initializing LoggingContext for quality report...")
    context = LoggingContext()
    
    # Add exclusions to the context
    for exclusion_type, count in exclusion_counts.items():
        if count > 0:
            logger.info(f"Adding exclusion: {exclusion_type} = {count}")
            context.add_exclusion(exclusion_type, count)
    
    # Write the report
    report_path = Path("results/quality_report.csv")
    # Ensure results directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Writing quality report to {report_path}")
    context.write_report(str(report_path))
    
    # Verification: Check if the file exists and has content
    if report_path.exists():
        df_report = pd.read_csv(report_path)
        if not df_report.empty:
            logger.info(f"Quality report written successfully with {len(df_report)} entries.")
        else:
            logger.warning("Quality report is empty.")
    else:
        logger.error("Quality report file was not created.")

def main():
    """
    Main entry point for the filter module.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess pupil data with filtering and blink interpolation.")
    parser.add_argument("--input", type=str, required=True, help="Path to input CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Path to output CSV file.")
    parser.add_argument("--fs", type=float, default=1000.0, help="Sampling frequency in Hz.")
    parser.add_argument("--cutoff", type=float, default=4.0, help="Lowpass filter cutoff in Hz.")
    
    args = parser.parse_args()
    
    config = {
        'fs': args.fs,
        'cutoff': args.cutoff
    }
    
    apply_filter_to_dataset(args.input, args.output, config)

if __name__ == "__main__":
    main()