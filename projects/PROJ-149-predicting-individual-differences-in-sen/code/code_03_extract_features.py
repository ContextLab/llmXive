"""
code/code_03_extract_features.py

This is a copy of code/03_extract_features.py to allow imports in tests
without circular dependency issues.
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

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / 'code'))

from config import (
    get_path,
    get_band_freqs,
    get_all_band_names,
    ensure_dirs,
    get_seed
)

# Constants
WINDOW_SECONDS = 4.0
OVERLAP_SECONDS = 2.0
EPOCH_DURATION_SECONDS = 300.0  # 5 minutes
INPUT_DIR = "data/interim/cleaned_eeg"
OUTPUT_FILE = "data/interim/eeg_psd.csv"


def load_preprocessed_eeg(subject_id: str) -> mne.Epochs | mne.io.Raw:
    """
    Load preprocessed EEG data for a specific subject from the cleaned_eeg directory.
    """
    input_path = get_path(INPUT_DIR)
    pattern = os.path.join(input_path, f"*{subject_id}*")
    files = glob.glob(pattern)
    
    if not files:
        raise FileNotFoundError(f"No preprocessed data found for subject {subject_id} in {input_path}")
    
    files.sort()
    raw = mne.io.read_raw_fif(files[0], preload=True)
    
    for f in files[1:]:
        raw_other = mne.io.read_raw_fif(f, preload=True)
        raw = raw.append(raw_other)
        
    return raw


def compute_welch_psd(raw: mne.io.Raw, window_sec: float, overlap_sec: float):
    """
    Compute Welch's PSD on continuous data.
    """
    sfreq = raw.info['sfreq']
    n_fft = int(window_sec * sfreq)
    n_overlap = int(overlap_sec * sfreq)
    
    psd, freqs = mne.time_frequency.psd_welch(
        raw,
        fmin=0,
        fmax=100,
        n_fft=n_fft,
        n_overlap=n_overlap,
        n_jobs=1,
        verbose=False
    )
    
    return freqs, psd


def aggregate_band_power(freqs: np.ndarray, psd: np.ndarray, raw: mne.io.Raw) -> dict:
    """
    Aggregate power into standard frequency bands.
    """
    band_freqs = get_band_freqs()
    
    default_bands = {
        'delta': (1, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'low_beta': (13, 20),
        'high_beta': (20, 30),
        'gamma': (30, 45)
    }
    
    bands_to_use = {**default_bands, **band_freqs}
    
    results = {}
    psd = np.array(psd)  # Ensure numpy array
    
    for band_name, (f_min, f_max) in bands_to_use.items():
        mask = (freqs >= f_min) & (freqs < f_max)
        if not np.any(mask):
            results[band_name] = 0.0
            continue
        
        band_psd = psd[:, mask]
        mean_power = np.mean(band_psd)
        results[band_name] = float(mean_power)
        
    return results


def extract_features_for_subject(subject_id: str, raw: mne.io.Raw, window_sec: float, overlap_sec: float) -> dict:
    """
    Extract all features for a single subject.
    """
    freqs, psd = compute_welch_psd(raw, window_sec, overlap_sec)
    band_powers = aggregate_band_power(freqs, psd, raw)
    
    row = {'participant_id': subject_id}
    row.update(band_powers)
    
    return row


def main():
    """
    Main entry point for feature extraction.
    """
    parser = argparse.ArgumentParser(description="Extract EEG band-power features from preprocessed data.")
    parser.add_argument('--window-seconds', type=float, default=WINDOW_SECONDS)
    parser.add_argument('--overlap-seconds', type=float, default=OVERLAP_SECONDS)
    parser.add_argument('--input-dir', type=str, default=INPUT_DIR)
    parser.add_argument('--output-file', type=str, default=OUTPUT_FILE)
    args = parser.parse_args()
    
    set_seed = get_seed()
    if set_seed is not None:
        np.random.seed(set_seed)
    
    input_path = get_path(args.input_dir)
    output_path = get_path(args.output_file)
    
    ensure_dirs(output_path)
    
    subjects = []
    if os.path.isdir(input_path):
        sub_dirs = [d for d in os.listdir(input_path) if d.startswith('sub-')]
        if sub_dirs:
            subjects = sub_dirs
        else:
            fif_files = glob.glob(os.path.join(input_path, 'sub-*.fif'))
            subjects = [os.path.basename(f).replace('_raw.fif', '').replace('_cleaned.fif', '') for f in fif_files]
    else:
        raise FileNotFoundError(f"Input directory not found: {input_path}")
    
    if not subjects:
        raise ValueError(f"No subjects found in {input_path}")
    
    print(f"Found {len(subjects)} subjects to process.")
    
    all_rows = []
    
    for sub in subjects:
        try:
            print(f"Processing subject: {sub}")
            raw = load_preprocessed_eeg(sub)
            row = extract_features_for_subject(sub, raw, args.window_seconds, args.overlap_seconds)
            all_rows.append(row)
        except Exception as e:
            print(f"Error processing subject {sub}: {e}")
            continue
    
    if not all_rows:
        raise RuntimeError("No features extracted. Check input data and error logs.")
    
    df = pd.DataFrame(all_rows)
    
    power_cols = [col for col in df.columns if col != 'participant_id']
    if df[power_cols].isnull().any().any():
        print("Warning: Null values found in power columns. Dropping rows with nulls.")
        df = df.dropna(subset=power_cols)
    
    df = df.sort_values('participant_id').reset_index(drop=True)
    df.to_csv(output_path, index=False)
    print(f"Features written to {output_path}")
    print(f"Total subjects processed: {len(df)}")
    
    return df


if __name__ == '__main__':
    main()