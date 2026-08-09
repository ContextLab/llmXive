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

# Import from project config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))
from config import get_path, ensure_dirs, get_band_freqs, get_all_band_names, get_seed
from utils.eeg_helpers import bandpass_filter, notch_filter, reject_channels_by_variance, apply_ica

def load_preprocessed_eeg(subject_id: str) -> Optional[mne.io.Raw]:
    """
    Load preprocessed EEG data for a specific subject from data/interim/cleaned_eeg.
    
    Args:
        subject_id: The subject identifier (e.g., 'sub-001')
        
    Returns:
        mne.io.Raw object or None if not found
    """
    # Construct path to the cleaned data directory
    cleaned_dir = get_path("interim", "cleaned_eeg")
    if not os.path.exists(cleaned_dir):
        print(f"Error: Cleaned EEG directory not found at {cleaned_dir}")
        return None
    
    # Search for files matching the subject ID
    pattern = os.path.join(cleaned_dir, f"*{subject_id}*")
    files = glob.glob(pattern)
    
    if not files:
        print(f"Warning: No preprocessed files found for subject {subject_id}")
        return None
    
    # Load the first matching file (typically .fif or .edf)
    # We assume the preprocessing step saved in MNE format (.fif)
    file_path = None
    for f in files:
        if f.endswith('.fif') or f.endswith('.edf'):
            file_path = f
            break
    
    if not file_path:
        print(f"Warning: No valid EEG file found for subject {subject_id} in {files}")
        return None
        
    try:
        raw = mne.io.read_raw_fif(file_path, preload=True)
        return raw
    except Exception as e:
        # Try EDf if FIF failed
        try:
            raw = mne.io.read_raw_edf(file_path, preload=True)
            return raw
        except Exception as e2:
            print(f"Error loading EEG file {file_path}: {e2}")
            return None

def compute_welch_psd(raw: mne.io.Raw, window_size: int = 4, overlap: int = 2) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute Welch's Power Spectral Density for continuous 5-minute epochs.
    
    Args:
        raw: Preprocessed MNE Raw object
        window_size: Window size in seconds (default 4)
        overlap: Overlap in seconds (default 2, from config.OVERLAP_SECONDS)
        
    Returns:
        Tuple of (frequencies, psd_array, channel_names)
    """
    # Get sampling frequency
    sfreq = raw.info['sfreq']
    
    # Calculate window and overlap in samples
    window_samples = int(window_size * sfreq)
    overlap_samples = int(overlap * sfreq)
    
    # Ensure we have enough data (at least 5 minutes = 300 seconds)
    total_samples = raw.n_times
    duration = total_samples / sfreq
    
    if duration < 300:
        print(f"Warning: Recording duration ({duration:.2f}s) is less than 5 minutes. Proceeding with available data.")
    
    # Extract data for all channels
    data = raw.get_data()  # Shape: (n_channels, n_times)
    channel_names = raw.ch_names
    
    # Compute PSD using Welch's method
    # nperseg: window length in samples
    # noverlap: number of samples of overlap
    # axis: compute along time axis (axis=1)
    try:
        freqs, psd = mne.time_frequency.psd_welch(
            raw, 
            fmin=0.5, 
            fmax=45.0,  # Cover up to gamma band
            n_per_seg=window_samples,
            n_overlap=overlap_samples,
            average='mean',
            verbose=False
        )
        return freqs, psd, channel_names
    except Exception as e:
        print(f"Error computing Welch PSD: {e}")
        # Fallback to scipy if MNE fails
        from scipy import signal
        # Reshape data for scipy: (n_channels, n_times)
        psd_list = []
        for i in range(data.shape[0]):
            f, pxx = signal.welch(
                data[i], 
                fs=sfreq, 
                nperseg=window_samples, 
                noverlap=overlap_samples,
                scaling='density'
            )
            psd_list.append(pxx)
        psd_array = np.array(psd_list)
        return f, psd_array, channel_names

def aggregate_band_power(freqs: np.ndarray, psd: np.ndarray, channel_names: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Aggregate PSD into standard frequency bands (delta, theta, alpha, low-beta, high-beta, gamma).
    
    Args:
        freqs: Frequency array from Welch's method
        psd: Power spectral density array (n_channels, n_freqs)
        channel_names: List of channel names
        
    Returns:
        Dictionary mapping subject/channel to band powers
    """
    band_defs = get_band_freqs()
    all_bands = get_all_band_names()
    
    results = {}
    
    for i, ch_name in enumerate(channel_names):
        ch_data = psd[i]
        ch_powers = {}
        
        for band_name in all_bands:
            if band_name in band_defs:
                f_min, f_max = band_defs[band_name]
                # Find indices for this frequency range
                mask = (freqs >= f_min) & (freqs < f_max)
                if np.any(mask):
                    # Mean power in this band
                    ch_powers[band_name] = float(np.mean(ch_data[mask]))
                else:
                    ch_powers[band_name] = 0.0
            
        results[ch_name] = ch_powers
        
    return results

def extract_features_for_subject(subject_id: str, window_size: int = 4, overlap: int = 2) -> Optional[pd.DataFrame]:
    """
    Extract all features (band powers) for a single subject.
    
    Args:
        subject_id: Subject identifier
        window_size: Window size in seconds
        overlap: Overlap in seconds
        
    Returns:
        DataFrame with one row per channel, or None if processing fails
    """
    # Load preprocessed data
    raw = load_preprocessed_eeg(subject_id)
    if raw is None:
        return None
    
    # Compute PSD
    freqs, psd, channel_names = compute_welch_psd(raw, window_size, overlap)
    if freqs is None or psd is None:
        return None
    
    # Aggregate band powers
    band_powers = aggregate_band_power(freqs, psd, channel_names)
    
    # Convert to DataFrame
    rows = []
    for ch_name, powers in band_powers.items():
        row = {
            'participant_id': subject_id,
            'channel': ch_name
        }
        row.update(powers)
        rows.append(row)
    
    df = pd.DataFrame(rows)
    return df

def main():
    """
    Main entry point for feature extraction.
    Processes all subjects in data/interim/cleaned_eeg and outputs to data/interim/eeg_psd.csv
    """
    parser = argparse.ArgumentParser(description='Extract EEG band-power features from preprocessed data.')
    parser.add_argument('--window-size', type=int, default=4, help='Window size in seconds (default: 4)')
    parser.add_argument('--overlap', type=int, default=2, help='Overlap in seconds (default: 2)')
    parser.add_argument('--subjects', type=str, nargs='+', help='Specific subject IDs to process (optional)')
    args = parser.parse_args()
    
    # Set global seed for reproducibility
    seed = get_seed()
    np.random.seed(seed)
    
    # Define paths
    cleaned_dir = get_path("interim", "cleaned_eeg")
    output_file = get_path("interim", "eeg_psd.csv")
    
    print(f"Starting feature extraction...")
    print(f"Input directory: {cleaned_dir}")
    print(f"Output file: {output_file}")
    print(f"Window size: {args.window_size}s, Overlap: {args.overlap}s")
    
    # Ensure output directory exists
    ensure_dirs(output_file)
    
    # Find all subjects to process
    if args.subjects:
        subjects_to_process = args.subjects
    else:
        # Scan directory for subjects
        subjects_to_process = []
        if os.path.exists(cleaned_dir):
            for item in os.listdir(cleaned_dir):
                item_path = os.path.join(cleaned_dir, item)
                if os.path.isdir(item_path) or item.endswith(('.fif', '.edf')):
                    # Extract subject ID from folder/file name
                    # Assume format: sub-XXX or similar
                    parts = item.replace('sub-', '').replace('.fif', '').replace('.edf', '').split('_')
                    if parts[0].isdigit() or (parts[0].startswith('0') and parts[0][1:].isdigit()):
                        subjects_to_process.append(f"sub-{parts[0]}")
                    elif len(parts) > 0:
                        subjects_to_process.append(f"sub-{parts[0]}")
        
        # Remove duplicates
        subjects_to_process = list(set(subjects_to_process))
    
    if not subjects_to_process:
        print("Error: No subjects found to process.")
        sys.exit(1)
    
    print(f"Found {len(subjects_to_process)} subjects to process.")
    
    all_features = []
    excluded_subjects = []
    
    for subject_id in subjects_to_process:
        print(f"Processing {subject_id}...")
        try:
            df = extract_features_for_subject(subject_id, args.window_size, args.overlap)
            if df is not None and not df.empty:
                all_features.append(df)
                print(f"  -> Successfully extracted features for {subject_id}")
            else:
                print(f"  -> Failed to extract features for {subject_id} (empty result)")
                excluded_subjects.append(subject_id)
        except Exception as e:
            print(f"  -> Error processing {subject_id}: {e}")
            excluded_subjects.append(subject_id)
    
    if not all_features:
        print("Error: No features extracted from any subject.")
        sys.exit(1)
    
    # Combine all dataframes
    final_df = pd.concat(all_features, ignore_index=True)
    
    # Save to CSV
    final_df.to_csv(output_file, index=False)
    
    print(f"\nFeature extraction complete.")
    print(f"Total subjects processed: {len(subjects_to_process)}")
    print(f"Successfully processed: {len(subjects_to_process) - len(excluded_subjects)}")
    print(f"Excluded: {len(excluded_subjects)}")
    if excluded_subjects:
        print(f"Excluded subjects: {excluded_subjects}")
    print(f"Output saved to: {output_file}")
    print(f"Shape of output: {final_df.shape}")
    print(f"Columns: {list(final_df.columns)}")

if __name__ == '__main__':
    main()