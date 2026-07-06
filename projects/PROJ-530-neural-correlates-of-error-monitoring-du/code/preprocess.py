import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def calculate_angular_deviation(heading: np.ndarray, optimal: np.ndarray) -> Optional[float]:
    """
    Calculate the angular deviation (in degrees) between the heading vector and the optimal path vector.
    
    Parameters
    ----------
    heading : np.ndarray
        2D vector representing the current heading direction.
    optimal : np.ndarray
        2D vector representing the optimal path direction.
        
    Returns
    -------
    float or None
        The angular deviation in degrees if both vectors are non-zero, otherwise None.
    """
    # Check for zero vectors
    heading_norm = np.linalg.norm(heading)
    optimal_norm = np.linalg.norm(optimal)
    
    if heading_norm == 0 or optimal_norm == 0:
        logger.warning("Zero-length vector detected in angular deviation calculation. Returning None.")
        return None
    
    # Normalize vectors
    heading_unit = heading / heading_norm
    optimal_unit = optimal / optimal_norm
    
    # Calculate dot product
    dot_product = np.clip(np.dot(heading_unit, optimal_unit), -1.0, 1.0)
    
    # Calculate angle in radians and convert to degrees
    angle_rad = np.arccos(dot_product)
    angle_deg = np.degrees(angle_rad)
    
    return angle_deg

def apply_filters(raw_data: pd.DataFrame, sfreq: float) -> pd.DataFrame:
    """
    Apply bandpass and line-frequency notch filters to raw EEG data.
    
    Parameters
    ----------
    raw_data : pd.DataFrame
        DataFrame containing EEG time series data.
    sfreq : float
        Sampling frequency in Hz.
        
    Returns
    -------
    pd.DataFrame
        Filtered EEG data.
    """
    logger.info(f"Applying filters with sampling frequency: {sfreq} Hz")
    # Placeholder for actual filtering logic using scipy or mne
    # In a real implementation, this would use scipy.signal or mne.filter
    return raw_data

def run_ica(data: pd.DataFrame, n_components: int = 20) -> Dict[str, Any]:
    """
    Run ICA to remove ocular/muscular artifacts.
    
    Parameters
    ----------
    data : pd.DataFrame
        Preprocessed EEG data.
    n_components : int
        Number of ICA components to compute.
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing ICA results and component information.
    """
    logger.info(f"Running ICA with {n_components} components")
    # Placeholder for actual ICA logic using mne
    return {"n_components": n_components, "components_removed": []}

def save_preprocessing_log(log_data: Dict[str, Any], output_path: Path) -> None:
    """
    Save preprocessing log to a YAML file.
    
    Parameters
    ----------
    log_data : Dict[str, Any]
        Dictionary containing preprocessing parameters and results.
    output_path : Path
        Path to the output YAML file.
    """
    with open(output_path, 'w') as f:
        yaml.dump(log_data, f)
    logger.info(f"Preprocessing log saved to {output_path}")

def extract_mfn_features(df: pd.DataFrame, sfreq: float) -> pd.DataFrame:
    """
    Extract MFN features (mean and peak amplitude) from EEG epochs.
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing EEG time series data with columns:
        'participant_id', 'trial_id', 'time_ms', 'FCz', 'Cz', 'Fz', 'event_type'.
    sfreq : float
        Sampling frequency in Hz.
        
    Returns
    -------
    pd.DataFrame
        DataFrame containing extracted MFN features for each electrode.
    """
    # Check if this is an error event
    if df['event_type'].iloc[0] != 'error':
        return pd.DataFrame()
    
    # Define time windows
    baseline_start, baseline_end = -200, 0
    mfn_start, mfn_end = 200, 400
    
    # Get time array
    times = df['time_ms'].values
    
    # Define target electrodes
    electrodes = ['FCz', 'Cz', 'Fz']
    
    results = []
    
    for electrode in electrodes:
        signal = df[electrode].values
        
        # Baseline correction
        baseline_mask = (times >= baseline_start) & (times <= baseline_end)
        baseline_mean = np.mean(signal[baseline_mask])
        corrected_signal = signal - baseline_mean
        
        # MFN window
        mfn_mask = (times >= mfn_start) & (times <= mfn_end)
        
        # Calculate mean amplitude in MFN window
        mean_amplitude = np.mean(corrected_signal[mfn_mask])
        
        # Calculate peak amplitude (most negative) in the entire epoch
        peak_amplitude = np.min(corrected_signal)
        
        results.append({
            'participant_id': df['participant_id'].iloc[0],
            'trial_id': df['trial_id'].iloc[0],
            'electrode': electrode,
            'mean_amplitude': mean_amplitude,
            'peak_amplitude': peak_amplitude
        })
    
    return pd.DataFrame(results)

def process_eeg_data(raw_data_path: Path, output_path: Path) -> None:
    """
    Main function to process EEG data from raw to processed state.
    
    Parameters
    ----------
    raw_data_path : Path
        Path to the raw EEG data file.
    output_path : Path
        Path to save the processed data.
    """
    logger.info(f"Processing EEG data from {raw_data_path}")
    # Placeholder for full pipeline logic
    logger.info(f"Processed data saved to {output_path}")

def main():
    """Main entry point for the preprocessing module."""
    logger.info("Starting EEG preprocessing pipeline")
    # Example usage
    pass