"""
T026c: Re-run feature extraction on robustness data (No-ICA and 2s-window).
Input: 
  - data/interim/robustness/no_ica/cleaned_eeg/ (cleaned .fif files without ICA)
  - data/interim/robustness/window_2s/cleaned_eeg/ (cleaned .fif files with 2s windows)
Output:
  - data/interim/robustness/no_ica/features.csv
  - data/interim/robustness/window_2s/features.csv

Logic:
  1. Load preprocessed EEG from robustness directories.
  2. Compute Welch's PSD (using specific window sizes if needed, though 2s window is usually handled in preprocessing, here we ensure consistency).
  3. Aggregate band powers.
  4. Calculate relative power (band/total).
  5. Apply Centered Log-Ratio (CLR) transformation with epsilon handling.
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

# Import from config to ensure consistency
from config import get_path, ensure_dirs, get_band_freqs, get_window_seconds, get_overlap_seconds

def load_preprocessed_eeg(input_dir: str) -> Dict[str, mne.io.Raw]:
    """Load all cleaned .fif files from the input directory."""
    print(f"Loading preprocessed EEG from: {input_dir}")
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Robustness input directory not found: {input_dir}")
    
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

def compute_relative_power_and_clr(band_powers: Dict[str, float], epsilon: float = 1e-6) -> Dict[str, float]:
    """
    Calculate relative power (band/total) and apply Centered Log-Ratio (CLR) transformation.
    """
    total_power = sum(band_powers.values())
    if total_power == 0:
        # Fallback if total is zero (should not happen with real data + epsilon)
        relative_powers = {k: epsilon for k in band_powers}
    else:
        relative_powers = {k: v / total_power for k, v in band_powers.items()}
    
    # Add epsilon to avoid log(0)
    adjusted_powers = {k: v + epsilon for k, v in relative_powers.items()}
    
    # CLR Transformation: log(x_i / geometric_mean)
    log_powers = {k: np.log(v) for k, v in adjusted_powers.items()}
    mean_log = np.mean(list(log_powers.values()))
    
    clr_powers = {k: v - mean_log for k, v in log_powers.items()}
    
    return clr_powers

def extract_features_for_subject(subj_id: str, raw: mne.io.Raw, bands: Dict[str, Tuple[float, float]], window_sec: float, overlap_sec: float) -> Dict:
    """Extract features for a single subject, including relative power and CLR."""
    freqs, psds = compute_welch_psd_chunked(raw, window_sec, overlap_sec)
    raw_band_powers = aggregate_band_power(freqs, psds, bands)
    
    # Apply relative power and CLR
    final_features = compute_relative_power_and_clr(raw_band_powers)
    
    # Add subject ID
    features = {'participant_id': subj_id}
    features.update(final_features)
    return features

def run_robustness_extraction(config_name: str, input_subdir: str, window_sec_override: Optional[float] = None):
    """
    Run the feature extraction pipeline for a specific robustness configuration.
    
    Args:
        config_name: Name of the config (e.g., 'no_ica', 'window_2s')
        input_subdir: Subdirectory under robustness for input data
        window_sec_override: Optional override for window size (for 2s window robustness)
    """
    # Determine paths
    base_robustness_dir = get_path("interim", "robustness")
    input_dir = os.path.join(base_robustness_dir, input_subdir, "cleaned_eeg")
    output_dir = os.path.join(base_robustness_dir, input_subdir)
    output_path = os.path.join(output_dir, "features.csv")
    
    print(f"--- Processing Robustness Config: {config_name} ---")
    print(f"Input: {input_dir}")
    print(f"Output: {output_path}")
    
    ensure_dirs(output_dir)
    
    bands = get_band_freqs()
    
    # Use default window/overlap unless overridden
    window_sec = window_sec_override if window_sec_override is not None else get_window_seconds()
    overlap_sec = get_overlap_seconds()
    
    # If window is 2s, adjust overlap to 1s (50% overlap) if not specified, 
    # but usually overlap is 50% of window. Let's stick to config defaults unless forced.
    # The task says "Re-run ... with --window-size 2". 
    # If the config has 4s window, we override.
    
    print(f"Using bands: {bands}")
    print(f"Window: {window_sec}s, Overlap: {overlap_sec}s")
    
    try:
        subjects = load_preprocessed_eeg(input_dir)
    except FileNotFoundError as e:
        print(f"Skipping {config_name}: {e}")
        return

    all_features = []
    
    for subj_id, raw in subjects.items():
        try:
            feats = extract_features_for_subject(subj_id, raw, bands, window_sec, overlap_sec)
            all_features.append(feats)
        except Exception as e:
            print(f"Error processing {subj_id} in {config_name}: {e}")
            continue
    
    if not all_features:
        print(f"ERROR: No features extracted for {config_name}.")
        # We do not exit(1) here because robustness might have partial success, 
        # but for T026c we expect valid data if T026a/b succeeded.
        return
        
    df = pd.DataFrame(all_features)
    df.to_csv(output_path, index=False)
    print(f"Saved robustness features to {output_path}")
    print(f"Processed {len(all_features)} subjects for {config_name}")

def main():
    parser = argparse.ArgumentParser(description="Extract features for Robustness Analysis (T026c)")
    parser.add_argument("--no-ica", action="store_true", help="Process No-ICA robustness data")
    parser.add_argument("--window-2s", action="store_true", help="Process 2-second window robustness data")
    parser.add_argument("--all", action="store_true", help="Process all robustness data")
    args = parser.parse_args()
    
    if not (args.no_ica or args.window_2s or args.all):
        print("Error: Must specify --no-ica, --window-2s, or --all")
        sys.exit(1)
    
    # Process No-ICA
    if args.no_ica or args.all:
        run_robustness_extraction(
            config_name="no_ica",
            input_subdir="no_ica",
            window_sec_override=None # Uses config default (4s)
        )
    
    # Process Window-2s
    if args.window_2s or args.all:
        run_robustness_extraction(
            config_name="window_2s",
            input_subdir="window_2s",
            window_sec_override=2.0 # Override to 2 seconds as per task
        )

if __name__ == "__main__":
    main()