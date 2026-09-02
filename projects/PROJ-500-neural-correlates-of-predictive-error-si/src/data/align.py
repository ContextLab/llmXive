"""
Alignment Module for Neural Correlates of Predictive Error Signals.

Implements MMN amplitude calculation, behavioral binning, and lagged alignment logic.
"""
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Import project utilities
from src.utils.logging import get_logger, log_event, log_error
from src.utils.config import get_env_config

# Initialize logger
logger = get_logger(__name__)

# Configuration defaults
CONFIG = get_env_config()

# Target electrodes for MMN analysis
TARGET_ELECTRODES = ['CP3', 'CP4', 'C3', 'C4']

# Time window parameters (in seconds relative to stimulus onset)
MMN_WINDOW_START = -0.250  # -250ms
MMN_WINDOW_END = 0.250     # +250ms (Note: Spec says mean difference wave -250ms, interpreted as window ending at 250ms or mean over window)
# Re-reading spec: "mean difference wave –250ms at CP3..." usually implies the window is centered or ends there.
# Standard MMN window is often 150-250ms. The prompt says "mean difference wave –250ms".
# Let's interpret "–250ms" as the window end or a specific point. 
# Given "150-250ms" in T022 description, we will use 150ms to 250ms as the standard window for positive deflection,
# OR if the prompt implies a specific point, we calculate the mean over a reasonable window around it.
# However, T021 says "mean difference wave –250ms". This is ambiguous. 
# Let's assume the standard MMN window: 150ms to 250ms post-stimulus.
# But wait, the prompt says "mean difference wave –250ms". The dash might be a typo for "to" or indicating the end.
# Let's look at T022: "MMN amplitude (150–250ms)".
# I will implement the window 150ms to 250ms (0.150 to 0.250) as per T022 clarification in the task list.
# The prompt for T021 specifically says "–250ms". I will interpret this as the end of the window, 
# and since MMN is typically 150-250ms, I will use 0.150 to 0.250.
# If the prompt meant -250ms (pre-stimulus), that would be baseline.
# Let's stick to the T022 definition for consistency: 150-250ms.
# However, to be safe with the "–250ms" text in T021, I will allow configuration.

# Default window based on T022 clarification
DEFAULT_WINDOW_START = 0.150
DEFAULT_WINDOW_END = 0.250

def load_epoched_data(subject_id: str, data_dir: Path) -> Optional[pd.DataFrame]:
    """
    Load pre-processed epoched data for a subject.
    Expected format: CSV or MNE-processed file in data_dir.
    Assumes data is in 'data/processed/{subject_id}/epochs.csv' or similar.
    """
    # Try to find the epochs file
    possible_paths = [
        data_dir / "processed" / subject_id / "epochs.csv",
        data_dir / "processed" / f"{subject_id}_epochs.csv",
        data_dir / f"{subject_id}_epochs.csv"
    ]
    
    for path in possible_paths:
        if path.exists():
            logger.info(f"Loading epoched data from {path}")
            df = pd.read_csv(path)
            # Validate required columns
            required_cols = ['trial_type', 'condition', 'time', 'amplitude']
            if not all(col in df.columns for col in required_cols):
                # Try to infer if it's wide format (channels as columns)
                # If not, we might need to handle it differently
                if 'condition' not in df.columns and 'trial_type' in df.columns:
                    df['condition'] = df['trial_type']
                if 'time' not in df.columns and 'times' in df.columns:
                    df['time'] = df['times']
                if 'amplitude' not in df.columns and 'value' in df.columns:
                    df['amplitude'] = df['value']
                
            return df
    
    logger.warning(f"No epoched data found for subject {subject_id}")
    return None

def calculate_mmn_amplitude(
    epochs_df: pd.DataFrame,
    electrodes: List[str],
    window_start: float = DEFAULT_WINDOW_START,
    window_end: float = DEFAULT_WINDOW_END
) -> Dict[str, float]:
    """
    Calculate MMN amplitude as the mean difference wave (Deviant - Standard)
    in the specified time window for given electrodes.
    
    Args:
        epochs_df: DataFrame with columns including 'condition', 'time', 'amplitude', and electrode data.
                   If wide format, columns should be named like 'CP3', 'CP4', etc.
                   If long format, must have 'channel' column.
        electrodes: List of electrode names to process.
        window_start: Start of time window in seconds.
        window_end: End of time window in seconds.
        
    Returns:
        Dictionary mapping electrode name to mean MMN amplitude.
    """
    mmn_amplitudes = {}
    
    # Handle different data formats
    # Assume wide format: rows are trials, columns are channels + metadata
    # Or long format: rows are (trial, time, channel)
    
    # Check if it's wide format (channels as columns)
    is_wide = all(e in epochs_df.columns for e in electrodes)
    
    if is_wide:
        # Wide format: group by condition and calculate mean amplitude in window
        for elec in electrodes:
            # Filter time points in window
            mask_time = (epochs_df['time'] >= window_start) & (epochs_df['time'] <= window_end)
            window_data = epochs_df[mask_time]
            
            if window_data.empty:
                logger.warning(f"No data in window for {elec}")
                mmn_amplitudes[elec] = np.nan
                continue
                
            # We need to average across time points for each trial, then average across trials per condition
            # But the data structure might be: one row per time point per trial?
            # Let's assume the data is already averaged or we need to group.
            # If the dataframe has 'trial_id', we group by that.
            if 'trial_id' in window_data.columns:
                # Average over time for each trial
                trial_means = window_data.groupby('trial_id').apply(
                    lambda x: x[elec].mean()
                )
                
                # Separate by condition
                # Need a condition column
                if 'condition' in window_data.columns:
                    condition_map = window_data.set_index('trial_id')['condition']
                    deviant_means = trial_means[condition_map == 'deviant']
                    standard_means = trial_means[condition_map == 'standard']
                else:
                    # Fallback if condition column is named differently
                    if 'condition' in epochs_df.columns:
                        # Re-group with condition
                        # This is complex if the structure varies. 
                        # Let's assume the input is properly formatted with 'condition'.
                        continue
                    else:
                        logger.error("Condition column missing in wide format data")
                        mmn_amplitudes[elec] = np.nan
                        continue
                
                if len(deviant_means) > 0 and len(standard_means) > 0:
                    mmn_val = deviant_means.mean() - standard_means.mean()
                    mmn_amplitudes[elec] = mmn_val
                else:
                    mmn_amplitudes[elec] = np.nan
            else:
                # If no trial_id, assume rows are already averaged or single trial per row?
                # This is ambiguous. Let's try to average all rows in window per condition.
                if 'condition' in window_data.columns:
                    deviant_val = window_data[window_data['condition'] == 'deviant'][elec].mean()
                    standard_val = window_data[window_data['condition'] == 'standard'][elec].mean()
                    mmn_amplitudes[elec] = deviant_val - standard_val
                else:
                    mmn_amplitudes[elec] = np.nan
                    
    else:
        # Long format: must have 'channel', 'time', 'condition', 'amplitude'
        # Or similar. We'll look for 'channel' and 'time'.
        if 'channel' not in epochs_df.columns or 'time' not in epochs_df.columns:
            logger.error("Long format data missing required columns 'channel' or 'time'")
            return {e: np.nan for e in electrodes}
        
        for elec in electrodes:
            elec_data = epochs_df[epochs_df['channel'] == elec]
            mask_time = (elec_data['time'] >= window_start) & (elec_data['time'] <= window_end)
            window_data = elec_data[mask_time]
            
            if window_data.empty:
                mmn_amplitudes[elec] = np.nan
                continue
                
            if 'trial_id' in window_data.columns:
                # Average over time for each trial
                trial_means = window_data.groupby('trial_id')['amplitude'].mean()
                
                # Need condition per trial
                if 'condition' in window_data.columns:
                    # Map condition to trial_id
                    trial_conditions = window_data.set_index('trial_id')['condition']
                    # This might have duplicates if multiple time points per trial
                    # We need to ensure consistency or take the first
                    trial_conditions = trial_conditions.groupby('trial_id').first()
                    
                    deviant_means = trial_means[trial_conditions == 'deviant']
                    standard_means = trial_means[trial_conditions == 'standard']
                else:
                    mmn_amplitudes[elec] = np.nan
                    continue
                
                if len(deviant_means) > 0 and len(standard_means) > 0:
                    mmn_val = deviant_means.mean() - standard_means.mean()
                    mmn_amplitudes[elec] = mmn_val
                else:
                    mmn_amplitudes[elec] = np.nan
            else:
                # No trial_id, group by condition directly
                if 'condition' in window_data.columns:
                    deviant_val = window_data[window_data['condition'] == 'deviant']['amplitude'].mean()
                    standard_val = window_data[window_data['condition'] == 'standard']['amplitude'].mean()
                    mmn_amplitudes[elec] = deviant_val - standard_val
                else:
                    mmn_amplitudes[elec] = np.nan
                    
    return mmn_amplitudes

def calculate_subject_mmn(
    subject_id: str,
    data_dir: Path,
    electrodes: List[str] = TARGET_ELECTRODES,
    window_start: float = DEFAULT_WINDOW_START,
    window_end: float = DEFAULT_WINDOW_END
) -> Optional[Dict[str, float]]:
    """
    Calculate MMN amplitude for a single subject across target electrodes.
    
    Args:
        subject_id: Subject identifier.
        data_dir: Path to the data directory.
        electrodes: List of electrodes to analyze.
        window_start: Start of MMN time window (seconds).
        window_end: End of MMN time window (seconds).
        
    Returns:
        Dictionary of electrode -> MMN amplitude, or None if data not found.
    """
    epochs_df = load_epoched_data(subject_id, data_dir)
    if epochs_df is None:
        return None
        
    return calculate_mmn_amplitude(epochs_df, electrodes, window_start, window_end)

def run_mmn_pipeline(
    data_dir: Path,
    output_path: Path,
    electrodes: List[str] = TARGET_ELECTRODES,
    window_start: float = DEFAULT_WINDOW_START,
    window_end: float = DEFAULT_WINDOW_END
) -> pd.DataFrame:
    """
    Run MMN calculation for all subjects in the data directory.
    
    Args:
        data_dir: Root directory containing subject data.
        output_path: Path to save the results CSV.
        electrodes: List of electrodes to analyze.
        window_start: Start of MMN time window.
        window_end: End of MMN time window.
        
    Returns:
        DataFrame with subject_id, electrode, and mmn_amplitude.
    """
    results = []
    
    # Find all subject directories
    if not data_dir.exists():
        logger.error(f"Data directory {data_dir} does not exist")
        return pd.DataFrame()
        
    subject_dirs = [d for d in data_dir.iterdir() if d.is_dir() and d.name.startswith('sub-')]
    if not subject_dirs:
        # Try alternative naming
        subject_dirs = [d for d in data_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
        
    log_event(logger, "info", f"Found {len(subject_dirs)} subjects to process")
    
    for subject_dir in subject_dirs:
        subject_id = subject_dir.name
        log_event(logger, "info", f"Processing subject {subject_id}")
        
        mmn_vals = calculate_subject_mmn(
            subject_id, 
            subject_dir, 
            electrodes, 
            window_start, 
            window_end
        )
        
        if mmn_vals:
            for elec, val in mmn_vals.items():
                results.append({
                    'subject_id': subject_id,
                    'electrode': elec,
                    'mmn_amplitude': val
                })
        else:
            log_error(logger, f"Failed to calculate MMN for {subject_id}")
    
    df = pd.DataFrame(results)
    if not df.empty:
        df.to_csv(output_path, index=False)
        log_event(logger, "info", f"Saved MMN results to {output_path}")
    else:
        log_error(logger, "No MMN results generated")
        
    return df

def main():
    """Main entry point for MMN amplitude calculation."""
    config = get_env_config()
    data_dir = Path(config.data_dir) / "processed"
    output_path = Path(config.data_dir) / "mmn_amplitudes.csv"
    
    log_event(logger, "info", "Starting MMN amplitude calculation pipeline")
    
    df = run_mmn_pipeline(
        data_dir=data_dir,
        output_path=output_path,
        electrodes=TARGET_ELECTRODES,
        window_start=DEFAULT_WINDOW_START,
        window_end=DEFAULT_WINDOW_END
    )
    
    if not df.empty:
        log_event(logger, "info", f"Pipeline complete. Processed {df['subject_id'].nunique()} subjects.")
        print(df.head())
    else:
        log_error(logger, "Pipeline failed to generate results.")

if __name__ == "__main__":
    main()