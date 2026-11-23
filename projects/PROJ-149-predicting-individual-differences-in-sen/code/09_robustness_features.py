"""
Robustness Feature Extraction (T025b)

Re-runs PSD extraction, band aggregation, and relative power calculation
with a 2-second window size to assess parameter sensitivity (FR-008).

Outputs:
    data/processed/robustness_features_2s.csv
"""
import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import local utils and config
# We assume config.py is in the same directory or parent
try:
    from config import get_path, ensure_dirs, EPSILON
except ImportError:
    # Fallback for execution context where config is in root
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from config import get_path, ensure_dirs, EPSILON

# Constants for Robustness Check
ROBUSTNESS_WINDOW_SIZE = 2  # Override default 4s with 2s as per task
DEFAULT_OVERLAP = 0.5
BANDS = {
    'delta': (1, 4),
    'theta': (4, 8),
    'alpha': (8, 13),
    'low_beta': (13, 20),
    'high_beta': (20, 30),
    'gamma': (30, 40)
}

def load_exclusion_log() -> pd.DataFrame:
    """Load the main exclusion log to determine valid participants."""
    # T010 outputs this file
    path = get_path("data/interim/exclusion_log.csv")
    if not os.path.exists(path):
        # Fallback if path logic differs
        path = "data/interim/exclusion_log.csv"
    return pd.read_csv(path)

def load_preprocessed_eeg(input_dir: str) -> Dict[str, np.ndarray]:
    """
    Load preprocessed EEG data (FIF files) from the robustness output of T025a.
    T025a output: data/interim/robustness_no_ica_eeg/
    Returns a dict mapping participant_id -> (n_channels, n_times) array.
    """
    # T025a produces robustness_no_ica_eeg directory
    base_dir = get_path("data/interim/robustness_no_ica_eeg")
    if not os.path.exists(base_dir):
        raise FileNotFoundError(f"Robustness preprocessed data not found at {base_dir}. Run T025a first.")
    
    data = {}
    # Assuming FIF files are named like sub-XX_eeg.fif
    files = glob.glob(os.path.join(base_dir, "**", "*.fif"), recursive=True)
    
    for f_path in files:
        try:
            import mne
            raw = mne.io.read_raw_fif(f_path, preload=True)
            # Extract subject ID from filename or info
            # Assuming filename pattern: sub-<id>_eeg.fif or similar
            fname = os.path.basename(f_path)
            # Simple heuristic: extract 'sub-XX' part
            parts = fname.split('_')
            sub_id = None
            for p in parts:
                if p.startswith('sub-'):
                    sub_id = p.replace('sub-', '')
                    break
            if not sub_id:
                # Fallback to generic ID if pattern fails
                sub_id = os.path.splitext(fname)[0]
            
            # Get data array
            arr = raw.get_data()
            data[sub_id] = arr
        except Exception as e:
            print(f"Warning: Could not load {f_path}: {e}")
            continue
    
    return data

def compute_welch_psd_chunked(data: np.ndarray, sfreq: float, window_size: float = ROBUSTNESS_WINDOW_SIZE) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Welch's PSD with the robustness window size (2s).
    Returns (freqs, psd) where psd shape is (n_channels, n_freqs).
    """
    from scipy.signal import welch
    nperseg = int(window_size * sfreq)
    noverlap = int(nperseg * DEFAULT_OVERLAP)
    
    # Compute PSD for all channels
    # scipy.signal.welch can handle 2D input (n_channels, n_times)
    freqs, psd = welch(data, fs=sfreq, nperseg=nperseg, noverlap=noverlap, axis=1)
    return freqs, psd

def aggregate_band_power(freqs: np.ndarray, psd: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Integrate power within canonical bands.
    Returns dict of band_name -> (n_channels,) array of mean power.
    """
    band_powers = {}
    for band, (f_min, f_max) in BANDS.items():
        mask = (freqs >= f_min) & (freqs <= f_max)
        if np.sum(mask) > 0:
            # Mean power in band
            band_powers[band] = np.mean(psd[:, mask], axis=1)
        else:
            band_powers[band] = np.zeros(psd.shape[0])
    return band_powers

def compute_relative_power(band_powers: Dict[str, np.ndarray], total_power: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Compute relative power = band_power / total_power.
    total_power is sum of all band powers or integral over 1-40Hz.
    Here we approximate total as sum of the 6 bands for consistency.
    """
    # Sum of all bands
    total = sum(band_powers.values())
    # Avoid division by zero
    total = np.maximum(total, EPSILON)
    
    relative = {}
    for band, power in band_powers.items():
        relative[band] = power / total
    return relative

def extract_features_for_subject(
    sub_id: str,
    data: np.ndarray,
    sfreq: float,
    median_rt: Optional[float] = None
) -> pd.DataFrame:
    """
    Process one subject: PSD -> Band Power -> Relative Power.
    Returns a DataFrame row.
    """
    # 1. Compute PSD
    freqs, psd = compute_welch_psd_chunked(data, sfreq)
    
    # 2. Aggregate Bands
    band_powers = aggregate_band_power(freqs, psd)
    
    # 3. Compute Relative Power
    relative_powers = compute_relative_power(band_powers, None)
    
    # 4. Aggregate across channels (Global Mean)
    row = {'participant_id': sub_id}
    if median_rt is not None:
        row['median_rt'] = median_rt
    
    for band, rel_power in relative_powers.items():
        row[f'{band}_rel'] = np.mean(rel_power)
    
    return pd.DataFrame([row])

def load_behavioral_metrics() -> pd.DataFrame:
    """Load behavioral metrics to join with EEG features."""
    # T013 outputs this
    path = get_path("data/interim/behavioral_metrics.csv")
    if not os.path.exists(path):
        path = "data/interim/behavioral_metrics.csv"
    return pd.read_csv(path)

def run_robustness_extraction():
    """Main pipeline for T025b."""
    print("Starting Robustness Feature Extraction (T025b) with 2s windows...")
    
    # 1. Load Preprocessed Data (from T025a)
    eeg_data = load_preprocessed_eeg("data/interim/robustness_no_ica_eeg")
    if not eeg_data:
        print("Error: No EEG data found. Ensure T025a has run.")
        return
    
    # 2. Load Behavioral Metrics
    behavior_df = load_behavioral_metrics()
    behavior_dict = dict(zip(behavior_df['participant_id'], behavior_df['median_rt']))
    
    # 3. Process each subject
    results = []
    for sub_id, data in eeg_data.items():
        # Skip if not in behavioral metrics (safety)
        if sub_id not in behavior_dict:
            continue
        
        try:
            # data shape: (n_channels, n_times)
            sfreq = 500 # PhysioNet EEG Motor Movement/Imagery is typically 500Hz
            # If we had the raw object we could get sfreq, but we assume standard here
            # or try to infer from length if needed. For robustness, we assume 500Hz.
            
            row = extract_features_for_subject(sub_id, data, sfreq, behavior_dict[sub_id])
            results.append(row)
        except Exception as e:
            print(f"Error processing {sub_id}: {e}")
            continue
    
    if not results:
        print("No features extracted. Check data alignment.")
        return

    # 4. Combine and Save
    final_df = pd.concat(results, ignore_index=True)
    
    # Ensure columns are in expected order
    cols = ['participant_id', 'median_rt', 'delta_rel', 'theta_rel', 'alpha_rel', 
            'low_beta_rel', 'high_beta_rel', 'gamma_rel']
    # Reorder if present
    final_df = final_df[[c for c in cols if c in final_df.columns]]
    
    # Output path
    output_path = get_path("data/processed/robustness_features_2s.csv")
    ensure_dirs(output_path)
    
    final_df.to_csv(output_path, index=False)
    print(f"Robustness features saved to {output_path}")

def main():
    run_robustness_extraction()

if __name__ == "__main__":
    main()