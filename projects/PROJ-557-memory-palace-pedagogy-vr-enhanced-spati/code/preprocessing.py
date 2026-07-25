import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union

from config import get_config
from utils.logging import log_step, log_error, setup_pipeline_logger

# Constants for filtering (derived from T005b algorithm definition)
# Cutoff frequency for low-pass filter (Hz)
LOW_PASS_CUTOFF_HZ = 4.0
# Sampling rate assumption (Hz) - typically 250Hz for Pupil Labs
DEFAULT_SAMPLING_RATE = 250.0

# Global logger
logger = None

def _get_logger():
    """Lazy initialization of the logger."""
    global logger
    if logger is None:
        logger = setup_pipeline_logger("preprocessing")
    return logger

def normalize_luminance_algorithm(luminance_values: np.ndarray, window_size: int = 100) -> np.ndarray:
    """
    Normalizes luminance values based on a rolling median to account for
    slow drifts in screen brightness or ambient light changes.
    
    Algorithm (from T005b):
    1. Compute rolling median over `window_size`.
    2. Subtract rolling median from original values.
    3. Divide by rolling standard deviation (or global std if rolling is 0)
       to normalize variance.
    
    Args:
        luminance_values: 1D numpy array of raw luminance values.
        window_size: Size of the rolling window for baseline estimation.
        
    Returns:
        Normalized luminance values (z-scored relative to local baseline).
    """
    if len(luminance_values) == 0:
        return luminance_values
    
    series = pd.Series(luminance_values)
    rolling_median = series.rolling(window=window_size, center=True, min_periods=1).median()
    rolling_std = series.rolling(window=window_size, center=True, min_periods=1).std()
    
    # Avoid division by zero
    rolling_std = rolling_std.replace(0, np.nan)
    rolling_std = rolling_std.fillna(series.std())
    
    normalized = (series - rolling_median) / rolling_std
    return normalized.values

def ingest_screen_luminance_logs(data_dir: Union[str, Path]) -> pd.DataFrame:
    """
    Ingests screen luminance logs from the raw dataset directory.
    
    The Pupil Labs ds004041 dataset typically stores screen logs in
    `data/raw/ds004041/sub-*/ses-*/func/sub-*-ses-*-screen_log.tsv`.
    This function aggregates them into a single DataFrame.
    
    Args:
        data_dir: Path to the raw data directory (data/raw).
        
    Returns:
        DataFrame with columns: ['participant_id', 'session_id', 'time', 'luminance'].
    """
    config = get_config()
    raw_path = Path(data_dir)
    logger = _get_logger()
    
    log_step(logger, "Ingesting screen luminance logs", {"path": str(raw_path)})
    
    luminance_dfs = []
    
    # Search for TSV files matching screen log pattern
    # ds004041 structure: sub-<label>/ses-<label>/func/...
    for tsv_file in raw_path.rglob("sub-*/*/*/sub-*_*_screen_log.tsv"):
        try:
            # Extract participant and session from path
            parts = tsv_file.parts
            # Assuming structure: .../sub-XX/ses-YY/func/file.tsv
            # We need to find the indices dynamically
            sub_idx = None
            ses_idx = None
            for i, part in enumerate(parts):
                if part.startswith("sub-"):
                    sub_idx = i
                elif part.startswith("ses-"):
                    ses_idx = i
            
            if sub_idx is not None and ses_idx is not None:
                participant_id = parts[sub_idx]
                session_id = parts[ses_idx]
            else:
                # Fallback if structure is unexpected
                participant_id = "unknown"
                session_id = "unknown"
                
            df = pd.read_csv(tsv_file, sep='\t')
            
            # Standardize columns if they differ slightly
            if 'time' not in df.columns:
                # Sometimes time is in a different column or index
                if 'timestamp' in df.columns:
                    df['time'] = df['timestamp']
                else:
                    df['time'] = range(len(df))
                    
            if 'luminance' not in df.columns:
                # Check for common aliases
                if 'luminance_mean' in df.columns:
                    df['luminance'] = df['luminance_mean']
                elif 'mean_luminance' in df.columns:
                    df['luminance'] = df['mean_luminance']
                else:
                    # Skip file if no luminance data
                    continue
                    
            df['participant_id'] = participant_id
            df['session_id'] = session_id
            luminance_dfs.append(df[['participant_id', 'session_id', 'time', 'luminance']])
            
        except Exception as e:
            log_error(logger, f"Failed to read luminance log {tsv_file}: {e}")
            continue
            
    if not luminance_dfs:
        raise FileNotFoundError(
            f"No screen luminance logs found in {raw_path}. "
            "Ensure the dataset ds004041 is fully downloaded and contains screen_log.tsv files."
        )
        
    combined_df = pd.concat(luminance_dfs, ignore_index=True)
    log_step(logger, "Ingestion complete", {"rows": len(combined_df)})
    return combined_df

def preprocess_luminance_for_window(
    raw_luminance: np.ndarray,
    window_size: int = 100
) -> np.ndarray:
    """
    Applies the full luminance preprocessing pipeline:
    1. Normalization (T005b algorithm)
    
    Args:
        raw_luminance: Array of raw luminance values.
        window_size: Rolling window size for normalization.
        
    Returns:
        Preprocessed (normalized) luminance values.
    """
    if raw_luminance is None or len(raw_luminance) == 0:
        return np.array([])
        
    return normalize_luminance_algorithm(raw_luminance, window_size)

def remove_blinks(pupil_data: pd.DataFrame, threshold: float = 1.5) -> pd.DataFrame:
    """
    Removes blink artifacts from pupil diameter data.
    
    Blinks are identified as sudden drops in pupil diameter or
    gaps where data is missing/zero for a significant duration.
    This implementation uses a robust z-score based outlier detection
    on the first derivative (rate of change) to identify blinks.
    
    Args:
        pupil_data: DataFrame containing 'pupil_diameter' column.
        threshold: Z-score threshold for identifying blink artifacts.
        
    Returns:
        DataFrame with blink artifacts masked (NaN).
    """
    if 'pupil_diameter' not in pupil_data.columns:
        raise ValueError("Input DataFrame must contain 'pupil_diameter' column")
        
    logger = _get_logger()
    log_step(logger, "Removing blinks", {"threshold": threshold})
    
    data = pupil_data['pupil_diameter'].values.astype(float)
    
    # Calculate first derivative (rate of change)
    # Blinks often show a sharp drop (negative spike)
    diff = np.diff(data)
    
    # Smooth the derivative slightly to avoid noise triggering false positives
    window = 5
    if len(diff) > window:
        diff_smooth = pd.Series(diff).rolling(window=window, center=True, min_periods=1).mean().values
    else:
        diff_smooth = diff
        
    # Calculate z-scores of the derivative
    mean_diff = np.mean(diff_smooth)
    std_diff = np.std(diff_smooth)
    
    if std_diff == 0:
        # No variation, no blinks
        return pupil_data
        
    z_scores = (diff_smooth - mean_diff) / std_diff
    
    # Identify blink regions: sharp drops (negative z-scores)
    # We mark the point of the drop and a small window after it as NaN
    blink_indices = np.where(z_scores < -threshold)[0]
    
    mask = np.ones(len(data), dtype=bool)
    blink_window = 10 # samples to mask after detection
    
    for idx in blink_indices:
        # Mask the drop point and subsequent samples
        start = idx
        end = min(idx + blink_window, len(data))
        mask[start:end] = False
        
    # Also handle long gaps if any (already NaN in original data)
    # This function focuses on detecting blinks in continuous data
    
    pupil_data_clean = pupil_data.copy()
    pupil_data_clean.loc[~mask, 'pupil_diameter'] = np.nan
    
    log_step(logger, "Blink removal complete", {"blinks_detected": len(blink_indices)})
    return pupil_data_clean

def low_pass_filter(signal: np.ndarray, cutoff_hz: float = LOW_PASS_CUTOFF_HZ, fs: float = DEFAULT_SAMPLING_RATE) -> np.ndarray:
    """
    Applies a low-pass Butterworth filter to remove high-frequency noise.
    
    Args:
        signal: 1D numpy array of the signal to filter.
        cutoff_hz: Cutoff frequency in Hz.
        fs: Sampling frequency in Hz.
        
    Returns:
        Filtered signal.
    """
    if len(signal) == 0:
        return signal
        
    logger = _get_logger()
    log_step(logger, "Applying low-pass filter", {"cutoff_hz": cutoff_hz, "fs": fs})
    
    nyquist = 0.5 * fs
    normalized_cutoff = cutoff_hz / nyquist
    
    if normalized_cutoff >= 1.0:
        log_error(logger, f"Cutoff frequency {cutoff_hz}Hz too high for fs={fs}Hz. Returning original signal.")
        return signal
        
    try:
        # Use a simple Butterworth filter
        # Order 4 is standard for physiological signals
        from scipy.signal import butter, filtfilt
        
        b, a = butter(4, normalized_cutoff, btype='low')
        
        # Pad signal to handle edge effects
        padded_signal = np.pad(signal, (30, 30), mode='edge')
        filtered_padded = filtfilt(b, a, padded_signal)
        
        # Remove padding
        filtered_signal = filtered_padded[30:-30]
        
        return filtered_signal
        
    except ImportError:
        raise ImportError("scipy is required for low-pass filtering. Install with: pip install scipy")

def baseline_correct(signal: np.ndarray, baseline_indices: Optional[np.ndarray] = None) -> np.ndarray:
    """
    Performs baseline correction by subtracting the mean of the baseline period.
    
    Args:
        signal: 1D numpy array of the signal.
        baseline_indices: Indices representing the baseline period.
                          If None, the first 20% of the signal is used.
                          
    Returns:
        Baseline-corrected signal.
    """
    if len(signal) == 0:
        return signal
        
    logger = _get_logger()
    
    if baseline_indices is None:
        # Default to first 20% of the signal
        baseline_len = int(len(signal) * 0.2)
        if baseline_len == 0:
            baseline_len = 1
        baseline_indices = np.arange(baseline_len)
        
    baseline_mean = np.mean(signal[baseline_indices])
    corrected_signal = signal - baseline_mean
    
    log_step(logger, "Baseline correction complete", {"baseline_mean": float(baseline_mean)})
    return corrected_signal