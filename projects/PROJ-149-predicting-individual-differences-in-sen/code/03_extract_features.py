"""
T012: Compute Welch's PSD on continuous 5-minute epochs.
Input: data/interim/cleaned_eeg_final/ (cleaned .fif files)
Output: data/interim/eeg_psd.csv (raw power values)

Window: 4s, Overlap: 2s.
Bands: delta, theta, alpha, low-beta, high-beta, gamma.

Implements chunked processing for memory efficiency and global mean aggregation.
"""
import os
import sys
import glob
import json
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import mne
from scipy import signal

from config import get_path, ensure_dirs, get_band_freqs, get_window_seconds, get_overlap_seconds

def load_preprocessed_eeg(input_dir: str) -> Dict[str, mne.io.Raw]:
    """Load all cleaned .fif files from the input directory."""
    print(f"Loading preprocessed EEG from: {input_dir}")
    files = glob.glob(os.path.join(input_dir, "*.fif"))
    if not files:
        raise FileNotFoundError(f"No .fif files found in {input_dir}")
    
    subjects = {}
    for f in files:
        subj_id = os.path.splitext(os.path.basename(f))[0]
        try:
            raw = mne.io.read_raw_fif(f, preload=True)
            subjects[subj_id] = raw
        except Exception as e:
            print(f"Warning: Could not load {f}: {e}")
    return subjects

def compute_welch_psd_chunked(raw: mne.io.Raw, window_sec: float, overlap_sec: float) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute Welch's PSD for the entire recording with chunked processing.
    Returns: freqs, psds (channels x freqs)
    """
    data = raw.get_data()
    sfreq = raw.info['sfreq']
    n_channels, n_times = data.shape
    
    n_fft = int(window_sec * sfreq)
    n_overlap = int(overlap_sec * sfreq)
    
    # Initialize storage for PSDs
    # We will compute PSD for each channel separately to manage memory
    all_psds = []
    
    # Process each channel
    for ch_idx in range(n_channels):
        ch_data = data[ch_idx, :]
        
        # Compute PSD for this channel
        freqs, psd = signal.welch(
            ch_data, 
            fs=sfreq, 
            nperseg=n_fft, 
            noverlap=n_overlap
        )
        all_psds.append(psd)
    
    # Stack PSDs: shape (n_channels, n_freqs)
    psds = np.stack(all_psds, axis=0)
    
    return freqs, psds

def aggregate_band_power(freqs: np.ndarray, psds: np.ndarray, bands: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """
    Aggregate PSD into band powers (mean power in band).
    Uses global mean aggregation across channels as per Constitution Principle VI.
    """
    band_powers = {}
    for name, (low, high) in bands.items():
        mask = (freqs >= low) & (freqs <= high)
        if np.sum(mask) == 0:
            band_powers[name] = 0.0
        else:
            # Mean power across frequencies in the band, then average across channels
            band_power = psds[:, mask].mean(axis=1).mean()
            band_powers[name] = float(band_power)
    return band_powers

def extract_features_for_subject(subj_id: str, raw: mne.io.Raw, bands: Dict[str, Tuple[float, float]], window_sec: float, overlap_sec: float) -> Dict:
    """Extract features for a single subject."""
    freqs, psds = compute_welch_psd_chunked(raw, window_sec, overlap_sec)
    band_powers = aggregate_band_power(freqs, psds, bands)
    
    # Add subject ID
    features = {'participant_id': subj_id}
    features.update(band_powers)
    return features

def main():
    parser = argparse.ArgumentParser(description="Extract PSD features from cleaned EEG")
    parser.add_argument("--input", type=str, default=None, help="Input directory for cleaned EEG")
    parser.add_argument("--output", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()
    
    input_dir = args.input if args.input else get_path("interim", "cleaned_eeg_final")
    output_path = args.output if args.output else get_path("interim", "eeg_psd.csv")
    
    ensure_dirs(os.path.dirname(output_path))
    
    bands = get_band_freqs()
    window_sec = get_window_seconds()
    overlap_sec = get_overlap_seconds()
    
    print(f"Using bands: {bands}")
    print(f"Window: {window_sec}s, Overlap: {overlap_sec}s")
    print(f"Input directory: {input_dir}")
    print(f"Output path: {output_path}")
    
    subjects = load_preprocessed_eeg(input_dir)
    all_features = []
    
    for subj_id, raw in subjects.items():
        try:
            feats = extract_features_for_subject(subj_id, raw, bands, window_sec, overlap_sec)
            all_features.append(feats)
        except Exception as e:
            print(f"Error processing {subj_id}: {e}")
            continue
    
    if not all_features:
        print("ERROR: No features extracted.")
        sys.exit(1)
        
    df = pd.DataFrame(all_features)
    df.to_csv(output_path, index=False)
    print(f"Saved features to {output_path}")
    print(f"Processed {len(all_features)} subjects")

if __name__ == "__main__":
    main()