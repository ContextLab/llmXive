"""
Feature extraction: Lempel-Ziv Complexity (LZC) and Permutation Entropy (PE).
Reads cleaned EEG data from data/processed/cleaned_eeg/ and writes metrics to data/analysis/complexity_metrics.csv.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import nolds
from pyentropy import perm_entropy

# Import logging utility from the shared module
from utils.logging import get_logger, log_operation

# Import config loader
from config import load_config


def setup_logger(name: str, log_file: str | None = None) -> Any:
    """Configure and return a logger. Delegates to the shared logging utility."""
    return get_logger(name)


def load_eeg_data(segment_path: Path) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Load a cleaned EEG segment from a .fif file.
    Returns (data, metadata) where data is (channels, samples).
    """
    import mne

    raw = mne.io.read_raw_fif(segment_path, preload=True)
    data = raw.get_data()  # Shape: (n_channels, n_samples)
    info = raw.info
    metadata = {
        "ch_names": info["ch_names"],
        "sfreq": info["sfreq"],
        "n_channels": len(info["ch_names"]),
        "n_samples": data.shape[1],
    }
    return data, metadata


def extract_lempel_ziv_complexity(signal: np.ndarray) -> float:
    """
    Calculate Lempel-Ziv Complexity (LZC) using median quantization.
    Uses nolds.lz6 which implements LZ76/LZ78 with median quantization.
    """
    # Ensure 1D array
    if signal.ndim > 1:
        raise ValueError("Signal must be 1D for LZC calculation.")
    
    # nolds.lz6 expects a sequence and uses median quantization internally
    try:
        lzc = nolds.lz6(signal)
        return float(lzc)
    except Exception as e:
        # Fallback to 0 if calculation fails (e.g., constant signal)
        return 0.0


def extract_permutation_entropy(signal: np.ndarray, order: int = 3, delay: int = 1) -> float:
    """
    Calculate Permutation Entropy (PE).
    Uses pyentropy.perm_entropy.
    """
    try:
        # pyentropy.perm_entropy expects a 1D array
        pe = perm_entropy(signal, order=order, delay=delay)
        return float(pe)
    except Exception as e:
        # Fallback to 0 if calculation fails
        return 0.0


def process_segment(data: np.ndarray, channel_idx: int, config: Dict[str, Any]) -> Tuple[float, float]:
    """
    Process a single channel of a segment to extract LZC and PE.
    Returns (lzc_value, pe_value).
    """
    channel_data = data[channel_idx, :]
    
    lzc = extract_lempel_ziv_complexity(channel_data)
    pe = extract_permutation_entropy(channel_data, order=3, delay=1)
    
    return lzc, pe


def write_metrics_to_csv(metrics: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Write the list of metrics dictionaries to a CSV file.
    """
    if not metrics:
        # Write header only if no data
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["participant_id", "channel", "segment_id", "lzc_value", "pe_value"])
        return

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["participant_id", "channel", "segment_id", "lzc_value", "pe_value"])
        for row in metrics:
            writer.writerow([
                row["participant_id"],
                row["channel"],
                row["segment_id"],
                row["lzc_value"],
                row["pe_value"]
            ])


def main() -> None:
    """
    Main entry point for feature extraction.
    Reads all cleaned segments from data/processed/cleaned_eeg/
    and writes complexity_metrics.csv to data/analysis/.
    """
    logger = setup_logger("features")
    config = load_config()

    input_dir = Path("data/processed/cleaned_eeg")
    output_dir = Path("data/analysis")
    output_file = output_dir / "complexity_metrics.csv"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_dir.exists():
        logger.error(f"Input directory {input_dir} does not exist. Please run preprocessing first.")
        sys.exit(1)

    eeg_files = list(input_dir.glob("*.fif"))
    if not eeg_files:
        logger.error(f"No .fif files found in {input_dir}.")
        sys.exit(1)

    logger.info(f"Found {len(eeg_files)} EEG segments to process.")

    all_metrics: List[Dict[str, Any]] = []

    for eeg_file in eeg_files:
        # Parse filename to extract participant_id and segment_id
        # Expected format: {participant_id}_{segment_id}.fif
        stem = eeg_file.stem
        parts = stem.split("_")
        if len(parts) >= 2:
            participant_id = parts[0]
            segment_id = "_".join(parts[1:]) # Handle cases where segment_id has underscores
        else:
            # Fallback: use whole stem as segment_id, participant_id as unknown
            participant_id = "unknown"
            segment_id = stem

        logger.info(f"Processing {eeg_file.name} -> P:{participant_id}, S:{segment_id}")

        try:
            data, metadata = load_eeg_data(eeg_file)
            n_channels = metadata["n_channels"]
            ch_names = metadata["ch_names"]

            for ch_idx, ch_name in enumerate(ch_names):
                lzc, pe = process_segment(data, ch_idx, config)
                
                metric_entry = {
                    "participant_id": participant_id,
                    "channel": ch_name,
                    "segment_id": segment_id,
                    "lzc_value": lzc,
                    "pe_value": pe
                }
                all_metrics.append(metric_entry)

        except Exception as e:
            logger.error(f"Failed to process {eeg_file.name}: {e}")
            # Continue with other files

    # Write results to CSV
    write_metrics_to_csv(all_metrics, output_file)
    logger.info(f"Successfully wrote {len(all_metrics)} metrics to {output_file}")


if __name__ == "__main__":
    main()
