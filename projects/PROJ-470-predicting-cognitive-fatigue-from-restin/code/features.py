"""Feature extraction script for EEG complexity metrics.

Calculates Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE)
for resting-state EEG segments per channel.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import csv
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import mne
from nolds import lzc_c
from pyentropy import permutation_entropy

# Import shared utilities from the project structure
from utils.logging import get_logger, log_operation, save_exclusion_log_csv
from utils.monitor import ResourceMonitor, run_stage_with_memory
from config import load_config


def setup_logger(name: str, log_file: str | None = None):
    """Setup a logger for the current module."""
    # Delegate to the shared logging utility to maintain contract
    return get_logger(name)


def load_sample_path(manifest_path: str = "data/raw/download_manifest.json") -> str:
    """Load the path of the cleaned EEG file from the download manifest.

    Args:
        manifest_path: Path to the download manifest JSON file.

    Returns:
        Path to the cleaned EEG file.

    Raises:
        FileNotFoundError: If manifest or sample file is not found.
    """
    if not os.path.exists(manifest_path):
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}. "
                                "Please run code/download.py first.")

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # The manifest should contain the path to the cleaned file from T012
    # T012 writes to data/processed/cleaned_eeg.fif
    sample_path = manifest.get("cleaned_eeg_path") or manifest.get("sample_eeg_path")

    if not sample_path:
        raise ValueError("Manifest does not contain 'cleaned_eeg_path' or 'sample_eeg_path'.")

    if not os.path.exists(sample_path):
        raise FileNotFoundError(f"Cleaned EEG file not found at: {sample_path}")

    return sample_path


def load_eeg_data(file_path: str) -> mne.Epochs | mne.Raw:
    """Load EEG data from an FIF file.

    Args:
        file_path: Path to the FIF file.

    Returns:
        Loaded MNE data object (Raw or Epochs).
    """
    try:
        data = mne.io.read_raw_fif(file_path, preload=True)
        # If it's Raw, we need to handle it differently than Epochs
        # For this implementation, we assume preprocessed data might be Raw or Epochs
        # We will process based on the structure
        return data
    except Exception as e:
        raise RuntimeError(f"Failed to load EEG data from {file_path}: {e}")


def extract_complexity_metrics(
    data: mne.Epochs | mne.Raw,
    participant_id: str = "unknown",
    segment_id: str = "0"
) -> List[Dict[str, Any]]:
    """Calculate LZC and PE for each channel.

    Args:
        data: MNE Raw or Epochs object.
        participant_id: Identifier for the participant.
        segment_id: Identifier for the segment.

    Returns:
        List of dictionaries containing metrics per channel.
    """
    logger = get_logger("features")
    log_operation("feature_extraction_start", participant_id=participant_id)

    results = []

    # Determine channels
    if isinstance(data, mne.Epochs):
        # Average over epochs to get a single time series per channel
        # Or process each epoch? The task implies "per channel per segment".
        # Assuming we process the averaged data for the segment or the first epoch.
        # To be robust, we'll average across epochs for a cleaner signal for complexity.
        data_array = data.get_data() # Shape: (n_epochs, n_channels, n_times)
        # Average across epochs
        data_array = np.mean(data_array, axis=0) # Shape: (n_channels, n_times)
        info = data.info
    else:
        # Raw data
        data_array = data.get_data() # Shape: (n_channels, n_times)
        info = data.info

    channels = info['ch_names']
    sfreq = info['sfreq']

    # Parameters
    emb_dim = 3
    delay = 1

    for idx, ch_name in enumerate(channels):
        signal = data_array[idx, :]

        # Remove NaNs if any (simple interpolation or drop)
        valid_mask = ~np.isnan(signal)
        if not np.all(valid_mask):
            signal = signal[valid_mask]
            if len(signal) < 100: # Minimum length check
                logger.warning(f"Channel {ch_name} too short after NaN removal, skipping.")
                continue

        # 1. Lempel-Ziv Complexity (LZC)
        # nolds.lzc_c expects a sequence. We can use the raw signal or quantize.
        # Task says: "Use median quantization for LZC".
        try:
            median_val = np.median(signal)
            binary_signal = (signal > median_val).astype(int)
            lzc_val = lzc_c(binary_signal)
        except Exception as e:
            logger.error(f"Error calculating LZC for {ch_name}: {e}")
            lzc_val = np.nan

        # 2. Permutation Entropy (PE)
        # pyentropy.permutation_entropy
        try:
            # Ensure signal is integer or float compatible
            pe_val = permutation_entropy(signal, order=emb_dim, delay=delay, normalize=True)
        except Exception as e:
            logger.error(f"Error calculating PE for {ch_name}: {e}")
            pe_val = np.nan

        results.append({
            "participant_id": participant_id,
            "channel": ch_name,
            "segment_id": segment_id,
            "lzc_value": lzc_val,
            "pe_value": pe_val
        })

    log_operation("feature_extraction_complete", count=len(results))
    return results


def save_metrics(results: List[Dict[str, Any]], output_path: str):
    """Save complexity metrics to a CSV file.

    Args:
        results: List of metric dictionaries.
        output_path: Path to the output CSV file.
    """
    if not results:
        logger = get_logger("features")
        logger.warning("No metrics to save.")
        return

    df = pd.DataFrame(results)
    # Ensure columns are in the expected order
    expected_cols = ["participant_id", "channel", "segment_id", "lzc_value", "pe_value"]
    df = df[expected_cols]

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=False)
    logger = get_logger("features")
    log_operation("metrics_saved", path=output_path, rows=len(results))


def preprocess_eeg():
    """Main entry point for feature extraction."""
    logger = setup_logger("features")
    log_operation("pipeline_start")

    config = load_config()
    monitor = ResourceMonitor()

    try:
        # 1. Load sample path from manifest
        sample_path = load_sample_path()
        logger.info(f"Loading data from: {sample_path}")

        # 2. Load EEG data
        eeg_data = load_eeg_data(sample_path)

        # 3. Extract metrics
        # Determine participant/segment ID from filename or config
        # For now, use a default or extract from path
        base_name = os.path.basename(sample_path)
        # Heuristic: extract ID if present, else use 'unknown'
        # Assuming filename might be like 'sub-001_cleaned.fif'
        parts = base_name.split('_')
        pid = "unknown"
        sid = "0"
        for part in parts:
            if part.startswith("sub-"):
                pid = part.replace("sub-", "")
            elif part.startswith("seg-"):
                sid = part.replace("seg-", "")

        metrics = extract_complexity_metrics(eeg_data, participant_id=pid, segment_id=sid)

        # 4. Save to data/analysis/complexity_metrics.csv
        output_path = "data/analysis/complexity_metrics.csv"
        save_metrics(metrics, output_path)

        log_operation("pipeline_success", output=output_path)
        return True

    except FileNotFoundError as e:
        logger.error(f"Data not found: {e}")
        return False
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        return False
    finally:
        # Stop monitoring and save usage
        monitor.stop()
        # Save resource usage to the required path
        resource_usage = monitor.get_usage()
        usage_path = "data/analysis/resource_usage.json"
        os.makedirs(os.path.dirname(usage_path), exist_ok=True)
        with open(usage_path, 'w') as f:
            json.dump(resource_usage, f, indent=2)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Extract EEG complexity features.")
    parser.add_argument("--config", type=str, default="code/config.yaml", help="Path to config file.")
    args = parser.parse_args()

    # Run the pipeline
    success = preprocess_eeg()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
