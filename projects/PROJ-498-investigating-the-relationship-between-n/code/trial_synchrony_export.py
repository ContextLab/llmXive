"""
Module: trial_synchrony_export.py
Purpose: Generate the per-trial synchrony CSV artifact (T036).

This module implements the logic to:
1. Load pre-processed epoch data and behavioral data per subject.
2. Compute trial-level synchrony metrics (mean PLV/wPLI) for the pre-stimulus window.
3. Merge with behavioral data (Reaction Time).
4. Filter out rows with missing synchrony or RT.
5. Save the result to `data/trial_level/per_trial_synchrony.csv`.
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Import from project modules based on provided API surface
from config import ensure_directories
from analysis import load_subject_epochs, extract_trial_behavioral_data
from synchrony import compute_synchrony_metrics, get_pair_id, get_theta_filtered_data, get_gamma_filtered_data, prepare_data_for_synchrony

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
TRIAL_LEVEL_DIR = DATA_DIR / "trial_level"
OUTPUT_FILE = TRIAL_LEVEL_DIR / "per_trial_synchrony.csv"

# Pre-stimulus window for synchrony calculation (matches T016 epoching: -1000ms to 0ms)
# We focus on the last 200ms before stimulus for pre-stimulus synchrony as per standard practice
# unless the spec implies the whole baseline. Using [-200, 0]ms is standard for pre-stimulus.
# However, T016 says -1000 to +2000. T024 says "pre-stimulus window".
# We will use the full baseline if available, or [-200, 0] if specific.
# Given the task T036 is about "per trial", we calculate synchrony for each epoch.
PRE_STIM_MIN = -1.0  # Start of epoch (ms -> s)
PRE_STIM_MAX = 0.0   # Stimulus onset

def load_subject_data(subject_id: str) -> Optional[Tuple[pd.DataFrame, Dict]]:
    """
    Load epoch data and behavioral data for a specific subject.
    Returns (behavioral_df, epochs_obj) or None if data missing.
    """
    try:
        # Load behavioral data (RT, Condition)
        # Assuming T030/T035 generated trial-level behavioral data or we extract it from epochs
        # The analysis.py `extract_trial_behavioral_data` likely returns a DataFrame.
        # We need to reconstruct the trial-level data if not already saved as a CSV by T035.
        # T035 saves trial_level_analysis.json, but T036 needs a CSV with specific columns.
        
        # Strategy: Load epochs from data/processed/{subject_id}_epochs.fif (or similar)
        # and behavioral data from data/trial_level/{subject_id}_behavior.csv (if T035 created it)
        # or extract from the epochs info if available.
        
        # Since T035 is "run_trial_level_lme" and likely saved a JSON, we might need to
        # re-extract or rely on the existence of a CSV from T035's internal step.
        # Let's assume the analysis module provides a way to get trial data.
        
        # Fallback: If T035 didn't save a CSV, we must construct it from the epochs and metadata.
        # For this implementation, we assume `extract_trial_behavioral_data` from analysis.py
        # returns a DataFrame with columns: subject_id, trial_id, condition, rt.
        
        behavioral_df = extract_trial_behavioral_data(subject_id)
        
        if behavioral_df is None or behavioral_df.empty:
            return None
        
        # Load epochs
        # The path is usually data/processed/subject_id/subject_id-epo.fif or similar
        # We need to find the exact path used in T019.
        # Let's assume a standard naming: data/processed/{subject_id}_epochs.fif
        epoch_path = PROCESSED_DIR / f"{subject_id}_epochs.fif"
        
        if not epoch_path.exists():
            # Try alternative naming if standard fails
            epoch_path = PROCESSED_DIR / subject_id / f"{subject_id}-epo.fif"
            if not epoch_path.exists():
                return None

        epochs = load_subject_epochs(subject_id)
        if epochs is None:
            return None
        
        return behavioral_df, epochs
        
    except Exception as e:
        print(f"Error loading data for {subject_id}: {e}")
        return None

def compute_trial_synchrony(epochs, behavioral_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute synchrony for each trial (epoch) and merge with behavioral data.
    """
    if epochs is None or behavioral_df is None:
        return pd.DataFrame()

    n_trials = len(epochs)
    if n_trials == 0:
        return pd.DataFrame()

    # Prepare data for synchrony calculation
    # We need to extract the pre-stimulus window from each epoch
    # and compute the synchrony metric (e.g., wPLI) for the defined electrode pairs.
    
    # Get electrode pairs (Frontoparietal)
    # These are defined in synchrony.py
    from synchrony import get_cross_region_pairs
    pairs = get_cross_region_pairs()
    
    if not pairs:
        print("No electrode pairs found for synchrony calculation.")
        return pd.DataFrame()

    # We will calculate the mean synchrony across the selected pairs for each trial
    # or calculate per pair and then aggregate. The task asks for a single 'synchrony' column.
    # We will compute the mean wPLI across the frontoparietal pairs for the pre-stimulus window.
    
    trial_synchrony_values = []
    
    # Extract data: shape (n_epochs, n_channels, n_times)
    data = epochs.get_data()  # in Volts
    times = epochs.times
    
    # Determine indices for pre-stimulus window
    mask = (times >= PRE_STIM_MIN) & (times <= PRE_STIM_MAX)
    if not np.any(mask):
        print(f"No time points found in window [{PRE_STIM_MIN}, {PRE_STIM_MAX}]")
        return pd.DataFrame()
        
    pre_stim_data = data[:, :, mask]
    pre_stim_times = times[mask]
    
    # We need to map electrode names to indices in the data array
    ch_names = epochs.ch_names
    ch_name_to_idx = {name: i for i, name in enumerate(ch_names)}
    
    # Filter bands (Theta and Gamma) as per T023/T024
    # We will compute synchrony for both and average, or pick one?
    # T025 says "theta and gamma". T036 asks for one 'synchrony' column.
    # We will compute the mean wPLI across Theta and Gamma bands for the frontoparietal pairs.
    
    # Helper to filter data in a specific band
    def filter_band(data, sfreq, low, high):
        from scipy.signal import butter, filtfilt
        b, a = butter(4, [low/(sfreq/2), high/(sfreq/2)], btype='band')
        # Apply filter to each epoch, each channel
        filtered = np.zeros_like(data)
        for e in range(data.shape[0]):
            for c in range(data.shape[1]):
                filtered[e, c, :] = filtfilt(b, a, data[e, c, :])
        return filtered

    sfreq = epochs.info['sfreq']
    
    # Theta: 4-7 Hz, Gamma: 30-45 Hz (approx, based on T023)
    theta_data = filter_band(pre_stim_data, sfreq, 4, 7)
    gamma_data = filter_band(pre_stim_data, sfreq, 30, 45)
    
    # Compute wPLI for each pair and each trial
    # wPLI formula: |mean(Im(COH))| / mean(|Im(COH)|)
    # We'll use a simplified implementation or mne if available, but mne's wpli is for epochs.
    # Since we need per-trial, we compute it manually for the specific window.
    
    def compute_wpli_trial(x, y):
        # x, y: (n_times,)
        # Cross-spectrum
        # Use FFT
        n = len(x)
        X = np.fft.rfft(x)
        Y = np.fft.rfft(y)
        # Cross-spectral density
        Cxy = X * np.conj(Y)
        # Imaginary part
        ImCxy = np.imag(Cxy)
        # wPLI = |mean(Im)| / mean(|Im|)
        # Avoid division by zero
        if np.mean(np.abs(ImCxy)) < 1e-10:
            return 0.0
        return np.abs(np.mean(ImCxy)) / np.mean(np.abs(ImCxy))

    # We will aggregate synchrony across pairs and bands for a single metric per trial
    # Or maybe the task implies one column per pair? "synchrony" implies one value.
    # Let's compute the mean wPLI across all frontoparietal pairs and both bands.
    
    trial_sync_list = []
    
    for i in range(n_trials):
        trial_theta = theta_data[i] # (n_channels, n_times)
        trial_gamma = gamma_data[i]
        
        pair_vals = []
        
        for (ch1, ch2) in pairs:
            if ch1 not in ch_name_to_idx or ch2 not in ch_name_to_idx:
                continue
            
            idx1 = ch_name_to_idx[ch1]
            idx2 = ch_name_to_idx[ch2]
            
            # Theta
            wpli_theta = compute_wpli_trial(trial_theta[idx1, :], trial_theta[idx2, :])
            # Gamma
            wpli_gamma = compute_wpli_trial(trial_gamma[idx1, :], trial_gamma[idx2, :])
            
            pair_vals.extend([wpli_theta, wpli_gamma])
        
        if pair_vals:
            mean_sync = np.mean(pair_vals)
        else:
            mean_sync = np.nan
        
        trial_sync_list.append(mean_sync)
    
    # Create DataFrame
    sync_df = pd.DataFrame({
        'trial_id': range(len(trial_sync_list)),
        'synchrony': trial_sync_list
    })
    
    # Merge with behavioral data
    # Ensure trial_ids match. behavioral_df should have 'trial_id'
    if 'trial_id' not in behavioral_df.columns:
        # If not, assume order matches
        behavioral_df['trial_id'] = range(len(behavioral_df))
        
    merged = pd.merge(behavioral_df, sync_df, on='trial_id', how='inner')
    
    # Add subject_id
    merged['subject_id'] = behavioral_df['subject_id'].iloc[0] if 'subject_id' in behavioral_df.columns else behavioral_df.index[0]
    
    # Select and order columns: subject_id, trial_id, condition, synchrony, rt
    # Note: 'rt' might be named 'reaction_time' or 'rt'. Check behavioral_df
    rt_col = None
    for col in ['rt', 'reaction_time', 'RT']:
        if col in merged.columns:
            rt_col = col
            break
    
    if rt_col:
        merged = merged.rename(columns={rt_col: 'rt'})
    
    required_cols = ['subject_id', 'trial_id', 'condition', 'synchrony', 'rt']
    # Ensure all required columns exist
    for col in required_cols:
        if col not in merged.columns:
            # Fill with NaN if missing
            merged[col] = np.nan
    
    return merged[required_cols]

def generate_trial_level_synchrony_csv():
    """
    Main entry point for T036.
    Iterates over all subjects, computes trial-level synchrony,
    and saves the aggregated CSV to data/trial_level/per_trial_synchrony.csv.
    """
    ensure_directories() # Ensure output dir exists
    
    # Get list of subjects from processed data
    # Assuming subjects are in data/processed/
    subjects = []
    if PROCESSED_DIR.exists():
        for item in PROCESSED_DIR.iterdir():
            if item.is_dir() or item.name.endswith('_epochs.fif'):
                # Extract subject ID
                name = item.name
                if name.endswith('_epochs.fif'):
                    sid = name.replace('_epochs.fif', '')
                else:
                    sid = item.name
                subjects.append(sid)
    
    if not subjects:
        print("No subject data found in data/processed/")
        # Create empty file with headers
        output_df = pd.DataFrame(columns=['subject_id', 'trial_id', 'condition', 'synchrony', 'rt'])
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        output_df.to_csv(OUTPUT_FILE, index=False)
        return

    all_trials = []
    
    for sid in subjects:
        print(f"Processing subject: {sid}")
        data = load_subject_data(sid)
        if data is None:
            print(f"Skipping {sid}: Data not found or invalid.")
            continue
        
        behavioral_df, epochs = data
        
        # Compute synchrony
        trial_df = compute_trial_synchrony(epochs, behavioral_df)
        
        if not trial_df.empty:
            all_trials.append(trial_df)
    
    if all_trials:
        final_df = pd.concat(all_trials, ignore_index=True)
        
        # Exclude rows with missing synchrony or rt
        final_df = final_df.dropna(subset=['synchrony', 'rt'])
        
        # Ensure output directory exists
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Save
        final_df.to_csv(OUTPUT_FILE, index=False)
        print(f"Saved trial-level synchrony to {OUTPUT_FILE}")
        print(f"Total rows: {len(final_df)}")
    else:
        print("No valid trial data found.")
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['subject_id', 'trial_id', 'condition', 'synchrony', 'rt']).to_csv(OUTPUT_FILE, index=False)

if __name__ == "__main__":
    generate_trial_level_synchrony_csv()