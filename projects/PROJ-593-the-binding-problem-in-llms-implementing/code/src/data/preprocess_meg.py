"""
Preprocess MEG data: Bandpass filter, compute Welch PSD, and normalize.

This script performs the unified preprocessing steps for MEG data:
1. Loads streamed MEG data from data/raw/meg_streamed.parquet
2. Applies a 4th-order Butterworth bandpass filter (1-100 Hz)
3. Computes Welch PSD with zero-padding to 512, Hann window, nperseg=256
4. Normalizes PSD to unit area
5. Saves two artifacts:
   - data/processed/meg_filtered.npy (filtered time series)
   - data/processed/meg_psd_normalized.npy (normalized PSD)
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import butter, filtfilt, welch, windows

# Ensure code directory is in path for imports if running as script
code_root = Path(__file__).resolve().parent.parent.parent
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

def load_config():
    """Load configuration from config/default.yaml."""
    import yaml
    config_path = code_root / "config" / "default.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def butter_bandpass_filter(data, fs, lowcut, highcut, order=4):
    """
    Apply a Butterworth bandpass filter to the data.
    
    Args:
        data: 1D numpy array of time series data
        fs: Sampling frequency in Hz
        lowcut: Low cutoff frequency in Hz
        highcut: High cutoff frequency in Hz
        order: Order of the Butterworth filter (default 4)
    
    Returns:
        Filtered data as 1D numpy array
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    
    # Ensure cutoff frequencies are within valid range
    if low >= 1.0 or high >= 1.0 or low >= high:
        raise ValueError(f"Invalid cutoff frequencies: low={low}, high={high} (nyq={nyq})")
    
    b, a = butter(order, [low, high], btype='band')
    # Use filtfilt for zero-phase filtering
    y = filtfilt(b, a, data)
    return y

def apply_bandpass_filter(df, fs, lowcut=1.0, highcut=100.0, order=4):
    """
    Apply bandpass filter to MEG data in the DataFrame.
    
    Args:
        df: DataFrame with 'signal' column containing time series data
        fs: Sampling frequency in Hz
        lowcut: Low cutoff frequency (default 1.0 Hz)
        highcut: High cutoff frequency (default 100.0 Hz)
        order: Filter order (default 4)
    
    Returns:
        DataFrame with 'filtered_signal' column
    """
    if 'signal' not in df.columns:
        raise ValueError("DataFrame must contain 'signal' column")
    
    # Ensure signal is 1D
    signal = df['signal'].values.flatten()
    filtered = butter_bandpass_filter(signal, fs, lowcut, highcut, order)
    
    df['filtered_signal'] = filtered
    return df

def compute_and_normalize_psd(data, fs, nperseg=256, target_len=512):
    """
    Compute Welch PSD with zero-padding and normalize to unit area.
    
    Args:
        data: 1D numpy array of filtered time series
        fs: Sampling frequency in Hz
        nperseg: Length of each segment for Welch's method (default 256)
        target_len: Target length for zero-padding (default 512)
    
    Returns:
        Tuple of (frequencies, normalized_psd)
    """
    # Zero-pad to target length if needed
    if len(data) < target_len:
        pad_width = target_len - len(data)
        data_padded = np.pad(data, (0, pad_width), mode='constant', constant_values=0)
    else:
        data_padded = data[:target_len]  # Truncate if longer (shouldn't happen with streaming)
    
    # Use Hann window
    window = windows.hann(nperseg)
    
    # Compute Welch PSD
    # nperseg must be <= len(data_padded)
    actual_nperseg = min(nperseg, len(data_padded))
    freqs, psd = welch(data_padded, fs=fs, window=window, nperseg=actual_nperseg, 
                       scaling='density', average='mean')
    
    # Normalize to unit area (integral of PSD = 1)
    psd_area = np.trapz(psd, freqs)
    if psd_area == 0:
        raise ValueError("PSD area is zero; cannot normalize")
    psd_normalized = psd / psd_area
    
    return freqs, psd_normalized

def validate_psd_data(freqs, psd_normalized):
    """
    Validate PSD data against schema requirements.
    
    Args:
        freqs: Array of frequencies
        psd_normalized: Normalized PSD values
    
    Raises:
        ValueError: If validation fails
    """
    if len(freqs) != len(psd_normalized):
        raise ValueError("Frequency and PSD arrays must have same length")
    
    if np.any(psd_normalized < 0):
        raise ValueError("PSD values must be non-negative")
    
    # Check unit area normalization
    area = np.trapz(psd_normalized, freqs)
    if not np.isclose(area, 1.0, atol=1e-6):
        raise ValueError(f"PSD not normalized to unit area (area={area})")
    
    # Check frequency range (should include gamma band 30-80 Hz)
    if freqs[-1] < 30:
        raise ValueError(f"Maximum frequency {freqs[-1]} Hz is too low for gamma analysis")

def main():
    """Main function to run the preprocessing pipeline."""
    print("Starting MEG preprocessing pipeline...")
    
    # Load configuration
    config = load_config()
    fs = config.get('sampling_frequency', 1000.0)  # Default 1000 Hz if not specified
    lowcut = config.get('lowcut', 1.0)
    highcut = config.get('highcut', 100.0)
    
    # Define paths
    raw_path = code_root / "data" / "raw" / "meg_streamed.parquet"
    processed_dir = code_root / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    filtered_output = processed_dir / "meg_filtered.npy"
    psd_output = processed_dir / "meg_psd_normalized.npy"
    
    # Verify input file exists
    if not raw_path.exists():
        raise FileNotFoundError(f"Input file not found: {raw_path}. Run T005 first.")
    
    print(f"Loading MEG data from {raw_path}...")
    df = pd.read_parquet(raw_path)
    print(f"Loaded {len(df)} samples")
    
    # Step 1: Apply bandpass filter
    print(f"Applying bandpass filter ({lowcut}-{highcut} Hz)...")
    df_filtered = apply_bandpass_filter(df, fs, lowcut, highcut)
    
    # Save filtered data
    print(f"Saving filtered data to {filtered_output}...")
    filtered_signal = df_filtered['filtered_signal'].values
    np.save(filtered_output, filtered_signal)
    
    # Step 2: Compute Welch PSD and normalize
    print("Computing Welch PSD and normalizing...")
    freqs, psd_normalized = compute_and_normalize_psd(
        filtered_signal, fs, nperseg=256, target_len=512
    )
    
    # Validate
    print("Validating PSD data...")
    validate_psd_data(freqs, psd_normalized)
    
    # Save normalized PSD (save both freqs and psd as a structured array)
    print(f"Saving normalized PSD to {psd_output}...")
    psd_data = np.array([freqs, psd_normalized])
    np.save(psd_output, psd_data)
    
    print("Preprocessing complete!")
    print(f"  Filtered signal: {filtered_output} ({len(filtered_signal)} samples)")
    print(f"  Normalized PSD: {psd_output} ({len(freqs)} frequency bins)")
    
    return filtered_output, psd_output

if __name__ == "__main__":
    main()
