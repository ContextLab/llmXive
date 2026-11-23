"""
Preprocessing pipeline for pupil diameter data from ds004041.

Implements:
  - Blink removal (interpolation)
  - Low-pass filtering (4Hz cutoff)
  - Baseline correction
  - Luminance normalization (using algorithm from T005b)
"""
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, Union
from scipy.signal import butter, filtfilt

from config import get_config
from utils.logging import log_step, log_error

# Constants derived from T005b
# Luminance normalization algorithm:
#   normalized = (raw - screen_baseline) / screen_baseline
#   where screen_baseline is the median luminance of the screen log for the session.
LUMINANCE_NORMALIZATION_FACTOR = 1.0  # Placeholder if no log, handled in function

def _load_screen_luminance_log(session_id: str, raw_dir: Path) -> Optional[np.ndarray]:
    """
    Ingest screen luminance logs from ds004041.
    Expected path: data/raw/ds004041/sub-<session_id>/ses-01/screen_luminance.json (or similar)
    Returns a numpy array of luminance values or None if not found.
    """
    # ds004041 structure varies; we look for standard BIDS-like luminance files
    # Assuming a file named 'screen_luminance.json' or similar exists in the session dir
    # If the dataset doesn't provide this, we return None and handle gracefully.
    session_path = raw_dir / session_id
    if not session_path.exists():
        log_step(f"Session path not found for {session_id}", level="WARNING")
        return None

    # Try common filenames for luminance logs
    candidates = [
        session_path / "screen_luminance.json",
        session_path / "screen_luminance.tsv",
        session_path / "events" / "screen_luminance.json",
        session_path / "stimuli" / "screen_luminance.json",
    ]

    for candidate in candidates:
        if candidate.exists():
            log_step(f"Found luminance log at {candidate}")
            try:
                if candidate.suffix == '.json':
                    with open(candidate, 'r') as f:
                        data = json.load(f)
                        # Assume structure: {"luminance": [...]} or similar
                        if isinstance(data, dict) and "luminance" in data:
                            return np.array(data["luminance"])
                        elif isinstance(data, list):
                            return np.array(data)
                elif candidate.suffix == '.tsv':
                    df = pd.read_csv(candidate, sep='\t')
                    # Assume column name 'luminance' or first numeric column
                    if 'luminance' in df.columns:
                        return df['luminance'].values
                    elif len(df.columns) > 0:
                        return df[df.columns[0]].values
            except Exception as e:
                log_error(f"Failed to parse luminance log {candidate}: {e}")
            return None
    return None

def ingest_screen_luminance_logs(session_id: str, raw_dir: Path) -> Optional[np.ndarray]:
    """
    Wrapper to load screen luminance logs for a specific session.
    Returns the luminance array or None if ingestion fails.
    """
    return _load_screen_luminance_log(session_id, raw_dir)

def normalize_luminance_algorithm(
    pupil_data: np.ndarray,
    luminance_log: Optional[np.ndarray],
    window_start_idx: int,
    window_end_idx: int
) -> np.ndarray:
    """
    Normalize pupil diameter based on screen luminance.
    
    Algorithm (T005b):
      1. Extract luminance values corresponding to the window [start, end].
      2. Compute the median luminance of the window (screen_baseline).
      3. Normalize: normalized_pupil = raw_pupil / screen_baseline.
      
    If luminance_log is None, returns raw_pupil (no normalization).
    """
    if luminance_log is None:
        return pupil_data
    
    # Ensure indices are within bounds
    if window_end_idx > len(luminance_log):
        window_end_idx = len(luminance_log)
    if window_start_idx < 0:
        window_start_idx = 0
        
    window_luminance = luminance_log[window_start_idx:window_end_idx]
    
    if len(window_luminance) == 0:
        return pupil_data
        
    screen_baseline = np.median(window_luminance)
    if screen_baseline == 0:
        # Avoid division by zero; return raw data
        log_step("Screen luminance median is zero, skipping normalization", level="WARNING")
        return pupil_data
        
    return pupil_data / screen_baseline

def preprocess_luminance_for_window(
    pupil_series: pd.Series,
    luminance_log: Optional[np.ndarray],
    window_start_time: float,
    window_end_time: float,
    sampling_rate: float
) -> pd.Series:
    """
    Preprocess a single window of pupil data with luminance normalization.
    
    Args:
        pupil_series: Pupil diameter values (aligned by time)
        luminance_log: Screen luminance values (aligned by time)
        window_start_time: Start time of the window
        window_end_time: End time of the window
        sampling_rate: Sampling rate in Hz
        
    Returns:
        Normalized pupil series
    """
    # Convert time to indices
    start_idx = int(window_start_time * sampling_rate)
    end_idx = int(window_end_time * sampling_rate)
    
    window_pupil = pupil_series.values[start_idx:end_idx]
    normalized = normalize_luminance_algorithm(window_pupil, luminance_log, start_idx, end_idx)
    
    return pd.Series(normalized, index=pupil_series.index[start_idx:end_idx])

def remove_blinks(pupil_data: np.ndarray, threshold: float = 0.1) -> np.ndarray:
    """
    Remove blinks by interpolating over periods where the pupil diameter
    drops below a threshold (indicating a blink).
    
    Args:
        pupil_data: Raw pupil diameter array
        threshold: Threshold below which a sample is considered a blink (relative to median)
        
    Returns:
        Pupil data with blinks interpolated
    """
    if len(pupil_data) == 0:
        return pupil_data
        
    median_val = np.median(pupil_data)
    if median_val == 0:
        return pupil_data
        
    # Identify blinks: values significantly below median
    blink_mask = pupil_data < (median_val * (1 - threshold))
    
    if not np.any(blink_mask):
        return pupil_data
        
    # Create index array for interpolation
    indices = np.arange(len(pupil_data))
    valid_indices = indices[~blink_mask]
    valid_values = pupil_data[~blink_mask]
    
    if len(valid_values) == 0:
        # All data is blinks? Return zeros or NaNs
        log_step("All data points identified as blinks", level="WARNING")
        return np.full_like(pupil_data, np.nan)
        
    # Interpolate
    interpolated = np.interp(indices, valid_indices, valid_values)
    return interpolated

def low_pass_filter(data: np.ndarray, cutoff: float = 4.0, sampling_rate: float = 250.0, order: int = 4) -> np.ndarray:
    """
    Apply a low-pass Butterworth filter to remove high-frequency noise.
    
    Args:
        data: Input data array
        cutoff: Cutoff frequency in Hz
        sampling_rate: Sampling rate in Hz
        order: Filter order
        
    Returns:
        Filtered data array
    """
    if len(data) == 0:
        return data
        
    nyquist = 0.5 * sampling_rate
    if cutoff >= nyquist:
        log_step(f"Cutoff frequency {cutoff}Hz >= Nyquist {nyquist}Hz, skipping filter", level="WARNING")
        return data
        
    normalized_cutoff = cutoff / nyquist
    
    try:
        b, a = butter(order, normalized_cutoff, btype='low')
        # Use filtfilt for zero-phase filtering
        filtered = filtfilt(b, a, data, padlen=len(data))
        return filtered
    except Exception as e:
        log_error(f"Low-pass filter failed: {e}")
        return data

def baseline_correct(data: np.ndarray, baseline_window: Tuple[int, int] = (0, 100)) -> np.ndarray:
    """
    Subtract the mean of a baseline window from the entire signal.
    
    Args:
        data: Input data array
        baseline_window: Tuple (start_idx, end_idx) defining the baseline period
        
    Returns:
        Baseline-corrected data
    """
    if len(data) == 0:
        return data
        
    start, end = baseline_window
    if end > len(data):
        end = len(data)
    if start < 0:
        start = 0
        
    if start >= end:
        log_step("Invalid baseline window, skipping baseline correction", level="WARNING")
        return data
        
    baseline_mean = np.mean(data[start:end])
    return data - baseline_mean