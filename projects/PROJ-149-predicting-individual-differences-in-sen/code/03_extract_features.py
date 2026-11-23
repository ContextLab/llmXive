"""
T012 [US1] Implement code/03_extract_features.py:
Compute Welch's PSD on continuous 5-minute epochs using 4-second windows with overlap from config.
Aggregate power into delta, theta, alpha, low-beta, high-beta, and gamma bands.
Calculate relative power and apply CLR transformation.
Input: data/interim/exclusion_log.csv, data/interim/cleaned_eeg_final/, data/interim/behavioral_metrics.csv
Output: data/processed/features_clr.csv
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
from typing import Dict, List, Tuple, Optional
from scipy import signal
from config import (
    get_path, ensure_dirs, get_epsilon, get_band_freqs, get_all_band_names,
    get_window_seconds, get_overlap_seconds, get_min_epoch_duration_minutes
)

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def load_exclusion_log() -> pd.DataFrame:
    """Load exclusion log and return excluded participant IDs."""
    exclusion_log_path = get_path("interim", "exclusion_log.csv")
    if not os.path.exists(exclusion_log_path):
        raise FileNotFoundError(
            "Exclusion log missing. Ensure T010c completed successfully."
        )
    df = pd.read_csv(exclusion_log_path)
    return set(df['participant_id'].tolist())

def load_preprocessed_eeg(input_dir: str) -> Dict[str, mne.io.Raw]:
    """Load all cleaned EEG files from the input directory."""
    eeg_files = glob.glob(os.path.join(input_dir, "*.fif"))
    if not eeg_files:
        raise FileNotFoundError(f"No .fif files found in {input_dir}")

    subjects = {}
    for fpath in eeg_files:
        try:
            raw = mne.io.read_raw_fif(fpath, preload=True)
            # Extract subject ID from filename or info
            subj_id = Path(fpath).stem.split('_')[0] if '_' in Path(fpath).stem else Path(fpath).stem
            subjects[subj_id] = raw
        except Exception as e:
            print(f"Warning: Could not load {fpath}: {e}")
            continue
    return subjects

def load_behavioral_metrics() -> pd.DataFrame:
    """Load behavioral metrics from T013."""
    b_path = get_path("interim", "behavioral_metrics.csv")
    if not os.path.exists(b_path):
        raise FileNotFoundError(f"Behavioral metrics file missing at {b_path}")
    return pd.read_csv(b_path)

def compute_welch_psd_chunked(raw: mne.io.Raw, window_sec: float, overlap_sec: float,
                              freqs: np.ndarray, n_fft: int = None) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Welch's PSD on continuous data in chunks to manage memory.
    Returns (freqs, psd_matrix, n_segments_used).
    """
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    n_channels, n_samples = data.shape

    if n_fft is None:
        n_fft = int(window_sec * sfreq)

    # Ensure n_fft does not exceed window size
    n_fft = min(n_fft, n_samples)

    # Overlap in samples
    noverlap = int(overlap_sec * sfreq)
    noverlap = min(noverlap, n_fft // 2)  # Standard max overlap

    # Chunk size for processing (e.g., 5 minutes of data at a time)
    chunk_duration = 300.0  # 5 minutes
    chunk_size = int(chunk_duration * sfreq)

    all_psd = []
    n_segments_total = 0

    for start in range(0, n_samples, chunk_size):
        end = min(start + chunk_size, n_samples)
        chunk_data = data[:, start:end]

        if chunk_data.shape[1] < n_fft:
            continue

        freqs_chunk, psd_chunk = signal.welch(
            chunk_data,
            fs=sfreq,
            nperseg=n_fft,
            noverlap=noverlap,
            nfft=n_fft,
            axis=-1,
            scaling='density',
            average='mean'
        )

        all_psd.append(psd_chunk)
        n_segments_total += psd_chunk.shape[-1]

    if not all_psd:
        # Fallback if no chunks were valid (shouldn't happen with valid data)
        freqs_chunk, psd_chunk = signal.welch(
            data, fs=sfreq, nperseg=n_fft, noverlap=noverlap, nfft=n_fft, axis=-1
        )
        return freqs_chunk, psd_chunk, 1

    psd_matrix = np.concatenate(all_psd, axis=-1)
    return freqs_chunk, psd_matrix, n_segments_total

def aggregate_band_power(freqs: np.ndarray, psd: np.ndarray, bands: Dict[str, Tuple[float, float]]) -> Dict[str, np.ndarray]:
    """
    Aggregate PSD into band powers (absolute).
    psd shape: (n_channels, n_freqs, n_segments)
    Returns dict of band_name -> mean_power_per_channel (n_channels,)
    """
    band_powers = {}
    for name, (f_min, f_max) in bands.items():
        mask = (freqs >= f_min) & (freqs < f_max)
        if not np.any(mask):
            band_powers[name] = np.zeros(psd.shape[0])
            continue
        # Mean power across frequency band and segments
        band_powers[name] = np.mean(psd[:, mask, :], axis=(1, 2))
    return band_powers

def compute_relative_power(band_powers: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """Compute relative power for each band."""
    total_power = np.sum(list(band_powers.values()), axis=0)
    # Add epsilon to avoid division by zero
    total_power = total_power + get_epsilon()
    rel_powers = {}
    for name, power in band_powers.items():
        rel_powers[name] = power / total_power
    return rel_powers

def compute_clr_transformation(rel_powers: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
    """
    Apply Centered Log-Ratio (CLR) transformation.
    CLR(x)_i = log(x_i / g(x)) where g(x) is the geometric mean.
    x_i + epsilon to avoid log(0).
    """
    eps = get_epsilon()
    bands = list(rel_powers.keys())
    n_channels = len(list(rel_powers.values())[0])
    n_bands = len(bands)

    # Stack into matrix (n_channels, n_bands)
    data_matrix = np.column_stack([rel_powers[b] for b in bands]) + eps

    # Geometric mean across bands for each channel
    geom_mean = np.exp(np.mean(np.log(data_matrix), axis=1, keepdims=True))

    # CLR
    clr_data = np.log(data_matrix / geom_mean)

    return {b: clr_data[:, i] for i, b in enumerate(bands)}

def extract_features_for_subject(
    subj_id: str,
    raw: mne.io.Raw,
    behavioral_df: pd.DataFrame,
    window_sec: float,
    overlap_sec: float,
    bands: Dict[str, Tuple[float, float]]
) -> Optional[Dict]:
    """Extract all features for a single subject."""
    # Check minimum duration
    duration_min = raw.times[-1] / 60.0
    min_dur = get_min_epoch_duration_minutes()
    if duration_min < min_dur:
        print(f"Skipping {subj_id}: duration {duration_min:.2f} min < {min_dur} min")
        return None

    # Compute PSD
    freqs, psd_matrix, _ = compute_welch_psd_chunked(raw, window_sec, overlap_sec, None)

    # Aggregate bands
    abs_powers = aggregate_band_power(freqs, psd_matrix, bands)

    # Relative power
    rel_powers = compute_relative_power(abs_powers)

    # CLR
    clr_powers = compute_clr_transformation(rel_powers)

    # Get behavioral metric
    rt_val = behavioral_df[behavioral_df['participant_id'] == subj_id]['median_rt'].values
    if len(rt_val) == 0:
        print(f"Warning: No RT found for {subj_id}")
        rt_val = np.nan
    else:
        rt_val = rt_val[0]

    row = {'participant_id': subj_id, 'median_rt': rt_val}
    for band, values in clr_powers.items():
        # Average across channels to get one value per band per subject
        row[f'clr_{band}'] = np.mean(values)

    return row

def main():
    print("Starting T012: Feature Extraction with CLR Transformation")

    # 1. Validate Config
    try:
        overlap = get_overlap_seconds()
    except ValueError as e:
        print(f"Config Error: {e}")
        sys.exit(1)

    window = get_window_seconds()
    bands = get_band_freqs()
    all_bands = get_all_band_names()

    print(f"Using window={window}s, overlap={overlap}s")
    print(f"Bands: {all_bands}")

    # 2. Load Exclusion Log
    excluded_ids = load_exclusion_log()
    print(f"Excluded participants: {len(excluded_ids)}")

    # 3. Load Preprocessed EEG
    eeg_dir = get_path("interim", "cleaned_eeg_final")
    subjects_eeg = load_preprocessed_eeg(eeg_dir)
    print(f"Loaded EEG for {len(subjects_eeg)} subjects")

    # 4. Load Behavioral Metrics
    behavioral_df = load_behavioral_metrics()

    # 5. Process Subjects
    features_list = []
    for subj_id, raw in subjects_eeg.items():
        if subj_id in excluded_ids:
            continue
        try:
            row = extract_features_for_subject(
                subj_id, raw, behavioral_df, window, overlap, bands
            )
            if row:
                features_list.append(row)
        except Exception as e:
            print(f"Error processing {subj_id}: {e}")
            continue

    if not features_list:
        print("No features extracted. Exiting.")
        sys.exit(1)

    df_features = pd.DataFrame(features_list)

    # 6. Validate Output Schema
    required_cols = ['participant_id', 'median_rt'] + [f'clr_{b}' for b in all_bands]
    missing_cols = [c for c in required_cols if c not in df_features.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in output: {missing_cols}")

    # 7. Save Output
    output_path = get_path("processed", "features_clr.csv")
    ensure_dirs(output_path)
    df_features.to_csv(output_path, index=False)
    print(f"Features saved to {output_path}")

    # 8. Sanity Check
    if df_features['median_rt'].isnull().any():
        print("Warning: Some RT values are null.")
    if df_features[[c for c in df_features.columns if c.startswith('clr_')]].isnull().any().any():
        print("Warning: Some CLR values are null.")

    print("T012 completed successfully.")

if __name__ == "__main__":
    main()
