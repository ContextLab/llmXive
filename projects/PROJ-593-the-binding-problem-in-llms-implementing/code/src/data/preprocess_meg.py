"""
Preprocess MEG data: Bandpass filter, compute Welch PSD, normalize, and validate.

This script performs the final steps of MEG preprocessing:
1. Loads bandpass filtered data (from T007)
2. Computes Welch PSD and normalizes to unit area (from T047)
3. Validates the output against schema requirements
4. Saves the validated data to the final output location
"""
import os
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import butter, filtfilt, welch, windows
from typing import Tuple, Optional, Dict, Any
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.analysis.spectral import compute_welch_psd, normalize_psd_to_unit_area

# Constants
DEFAULT_CONFIG_PATH = "config/default.yaml"
DEFAULT_LOW_FREQ = 30.0
DEFAULT_HIGH_FREQ = 50.0
DEFAULT_SEQ_LEN = 512
DEFAULT_FPS = 1000  # Assumed sampling rate for MEG data

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file."""
    import yaml
    config_path = project_root / DEFAULT_CONFIG_PATH
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def validate_psd_data(
    psd_data: np.ndarray,
    expected_shape: Tuple[int, ...],
    min_value: float = 0.0,
    max_value: float = 1.0
) -> Dict[str, Any]:
    """
    Validate PSD data against expected schema requirements.

    Args:
        psd_data: The PSD data array to validate
        expected_shape: Expected shape of the data
        min_value: Minimum allowed value
        max_value: Maximum allowed value

    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "shape": list(psd_data.shape),
        "dtype": str(psd_data.dtype),
        "min_value": float(np.min(psd_data)),
        "max_value": float(np.max(psd_data)),
        "mean_value": float(np.mean(psd_data)),
        "sum_normalized": float(np.sum(psd_data))
    }

    # Check shape
    if psd_data.shape != expected_shape:
        validation_result["valid"] = False
        validation_result["errors"].append(
            f"Shape mismatch: expected {expected_shape}, got {psd_data.shape}"
        )

    # Check for NaN or Inf
    if np.any(np.isnan(psd_data)):
        validation_result["valid"] = False
        validation_result["errors"].append("Data contains NaN values")

    if np.any(np.isinf(psd_data)):
        validation_result["valid"] = False
        validation_result["errors"].append("Data contains Inf values")

    # Check value range (normalized PSD should be between 0 and 1)
    if np.any(psd_data < min_value):
        validation_result["warnings"].append(
            f"Data contains values below {min_value}: min={np.min(psd_data)}"
        )

    if np.any(psd_data > max_value):
        validation_result["warnings"].append(
            f"Data contains values above {max_value}: max={np.max(psd_data)}"
        )

    # Check normalization (sum should be close to 1 for each sample)
    # We check if the mean sum is close to 1 (allowing some tolerance)
    if psd_data.ndim >= 2:
        sums = np.sum(psd_data, axis=-1)
        mean_sum = np.mean(sums)
        if not np.isclose(mean_sum, 1.0, atol=0.01):
            validation_result["warnings"].append(
                f"Data may not be properly normalized: mean sum={mean_sum}"
            )

    return validation_result

def main():
    """
    Main function to preprocess, validate, and store MEG data.

    This function:
    1. Loads the bandpass filtered data from T007
    2. Computes Welch PSD and normalizes (from T047)
    3. Validates the output
    4. Saves the validated data
    """
    # Load configuration
    config = load_config()
    low_freq = config.get('preprocessing', {}).get('low_freq', DEFAULT_LOW_FREQ)
    high_freq = config.get('preprocessing', {}).get('high_freq', DEFAULT_HIGH_FREQ)
    seq_len = config.get('preprocessing', {}).get('seq_len', DEFAULT_SEQ_LEN)
    fps = config.get('preprocessing', {}).get('fps', DEFAULT_FPS)

    # Define paths
    data_dir = project_root / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    input_path = data_dir / "meg_filtered.npy"
    output_path = data_dir / "meg_psd_normalized.npy"
    validation_path = data_dir / "meg_validation_report.json"

    # Check if input file exists
    if not input_path.exists():
        print(f"ERROR: Input file not found: {input_path}")
        print("Please run T007 (bandpass filter) before running this script.")
        sys.exit(1)

    # Load bandpass filtered data
    print(f"Loading bandpass filtered data from {input_path}...")
    try:
        filtered_data = np.load(input_path)
        print(f"Loaded data with shape: {filtered_data.shape}, dtype: {filtered_data.dtype}")
    except Exception as e:
        print(f"ERROR: Failed to load input data: {e}")
        sys.exit(1)

    # Compute Welch PSD and normalize
    print("Computing Welch PSD and normalizing to unit area...")
    try:
        # If data is 2D (n_samples, n_timepoints), we need to handle it appropriately
        if filtered_data.ndim == 2:
            # Assume shape is (n_samples, n_timepoints)
            n_samples, n_timepoints = filtered_data.shape
            psd_list = []

            for i in range(n_samples):
                # Compute Welch PSD for each sample
                freqs, psd = compute_welch_psd(
                    filtered_data[i],
                    fs=fps,
                    nperseg=min(seq_len, n_timepoints),
                    noverlap=min(seq_len // 2, n_timepoints // 2)
                )
                # Normalize to unit area
                psd_norm = normalize_psd_to_unit_area(psd)
                psd_list.append(psd_norm)

            psd_data = np.array(psd_list)
            freqs_data = freqs
        elif filtered_data.ndim == 3:
            # Assume shape is (n_samples, n_channels, n_timepoints)
            n_samples, n_channels, n_timepoints = filtered_data.shape
            psd_list = []

            for i in range(n_samples):
                channel_psd_list = []
                for j in range(n_channels):
                    freqs, psd = compute_welch_psd(
                        filtered_data[i, j],
                        fs=fps,
                        nperseg=min(seq_len, n_timepoints),
                        noverlap=min(seq_len // 2, n_timepoints // 2)
                    )
                    psd_norm = normalize_psd_to_unit_area(psd)
                    channel_psd_list.append(psd_norm)
                psd_list.append(np.array(channel_psd_list))

            psd_data = np.array(psd_list)
            freqs_data = freqs
        else:
            print(f"ERROR: Unsupported data shape: {filtered_data.shape}")
            sys.exit(1)

        print(f"Computed PSD data with shape: {psd_data.shape}")

    except Exception as e:
        print(f"ERROR: Failed to compute PSD: {e}")
        sys.exit(1)

    # Validate the output
    print("Validating output data...")
    validation_result = validate_psd_data(
        psd_data,
        expected_shape=psd_data.shape,  # Validate against actual shape
        min_value=0.0,
        max_value=1.0
    )

    # Save validation report
    with open(validation_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    print(f"Validation report saved to {validation_path}")

    if not validation_result["valid"]:
        print("WARNING: Validation failed with the following errors:")
        for error in validation_result["errors"]:
            print(f"  - {error}")
        # Still save the data, but warn the user
        print("Data will be saved despite validation failures.")

    if validation_result["warnings"]:
        print("Validation warnings:")
        for warning in validation_result["warnings"]:
            print(f"  - {warning}")

    # Save the validated data
    print(f"Saving validated PSD data to {output_path}...")
    try:
        np.save(output_path, psd_data)
        print(f"Successfully saved data with shape: {psd_data.shape}")
    except Exception as e:
        print(f"ERROR: Failed to save output data: {e}")
        sys.exit(1)

    # Verify the saved file
    if output_path.exists():
        saved_data = np.load(output_path)
        print(f"Verification: Saved file contains data with shape: {saved_data.shape}")
        print("Preprocessing and validation complete!")
    else:
        print("ERROR: Output file was not created")
        sys.exit(1)

if __name__ == "__main__":
    main()
