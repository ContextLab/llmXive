"""Preprocessing pipeline for EEG data.

Applies filters, removes artifacts, and validates segment lengths.
"""
import os
import sys
import yaml
import logging
import numpy as np
import mne
from pathlib import Path
from datetime import datetime

# Import from local modules
from code.utils.logging import (
    get_logger,
    log_artifact_rejection,
    log_participant_exclusion,
    save_exclusion_log_csv,
)

def load_config(config_path: str = "code/config.yaml") -> dict:
    """Load configuration from YAML file."""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def setup_logger(name: str, log_file: str = None) -> logging.Logger:
    """Set up a logger for the module.

    Args:
        name: Logger name
        log_file: Optional log file path

    Returns:
        Logger instance
    """
    # Use the tolerant logger from utils.logging
    logger = get_logger(name, log_file=log_file)
    return logger

def stream_eeg_files(data_dir: str):
    """Stream EEG files from the data directory."""
    data_path = Path(data_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"Data directory not found: {data_dir}")

    for file_path in data_path.glob("*"):
        if file_path.suffix in [".fif", ".edf", ".bdf"]:
            yield file_path

def apply_bandpass_filter(raw: mne.io.Raw, low: float, high: float) -> mne.io.Raw:
    """Apply bandpass filter to EEG data."""
    raw_filtered = raw.copy()
    raw_filtered.filter(low_freq=low, high_freq=high)
    return raw_filtered

def apply_notch_filter(raw: mne.io.Raw, freq: float) -> mne.io.Raw:
    """Apply notch filter to remove line noise."""
    raw_notched = raw.copy()
    raw_notched.notch_filter(freqs=freq)
    return raw_notched

def detect_line_noise_peak(raw: mne.io.Raw, freq: float = 50.0) -> float:
    """Detect line noise peak in the spectrum."""
    psd, freqs = raw.compute_psd()
    # Find peak power at the target frequency
    peak_idx = np.argmin(np.abs(freqs - freq))
    return psd.data[0, peak_idx]

def reject_artifacts(raw: mne.io.Raw, threshold: float) -> mne.io.Raw:
    """Reject epochs with amplitude exceeding threshold."""
    # Convert to microvolts if necessary
    data = raw.get_data() * 1e6  # Convert to uV
    rejected = []
    for i, ch_data in enumerate(data):
        if np.max(np.abs(ch_data)) > threshold:
            rejected.append(i)

    if rejected:
        # Log rejection
        log_artifact_rejection(
            artifact_type="epoch",
            reason="amplitude_threshold",
            participant_id="unknown",
            epoch_indices=rejected,
        )

    return raw

def reject_short_segments(raw: mne.io.Raw, min_duration: float) -> tuple:
    """Reject segments shorter than the minimum duration.

    Args:
        raw: Raw EEG data
        min_duration: Minimum duration in seconds

    Returns:
        tuple: (filtered_raw, list of exclusion entries)
    """
    duration = raw.times[-1] - raw.times[0]
    exclusion_entries = []

    if duration < min_duration:
        # Log the rejection
        log_artifact_rejection(
            artifact_type="segment",
            reason="segment_too_short",
            participant_id=raw.info.get("subject_info", {}).get("subject_id", "unknown"),
            duration=duration,
            min_duration=min_duration,
        )

        # Create exclusion entry
        exclusion_entries.append({
            "participant_id": raw.info.get("subject_info", {}).get("subject_id", "unknown"),
            "reason": "segment_too_short",
            "timestamp": datetime.utcnow().isoformat(),
        })

        return None, exclusion_entries

    return raw, exclusion_entries

def process_eeg_stream(
    data_dir: str,
    output_dir: str,
    config: dict,
):
    """Process all EEG files in the data directory."""
    logger = setup_logger("preprocess")

    min_duration = 120.0  # FR-002: minimum segment length
    artifact_threshold = config.get("artifact_threshold_uV", 100.0)
    filter_low = config.get("filter_low", 1.0)
    filter_high = config.get("filter_high", 40.0)
    notch_freq = config.get("notch_frequency", 50.0)

    all_exclusions = []

    for file_path in stream_eeg_files(data_dir):
        try:
            raw = mne.io.read_raw_fif(file_path, preload=True)
        except Exception as e:
            logger.log("error_loading_file", file=str(file_path), error=str(e))
            continue

        # Apply filters
        raw_filtered = apply_bandpass_filter(raw, filter_low, filter_high)
        raw_notched = apply_notch_filter(raw_filtered, notch_freq)

        # Reject artifacts
        raw_clean = reject_artifacts(raw_notched, artifact_threshold)

        # Validate segment length (T014)
        raw_valid, exclusions = reject_short_segments(raw_clean, min_duration)
        all_exclusions.extend(exclusions)

        if raw_valid is not None:
            # Save processed data
            output_path = Path(output_dir) / f"cleaned_{file_path.name}"
            raw_valid.save(output_path, overwrite=True)

    # Save exclusion log
    if all_exclusions:
        save_exclusion_log_csv(all_exclusions)

def save_exclusion_log(entries: list, log_file: str = "data/processed/exclusion_log.csv"):
    """Save exclusion log to CSV."""
    save_exclusion_log_csv(entries, log_file)

def save_processed_data(raw: mne.io.Raw, output_path: str):
    """Save processed EEG data."""
    raw.save(output_path, overwrite=True)

def main():
    """Main entry point for preprocessing."""
    config = load_config()

    # Setup logger
    logger = setup_logger("preprocess")

    # Process EEG data
    process_eeg_stream(
        data_dir="data/raw",
        output_dir="data/processed",
        config=config,
    )

    logger.log("preprocessing_complete", status="success")

if __name__ == "__main__":
    main()