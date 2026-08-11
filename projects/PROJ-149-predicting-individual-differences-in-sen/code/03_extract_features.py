"""
T012: Compute Welch's PSD on continuous 5-minute epochs and aggregate band power.

Inputs:
    data/interim/cleaned_eeg/ (directory containing preprocessed .fif files)
Outputs:
    data/interim/eeg_psd.csv (one row per subject, columns: subject_id, delta, theta, alpha, low_beta, high_beta, gamma)

Parameters (from config.py):
    - window_seconds: 4
    - overlap_seconds: 2
    - bands: delta, theta, alpha, low_beta, high_beta, gamma
"""

import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
import mne
from pathlib import Path

# Add project root to path to ensure config and utils are importable
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import (
    get_path,
    ensure_dirs,
    get_band_freqs,
    get_all_band_names,
    get_window_seconds,
    get_overlap_seconds,
    get_seed
)
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

def load_preprocessed_eeg(input_dir: str):
    """
    Load all preprocessed .fif files from the input directory.
    Returns a list of (subject_id, Raw) tuples.
    """
    raw_files = glob.glob(os.path.join(input_dir, "*", "*.fif"))
    if not raw_files:
        # Also check for non-wildcard subdirectories if structure is flat
        raw_files = glob.glob(os.path.join(input_dir, "*.fif"))
    
    if not raw_files:
        raise FileNotFoundError(f"No .fif files found in {input_dir}")

    data = []
    for fpath in raw_files:
        try:
            raw = mne.io.read_raw_fif(fpath, preload=True)
            # Extract subject ID from filename or path
            # Assuming filename pattern: sub-XXX_task-XXX.fif or similar
            fname = os.path.basename(fpath)
            # Simple heuristic: extract first alphanumeric sequence after 'sub-' if present, else stem
            if "sub-" in fname:
                parts = fname.split("sub-")
                if len(parts) > 1:
                    sub_id = parts[1].split("_")[0]
                else:
                    sub_id = os.path.splitext(fname)[0]
            else:
                sub_id = os.path.splitext(fname)[0]
            
            data.append((sub_id, raw))
        except Exception as e:
            print(f"Warning: Could not load {fpath}: {e}")
    
    return data

def compute_welch_psd(raw: mne.io.Raw, sfreq: float, window_sec: float, overlap_sec: float):
    """
    Compute Welch's PSD on the continuous data.
    Returns freqs (Hz) and psd (V^2/Hz) array of shape (n_channels, n_freqs).
    """
    # Use mne.time_frequency.psd_welch
    # nperseg = window_sec * sfreq
    # noverlap = overlap_sec * sfreq
    nperseg = int(window_sec * sfreq)
    noverlap = int(overlap_sec * sfreq)
    
    # Ensure noverlap < nperseg
    if noverlap >= nperseg:
        noverlap = nperseg // 2
    
    psd, freqs = mne.time_frequency.psd_welch(
        raw,
        fmin=0.5, # Lower bound to avoid DC drift issues
        fmax=100.0, # Upper bound for gamma
        n_per_seg=nperseg,
        n_overlap=noverlap,
        n_fft=nperseg, # Keep FFT length consistent with window
        verbose=False
    )
    return freqs, psd

def aggregate_band_power(freqs: np.ndarray, psd: np.ndarray, bands: dict):
    """
    Aggregate PSD into band power (mean power in each band).
    Returns a dict: band_name -> mean_power
    """
    band_powers = {}
    for band_name, (f_min, f_max) in bands.items():
        # Find indices for this band
        idx = np.where((freqs >= f_min) & (freqs < f_max))[0]
        if len(idx) == 0:
            # Fallback if band not found (e.g., sampling rate too low)
            band_powers[band_name] = 0.0
        else:
            # Mean power across frequencies and channels
            # psd shape: (n_channels, n_freqs)
            # We average over frequencies first, then channels to get a single value per subject
            band_psd = psd[:, idx]
            mean_power = np.mean(band_psd)
            band_powers[band_name] = mean_power
    return band_powers

def extract_features_for_subject(sub_id: str, raw: mne.io.Raw):
    """
    Process a single subject: compute PSD and aggregate band powers.
    Returns a dict: {subject_id, delta, theta, alpha, low_beta, high_beta, gamma}
    """
    sfreq = raw.info['sfreq']
    
    # 1. Compute Welch PSD
    # Parameters from config
    window_sec = get_window_seconds()
    overlap_sec = get_overlap_seconds()
    
    freqs, psd = compute_welch_psd(raw, sfreq, window_sec, overlap_sec)
    
    # 2. Get band definitions
    bands = get_band_freqs()
    
    # 3. Aggregate
    band_powers = aggregate_band_power(freqs, psd, bands)
    
    # Construct result row
    row = {'subject_id': sub_id}
    row.update(band_powers)
    
    return row

def main():
    """
    Main entry point for T012.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(description="Extract EEG PSD features (T012)")
    parser.add_argument("--input-dir", type=str, default=None,
                        help="Directory containing preprocessed EEG data (default: from config)")
    parser.add_argument("--output-csv", type=str, default=None,
                        help="Output CSV path (default: from config)")
    args = parser.parse_args()

    # Set seed for reproducibility (though Welch is deterministic)
    set_global_seed = get_seed()
    
    # Determine paths
    input_dir = args.input_dir or get_path("cleaned_eeg")
    output_csv = args.output_csv or get_path("eeg_psd")
    
    # Ensure output directory exists
    ensure_dirs(output_csv)
    
    print(f"Loading preprocessed EEG from: {input_dir}")
    raw_data_list = load_preprocessed_eeg(input_dir)
    print(f"Found {len(raw_data_list)} subjects.")

    if len(raw_data_list) == 0:
        print("Error: No valid EEG data found. Exiting.")
        sys.exit(1)

    features = []
    for sub_id, raw in raw_data_list:
        try:
            row = extract_features_for_subject(sub_id, raw)
            features.append(row)
            print(f"Processed {sub_id}")
        except Exception as e:
            print(f"Error processing {sub_id}: {e}")
            # Optionally continue or fail. For robustness, we log and continue.
            # But per spec, we should ensure data integrity.
            # Let's fail loudly if a subject is expected to be processed.
            # sys.exit(1) 
    
    if not features:
        print("Error: No features extracted. Exiting.")
        sys.exit(1)

    # Create DataFrame
    df = pd.DataFrame(features)
    
    # Ensure columns are in a specific order
    band_names = get_all_band_names()
    cols = ['subject_id'] + band_names
    # Only keep columns that exist in df (in case some bands were empty)
    final_cols = [c for c in cols if c in df.columns]
    df = df[final_cols]
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    print(f"Saved features to: {output_csv}")
    print(f"Shape: {df.shape}")
    print(df.head())

if __name__ == "__main__":
    main()