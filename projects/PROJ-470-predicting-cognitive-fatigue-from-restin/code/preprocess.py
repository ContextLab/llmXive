"""
EEG Preprocessing Pipeline for Cognitive Fatigue Study.

This module implements the full preprocessing pipeline including:
- Bandpass filtering (1-40 Hz)
- Notch filtering (50 Hz)
- Re‑referencing
- Artifact rejection (amplitude and length)
- Parallel processing of the full dataset
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch

# Import logging utility from the shared module
from utils.logging import get_logger, log_participant_exclusion, log_artifact_rejection, save_exclusion_log_csv

# Global logger instance
logger = get_logger("preprocess")

# Constants
MIN_SEGMENT_DURATION_SEC = 120
ARTIFACT_THRESHOLD_UV = 100.0
OUTPUT_DIR = "data/processed/cleaned_eeg"
EXCLUSION_LOG_PATH = "data/processed/exclusion_log.csv"
MANIFEST_PATH = "data/raw/download_manifest.json"


def load_config() -> Dict[str, Any]:
    """Load configuration from ``code/config.yaml``."""
    import yaml
    config_path = Path("code/config.yaml")
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    # Ensure required keys exist with defaults
    defaults = {
        "filter_low": 1.0,
        "filter_high": 40.0,
        "notch_frequency": 50.0,
        "artifact_threshold_uV": 100,
        "random_seed": 42,
    }

    for key, default_val in defaults.items():
        if key not in config:
            config[key] = default_val
        else:
            # Type conversion if necessary
            if key == "artifact_threshold_uV":
                config[key] = int(config[key])
            else:
                config[key] = float(config[key])

    return config


def load_manifest(manifest_path: str = MANIFEST_PATH) -> List[Dict[str, Any]]:
    """
    Load the download manifest containing participant data.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        List of participant dictionaries.
    """
    if not os.path.exists(manifest_path):
        logger.error(f"Manifest file not found: {manifest_path}")
        logger.error("Please run ``code/download.py`` first to generate the manifest.")
        sys.exit(1)

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    if not isinstance(manifest, list):
        logger.error("Manifest must be a list of participant entries.")
        sys.exit(1)

    logger.info(f"Loaded manifest with {len(manifest)} participants.")
    return manifest


def apply_bandpass_filter(
    data: np.ndarray,
    sfreq: float,
    low_cut: float = 1.0,
    high_cut: float = 40.0,
) -> np.ndarray:
    """
    Apply a 4th‑order Butterworth band‑pass filter.

    Args:
        data: EEG data array (channels × samples).
        sfreq: Sampling frequency in Hz.
        low_cut: Low cutoff frequency.
        high_cut: High cutoff frequency.

    Returns:
        Filtered data array.
    """
    nyquist = sfreq / 2.0

    # Normalise frequencies
    low = low_cut / nyquist
    high = high_cut / nyquist

    low = max(0.001, min(low, 0.999))
    high = max(0.001, min(high, 0.999))

    b, a = butter(4, [low, high], btype="band")
    filtered_data = filtfilt(b, a, data, axis=-1)

    return filtered_data


def apply_notch_filter(
    data: np.ndarray,
    sfreq: float,
    freq: float = 50.0,
    q: float = 30.0,
) -> np.ndarray:
    """
    Apply a notch filter to remove line noise.

    Args:
        data: EEG data array.
        sfreq: Sampling frequency in Hz.
        freq: Notch frequency (50 Hz or 60 Hz).
        q: Quality factor (higher = narrower notch).

    Returns:
        Filtered data array.
    """
    nyquist = sfreq / 2.0
    freq = min(freq, nyquist * 0.99)  # Ensure frequency is valid

    b, a = iirnotch(freq / nyquist, q)
    filtered_data = filtfilt(b, a, data, axis=-1)

    return filtered_data


def re_reference(data: np.ndarray, method: str = "average") -> np.ndarray:
    """
    Re‑reference EEG data.

    Args:
        data: EEG data array (channels × samples).
        method: ``'average'`` (default) or ``'common'`` (placeholder).

    Returns:
        Re‑referenced data array.
    """
    if method == "average":
        mean_signal = np.mean(data, axis=0, keepdims=True)
        return data - mean_signal
    logger.warning(f"Unknown re‑referencing method: {method}. Returning original data.")
    return data


def reject_artifacts_by_amplitude(
    data: np.ndarray,
    threshold_uv: float = 100.0,
) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
    """
    Reject epochs that exceed amplitude thresholds.

    Args:
        data: EEG data array (epochs × channels × samples).
        threshold_uv: Threshold in µV.

    Returns:
        Tuple of (cleaned_data, list of rejection logs).
    """
    rejection_logs = []
    cleaned_epochs = []

    # Convert threshold to volts (MNE stores data in V)
    threshold = threshold_uv * 1e-6

    for i, epoch in enumerate(data):
        max_amplitude = np.max(np.abs(epoch))
        if max_amplitude > threshold:
            rejection_logs.append(
                {
                    "epoch_index": i,
                    "max_amplitude_uv": max_amplitude * 1e6,
                    "threshold_uv": threshold_uv,
                    "reason": "amplitude_exceeded",
                }
            )
        else:
            cleaned_epochs.append(epoch)

    cleaned_data = np.array(cleaned_epochs) if cleaned_epochs else np.array([])
    if not cleaned_epochs:
        logger.warning("All epochs rejected due to amplitude threshold.")
    return cleaned_data, rejection_logs


def validate_segment_length(
    data: np.ndarray,
    sfreq: float,
    min_duration_sec: float = MIN_SEGMENT_DURATION_SEC,
) -> Tuple[np.ndarray, bool]:
    """
    Validate that a segment meets the minimum duration requirement.

    Args:
        data: EEG data array (channels × samples).
        sfreq: Sampling frequency in Hz.
        min_duration_sec: Minimum required duration.

    Returns:
        Tuple of (data, is_valid).
    """
    n_samples = data.shape[-1]
    duration_sec = n_samples / sfreq
    if duration_sec < min_duration_sec:
        logger.warning(
            f"Segment duration {duration_sec:.2f}s < {min_duration_sec}s. Excluding."
        )
        return data, False
    return data, True


def process_segment(
    raw_data: np.ndarray,
    sfreq: float,
    participant_id: str,
    segment_id: str,
    config: Dict[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Process a single EEG segment: filter, re‑reference and reject artifacts.

    This is a pure function with no file I/O.  It returns the processed data
    and a list of any rejection logs that were generated.
    """
    rejection_logs = []

    # Band‑pass
    filtered_data = apply_bandpass_filter(
        raw_data,
        sfreq,
        low_cut=config["filter_low"],
        high_cut=config["filter_high"],
    )

    # Notch
    filtered_data = apply_notch_filter(
        filtered_data, sfreq, freq=config["notch_frequency"]
    )

    # Re‑reference
    re_ref_data = re_reference(filtered_data, method="average")

    # Length check
    re_ref_data, is_valid_length = validate_segment_length(
        re_ref_data,
        sfreq,
        config.get("min_duration_sec", MIN_SEGMENT_DURATION_SEC),
    )
    if not is_valid_length:
        rejection_logs.append(
            {
                "participant_id": participant_id,
                "segment_id": segment_id,
                "reason": "segment_too_short",
                "timestamp": datetime.utcnow().isoformat(),
            }
        )
        return (
            {
                "processed_data": None,
                "participant_id": participant_id,
                "segment_id": segment_id,
            },
            rejection_logs,
        )

    # Artifact rejection (single‑epoch wrapper)
    data_for_rejection = re_ref_data[np.newaxis, :, :]
    cleaned_data, artifact_logs = reject_artifacts_by_amplitude(
        data_for_rejection, threshold_uv=config["artifact_threshold_uV"]
    )
    for log in artifact_logs:
        rejection_logs.append(
            {
                "participant_id": participant_id,
                "segment_id": segment_id,
                "reason": "artifact_rejected",
                "max_amplitude_uv": log["max_amplitude_uv"],
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    if cleaned_data.size == 0:
        return (
            {
                "processed_data": None,
                "participant_id": participant_id,
                "segment_id": segment_id,
            },
            rejection_logs,
        )

    processed_data = cleaned_data[0]
    metadata = {
        "processed_data": processed_data,
        "sfreq": sfreq,
        "participant_id": participant_id,
        "segment_id": segment_id,
        "n_channels": processed_data.shape[0],
        "n_samples": processed_data.shape[1],
    }
    return metadata, rejection_logs


def save_cleaned_data(metadata: Dict[str, Any], output_path: str) -> None:
    """
    Save processed EEG data to a ``.fif`` file.

    The heavy ``mne`` import is performed lazily so that the module can be
    imported even on systems where ``mne`` is not installed – the import
    error will be raised only when this function is actually called.
    """
    if metadata["processed_data"] is None:
        logger.warning(
            f"No data to save for {metadata['participant_id']}_{metadata['segment_id']}."
        )
        return

    try:
        import mne  # Local import – optional at import time
    except ImportError as exc:
        logger.error("MNE‑Python is required for saving cleaned data.")
        raise exc

    info = mne.create_info(
        ch_names=[f"EEG{i:03d}" for i in range(metadata["n_channels"])],
        sfreq=metadata["sfreq"],
        ch_types="eeg",
    )
    raw = mne.io.RawArray(metadata["processed_data"], info)
    raw.save(output_path, overwrite=True)
    logger.info(f"Saved cleaned data to {output_path}")


def process_single_entry(args: Tuple[Dict[str, Any], Dict[str, Any]]) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Process a single manifest entry – intended for parallel execution.
    """
    entry, config = args
    participant_id = entry["participant_id"]
    segment_id = entry.get("segment_id", "0")
    file_path = entry["file_path"]

    logger.info(f"Processing {participant_id}/{segment_id} from {file_path}")

    try:
        # Lazy import of ``mne`` – avoids import‑time failures when the library is absent.
        import mne
        raw = mne.io.read_raw_fif(file_path, preload=True)
        data = raw.get_data()
        sfreq = raw.info["sfreq"]
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        return participant_id, [
            {
                "participant_id": participant_id,
                "segment_id": segment_id,
                "reason": "load_error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }
        ]

    metadata, rejection_logs = process_segment(
        data, sfreq, participant_id, segment_id, config
    )

    if metadata["processed_data"] is not None:
        output_dir = Path(OUTPUT_DIR)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{participant_id}_{segment_id}.fif")
        save_cleaned_data(metadata, output_path)

    return participant_id, rejection_logs


def preprocess_eeg(n_jobs: int = -1) -> None:
    """
    Preprocess the entire dataset using parallel execution.
    """
    config = load_config()
    manifest = load_manifest()

    args_list = [(entry, config) for entry in manifest]

    all_rejection_logs: List[Dict[str, Any]] = []

    logger.info(f"Starting parallel preprocessing with {n_jobs} jobs.")
    with ProcessPoolExecutor(max_workers=n_jobs) as executor:
        futures = [executor.submit(process_single_entry, args) for args in args_list]

        for future in as_completed(futures):
            participant_id, logs = future.result()
            all_rejection_logs.extend(logs)
            if logs:
                logger.info(f"Rejection logs for {participant_id}: {len(logs)} entries.")

    # Write exclusion log (always creates the CSV, even if empty)
    if all_rejection_logs:
        save_exclusion_log_csv(all_rejection_logs, EXCLUSION_LOG_PATH)
        logger.info(f"Saved exclusion log to {EXCLUSION_LOG_PATH}")
    else:
        save_exclusion_log_csv([], EXCLUSION_LOG_PATH)
        logger.info("No rejections occurred. Created empty exclusion log.")

    output_dir = Path(OUTPUT_DIR)
    if output_dir.exists():
        files = list(output_dir.glob("*.fif"))
        logger.info(f"Preprocessing complete. Saved {len(files)} cleaned EEG files to {OUTPUT_DIR}.")
    else:
        logger.error(f"Output directory {OUTPUT_DIR} does not exist. Preprocessing may have failed.")


def main() -> None:
    """Entry point for the preprocessing pipeline."""
    parser = argparse.ArgumentParser(description="Preprocess EEG data for cognitive fatigue study.")
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=-1,
        help="Number of parallel jobs (default: -1 for all CPUs).",
    )
    args = parser.parse_args()
    preprocess_eeg(n_jobs=args.n_jobs)


if __name__ == "__main__":
    main()
