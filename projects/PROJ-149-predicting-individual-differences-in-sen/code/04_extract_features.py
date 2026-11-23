"""
Task T012: Extract EEG Band-Power Features from Preprocessed Data.

Implements FR-003 and FR-010.
- Computes Welch's PSD on continuous multi-minute epochs.
- Uses 2-second windows with 50% overlap (per Constitution Principle VI).
- Aggregates power into canonical bands: delta, theta, alpha, low-beta, high-beta, gamma.
- Calculates relative power (band / total 1-40 Hz power).
- Output: data/processed/features.csv
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

# Import shared config and utils
from config import (
    get_path,
    ensure_dirs,
    get_band_freqs,
    get_all_band_names,
    get_window_seconds,
    get_overlap_seconds,
    get_epsilon,
    get_seed
)
from utils.eeg_helpers import bandpass_filter, notch_filter

# Set global seed for reproducibility
from config import set_global_seed
set_global_seed()


def load_exclusion_log(log_path: str) -> pd.DataFrame:
    """Load the exclusion log from preprocessing."""
    if not os.path.exists(log_path):
        return pd.DataFrame(columns=['participant_id', 'reason', 'channels_rejected_ratio'])
    return pd.read_csv(log_path)


def load_preprocessed_eeg(input_dir: str) -> Dict[str, mne.io.Raw]:
    """
    Load preprocessed EEG raw files from the specified directory.
    Returns a dictionary mapping participant_id to mne.io.Raw object.
    """
    eeg_files = glob.glob(os.path.join(input_dir, "*.fif"))
    if not eeg_files:
        # Fallback to interim/preprocessed_eeg if input_dir is relative or generic
        eeg_files = glob.glob(os.path.join(get_path("interim", "preprocessed_eeg"), "*.fif"))
    
    participants = {}
    for f_path in eeg_files:
        try:
            raw = mne.io.read_raw_fif(f_path, preload=True)
            # Extract ID from filename (e.g., sub-001_ses-01_task-rest.fif -> 001)
            basename = os.path.basename(f_path)
            # Handle various naming conventions
            if basename.startswith("sub-"):
                pid = basename.split("_")[0].replace("sub-", "")
            else:
                pid = os.path.splitext(basename)[0]
            participants[pid] = raw
        except Exception as e:
            print(f"Warning: Could not load {f_path}: {e}")
    return participants


def load_behavioral_metrics(metrics_path: str) -> pd.DataFrame:
    """
    Load behavioral metrics (median RT) for participants.
    """
    if not os.path.exists(metrics_path):
        # Try alternative path
        alt_path = os.path.join(get_path("interim"), "behavioral_metrics.csv")
        if os.path.exists(alt_path):
            metrics_path = alt_path
        else:
            raise FileNotFoundError(f"Behavioral metrics file not found at {metrics_path} or {alt_path}")
    
    df = pd.read_csv(metrics_path)
    if 'participant_id' not in df.columns:
        # Sometimes column is named 'subject_id' or similar
        if 'subject_id' in df.columns:
            df.rename(columns={'subject_id': 'participant_id'}, inplace=True)
        else:
            raise ValueError("Behavioral metrics file must contain 'participant_id' column")
    return df


def compute_welch_psd_chunked(raw: mne.io.Raw, sfreq: float, window_sec: float, overlap_sec: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Welch's PSD on the continuous data using specified window and overlap.
    Returns (frequencies, psd_matrix) where psd_matrix is (n_channels, n_freqs).
    """
    # Get data and times
    data = raw.get_data()  # (n_channels, n_times)
    n_channels, n_times = data.shape
    
    # Convert seconds to samples
    window_samples = int(window_sec * sfreq)
    overlap_samples = int(overlap_sec * sfreq)
    step_samples = window_samples - overlap_samples
    
    if step_samples <= 0:
        raise ValueError("Overlap cannot be >= window size")
    
    # Collect PSDs for each segment
    all_psd_segments = []
    
    for start in range(0, n_times - window_samples + 1, step_samples):
        end = start + window_samples
        segment = data[:, start:end]
        
        # Compute PSD for this segment using scipy.signal.welch
        # We need to average across segments later, but welch expects 1D or 2D (n_channels, n_times)
        # scipy.signal.welch works on 2D input (n_channels, n_times) if axis=-1
        try:
            from scipy.signal import welch
            # Calculate PSD for this segment
            # nperseg must be <= segment length
            nperseg = min(window_samples, segment.shape[1])
            f, Pxx = welch(segment, fs=sfreq, nperseg=nperseg, axis=-1, average='mean')
            # Pxx shape: (n_channels, n_freqs)
            all_psd_segments.append(Pxx)
        except Exception as e:
            print(f"Warning: PSD calculation failed for segment at {start}: {e}")
            continue
    
    if not all_psd_segments:
        # Fallback if no segments were valid: compute on whole data if long enough
        if n_times >= window_samples:
            from scipy.signal import welch
            f, Pxx = welch(data, fs=sfreq, nperseg=window_samples, axis=-1, average='mean')
            return f, Pxx
        else:
            raise ValueError("Data too short to compute PSD with given window size")
    
    # Average PSD across all valid segments
    psd_matrix = np.mean(np.stack(all_psd_segments, axis=0), axis=0)
    return f, psd_matrix


def aggregate_band_power(frequencies: np.ndarray, psd_matrix: np.ndarray, bands: Dict[str, Tuple[float, float]]) -> Dict[str, np.ndarray]:
    """
    Aggregate PSD into canonical frequency bands.
    Returns a dict mapping band_name to array of mean power per channel.
    """
    band_powers = {}
    for band_name, (low, high) in bands.items():
        mask = (frequencies >= low) & (frequencies < high)
        if np.sum(mask) == 0:
            print(f"Warning: No frequencies found for band {band_name} ({low}-{high} Hz)")
            band_powers[band_name] = np.zeros(psd_matrix.shape[0])
        else:
            # Mean power in band for each channel
            band_powers[band_name] = np.mean(psd_matrix[:, mask], axis=1)
    return band_powers


def compute_relative_power(band_powers: Dict[str, np.ndarray], total_band: str = None) -> Dict[str, np.ndarray]:
    """
    Compute relative power for each band.
    Relative Power = Band Power / Total Power (1-40 Hz).
    If total_band is None, sum of all bands is used.
    """
    # Calculate total power (sum of all bands)
    if total_band is None:
        total_power = np.sum(list(band_powers.values()), axis=0)
    else:
        total_power = band_powers.get(total_band, np.sum(list(band_powers.values()), axis=0))
    
    epsilon = get_epsilon()
    relative_powers = {}
    for band_name, power in band_powers.items():
        relative_powers[band_name] = power / (total_power + epsilon)
    return relative_powers


def extract_features_for_subject(participant_id: str, raw: mne.io.Raw, median_rt: float, bands: Dict[str, Tuple[float, float]]) -> Optional[Dict]:
    """
    Extract all features for a single subject.
    """
    sfreq = raw.info['sfreq']
    window_sec = get_window_seconds()
    overlap_sec = get_overlap_seconds()
    
    try:
        # Compute PSD
        frequencies, psd_matrix = compute_welch_psd_chunked(raw, sfreq, window_sec, overlap_sec)
        
        # Aggregate band powers
        band_powers = aggregate_band_power(frequencies, psd_matrix, bands)
        
        # Compute relative powers
        relative_powers = compute_relative_power(band_powers)
        
        # Construct feature record
        record = {
            'participant_id': participant_id,
            'median_rt': median_rt
        }
        for band_name in get_all_band_names():
            if band_name in relative_powers:
                record[f'{band_name}_rel'] = float(relative_powers[band_name].mean()) # Average across channels
            else:
                record[f'{band_name}_rel'] = 0.0
        
        return record
    except Exception as e:
        print(f"Error extracting features for {participant_id}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Extract EEG band-power features.")
    parser.add_argument('--preprocessed-dir', type=str, default=None, help="Directory containing preprocessed .fif files")
    parser.add_argument('--behavioral-path', type=str, default=None, help="Path to behavioral metrics CSV")
    parser.add_argument('--exclusion-log', type=str, default=None, help="Path to exclusion log CSV")
    parser.add_argument('--output-dir', type=str, default=None, help="Directory for output CSV")
    args = parser.parse_args()
    
    # Determine paths
    preprocessed_dir = args.preprocessed_dir or get_path("interim", "ica_cleaned_eeg")
    behavioral_path = args.behavioral_path or get_path("interim", "behavioral_metrics.csv")
    exclusion_log_path = args.exclusion_log or get_path("interim", "exclusion_log.csv")
    output_dir = args.output_dir or get_path("processed")
    
    # Ensure output directory exists
    ensure_dirs(output_dir)
    output_file = os.path.join(output_dir, "features.csv")
    
    print(f"Loading preprocessed EEG from: {preprocessed_dir}")
    print(f"Loading behavioral metrics from: {behavioral_path}")
    print(f"Loading exclusion log from: {exclusion_log_path}")
    
    # Load data
    eeg_data = load_preprocessed_eeg(preprocessed_dir)
    if not eeg_data:
        print("Error: No preprocessed EEG data found.")
        sys.exit(1)
        
    behavioral_df = load_behavioral_metrics(behavioral_path)
    exclusion_df = load_exclusion_log(exclusion_log_path)
    
    # Create a set of excluded IDs
    excluded_ids = set(exclusion_df['participant_id'].astype(str)) if 'participant_id' in exclusion_df.columns else set()
    
    # Get band definitions
    bands = get_band_freqs()
    
    # Merge behavioral data
    behavioral_dict = behavioral_df.set_index('participant_id')['median_rt'].to_dict()
    
    # Extract features
    features_list = []
    for pid, raw in eeg_data.items():
        if pid in excluded_ids:
            print(f"Skipping excluded participant: {pid}")
            continue
        
        if pid not in behavioral_dict:
            print(f"Warning: No behavioral data for participant {pid}, skipping.")
            continue
        
        median_rt = behavioral_dict[pid]
        record = extract_features_for_subject(pid, raw, median_rt, bands)
        if record:
            features_list.append(record)
    
    if not features_list:
        print("Warning: No features extracted. Check data availability.")
        # Create empty file with headers
        df = pd.DataFrame(columns=['participant_id', 'median_rt'] + [f'{b}_rel' for b in get_all_band_names()])
    else:
        df = pd.DataFrame(features_list)
    
    # Save
    df.to_csv(output_file, index=False)
    print(f"Features saved to: {output_file}")
    print(f"Extracted {len(df)} participant records.")
    
    # Verify output exists
    if not os.path.exists(output_file):
        print("Error: Output file was not created.")
        sys.exit(1)


if __name__ == "__main__":
    main()