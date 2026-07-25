"""
Preprocess MEG data: Bandpass filter, compute Welch PSD, normalize, and validate.

This script implements the full preprocessing pipeline for MEG data:
1. Bandpass filter (30-50Hz) - Part 1 (T007)
2. Compute Welch PSD and normalize to unit area - Part 2 (T047)
3. Validate and store pre-processed data - Part 3 (T008)

Dependencies:
- T005: download_meg.py (creates data/raw/meg_streamed.parquet)
- T007: Bandpass filtering
- T047: PSD computation and normalization
"""

import os
import sys
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.signal import butter, filtfilt, welch, windows

# Project root (assumes code/ is at project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Ensure output directory exists
DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Constants
SAMPLE_RATE = 1000.0  # Hz (assumed based on typical MEG data)
FREQ_LOW = 30.0       # Hz
FREQ_HIGH = 50.0      # Hz
NFFT = 512            # Zero-pad to 512 for PSD computation


def butter_bandpass(lowcut, highcut, fs, order=5):
    """Design a Butterworth bandpass filter."""
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band')
    return b, a


def apply_bandpass_filter(data, fs, lowcut, highcut, order=5):
    """Apply bandpass filter to data using filtfilt for zero-phase filtering."""
    b, a = butter_bandpass(lowcut, highcut, fs, order)
    # Apply filtfilt for zero-phase filtering (forward and backward)
    filtered_data = filtfilt(b, a, data, axis=0)
    return filtered_data


def compute_and_normalize_psd(data, fs, nfft=NFFT):
    """
    Compute Welch PSD and normalize to unit area.

    Args:
        data: numpy array of shape (n_channels, n_samples) or (n_samples,)
        fs: sampling frequency in Hz
        nfft: number of FFT points (zero-pad if necessary)

    Returns:
        freqs: frequency array
        psd_normalized: normalized PSD (unit area)
    """
    # Ensure data is 2D
    if data.ndim == 1:
        data = data.reshape(1, -1)

    n_channels = data.shape[0]
    n_samples = data.shape[1]

    # Initialize arrays for results
    freqs = None
    psd_normalized = np.zeros((n_channels, nfft // 2 + 1))

    for ch in range(n_channels):
        # Compute Welch PSD
        freqs_ch, psd_ch = welch(
            data[ch],
            fs=fs,
            nperseg=min(n_samples, nfft),
            nfft=nfft,
            scaling='density',
            window='hann'
        )

        # Normalize to unit area
        # Integral approximation using trapezoidal rule
        area = np.trapz(psd_ch, freqs_ch)
        if area > 0:
            psd_ch_normalized = psd_ch / area
        else:
            psd_ch_normalized = psd_ch  # Avoid division by zero

        psd_normalized[ch] = psd_ch_normalized

        # Store frequency array (same for all channels)
        if freqs is None:
            freqs = freqs_ch

    return freqs, psd_normalized


def validate_psd_data(psd_data, freqs, min_freq=30.0, max_freq=50.0, tolerance=1e-6):
    """
    Validate pre-processed PSD data.

    Checks:
    1. Data is not empty
    2. All values are non-negative (PSD property)
    3. Normalized PSD sums to approximately 1.0 (unit area)
    4. Frequency array is monotonic increasing
    5. Frequency range covers expected band (30-50Hz)

    Returns:
        dict: Validation results with status and details
    """
    validation_result = {
        "status": "valid",
        "checks": {},
        "warnings": [],
        "errors": []
    }

    # Check 1: Data is not empty
    if psd_data.size == 0:
        validation_result["status"] = "invalid"
        validation_result["errors"].append("PSD data is empty")
        return validation_result

    # Check 2: All values are non-negative
    if np.any(psd_data < 0):
        validation_result["status"] = "invalid"
        validation_result["errors"].append("PSD contains negative values")
    else:
        validation_result["checks"]["non_negative"] = True

    # Check 3: Normalized PSD sums to approximately 1.0 (unit area)
    # Use trapezoidal integration across frequency axis
    areas = np.trapz(psd_data, freqs, axis=1)
    expected_area = 1.0
    area_tolerance = 1e-3  # 0.1% tolerance for numerical precision

    for i, area in enumerate(areas):
        if abs(area - expected_area) > area_tolerance:
            validation_result["warnings"].append(
                f"Channel {i}: Normalized area = {area:.6f} (expected ~{expected_area})"
            )

    if not validation_result["warnings"]:
        validation_result["checks"]["unit_area"] = True

    # Check 4: Frequency array is monotonic increasing
    if not np.all(np.diff(freqs) > 0):
        validation_result["status"] = "invalid"
        validation_result["errors"].append("Frequency array is not monotonic increasing")
    else:
        validation_result["checks"]["monotonic_freq"] = True

    # Check 5: Frequency range covers expected band
    if freqs[0] > min_freq or freqs[-1] < max_freq:
        validation_result["warnings"].append(
            f"Frequency range [{freqs[0]:.1f}, {freqs[-1]:.1f}] Hz may not fully cover [{min_freq}, {max_freq}] Hz band"
        )
    else:
        validation_result["checks"]["freq_range"] = True

    return validation_result


def main():
    """
    Main function to preprocess and validate MEG data.

    Pipeline:
    1. Load raw MEG data from parquet file (from T005)
    2. Apply bandpass filter (30-50Hz) - Part 1 (T007)
    3. Compute Welch PSD and normalize to unit area - Part 2 (T047)
    4. Validate pre-processed data - Part 3 (T008)
    5. Save validated data and validation report
    """
    print("=" * 60)
    print("MEG Data Preprocessing Pipeline (Part 3: Validation)")
    print("=" * 60)

    # Step 1: Load raw MEG data
    input_file = DATA_RAW_DIR / "meg_streamed.parquet"
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_file}. "
            "Please run T005 (download_meg.py) first to create this file."
        )

    print(f"\n[1/5] Loading raw MEG data from {input_file}...")
    df = pd.read_parquet(input_file)

    # Extract signal data (assuming 'signal' column contains the MEG time series)
    # Adjust column name based on actual schema if needed
    if 'signal' in df.columns:
        signal_data = df['signal'].values
    elif 'data' in df.columns:
        signal_data = df['data'].values
    else:
        # Try to find a numeric column
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            signal_data = df[numeric_cols[0]].values
            print(f"  Warning: Using column '{numeric_cols[0]}' as signal data")
        else:
            raise ValueError("No signal data found in the dataset")

    # Ensure data is 2D (n_channels, n_samples)
    if signal_data.ndim == 1:
        signal_data = signal_data.reshape(1, -1)

    print(f"  Loaded data shape: {signal_data.shape}")

    # Step 2: Apply bandpass filter (30-50Hz)
    print(f"\n[2/5] Applying bandpass filter ({FREQ_LOW}-{FREQ_HIGH} Hz)...")
    filtered_data = apply_bandpass_filter(
        signal_data,
        fs=SAMPLE_RATE,
        lowcut=FREQ_LOW,
        highcut=FREQ_HIGH
    )
    print(f"  Filtered data shape: {filtered_data.shape}")

    # Save filtered data (for T007 verification)
    filtered_output_file = DATA_PROCESSED_DIR / "meg_filtered.npy"
    np.save(filtered_output_file, filtered_data)
    print(f"  Saved filtered data to {filtered_output_file}")

    # Step 3: Compute Welch PSD and normalize to unit area
    print(f"\n[3/5] Computing Welch PSD and normalizing to unit area...")
    freqs, psd_normalized = compute_and_normalize_psd(
        filtered_data,
        fs=SAMPLE_RATE,
        nfft=NFFT
    )
    print(f"  PSD shape: {psd_normalized.shape}")
    print(f"  Frequency range: [{freqs[0]:.1f}, {freqs[-1]:.1f}] Hz")

    # Save normalized PSD (for T047 verification)
    psd_output_file = DATA_PROCESSED_DIR / "meg_psd_normalized.npy"
    np.save(psd_output_file, psd_normalized)
    print(f"  Saved normalized PSD to {psd_output_file}")

    # Step 4: Validate pre-processed data
    print(f"\n[4/5] Validating pre-processed data...")
    validation_result = validate_psd_data(psd_normalized, freqs)

    print(f"  Validation status: {validation_result['status'].upper()}")

    if validation_result['checks']:
        print("  Passed checks:")
        for check, passed in validation_result['checks'].items():
            if passed:
                print(f"    - {check}")

    if validation_result['warnings']:
        print("  Warnings:")
        for warning in validation_result['warnings']:
            print(f"    - {warning}")

    if validation_result['errors']:
        print("  Errors:")
        for error in validation_result['errors']:
            print(f"    - {error}")

    # Step 5: Save validation report
    validation_report_file = DATA_PROCESSED_DIR / "meg_validation_report.json"
    with open(validation_report_file, 'w') as f:
        json.dump(validation_result, f, indent=2)
    print(f"\n[5/5] Saved validation report to {validation_report_file}")

    # Final summary
    print("\n" + "=" * 60)
    print("Preprocessing Pipeline Complete")
    print("=" * 60)
    print(f"  Filtered data: {filtered_output_file}")
    print(f"  Normalized PSD: {psd_output_file}")
    print(f"  Validation report: {validation_report_file}")
    print(f"  Status: {validation_result['status'].upper()}")

    if validation_result['status'] == 'valid':
        print("\n✓ All validations passed. Data is ready for downstream analysis.")
        return 0
    else:
        print("\n✗ Validation failed. Please review errors and warnings.")
        return 1


if __name__ == "__main__":
    sys.exit(main())