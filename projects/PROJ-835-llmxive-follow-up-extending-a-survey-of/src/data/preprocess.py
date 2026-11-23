"""
Preprocessing module for audio data in the LlmXive follow-up project.

This module handles:
- Loading audio files using librosa
- Validating audio file integrity
- Computing file hashes for integrity tracking
- Preprocessing batches of audio into embeddings-ready format
- Validating label independence (checking for latent-space correlation in metadata)

Requirements:
- FR-005: Skip corrupted files gracefully
- FR-005: Validate label independence
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import librosa
from scipy import stats

# Import from project utilities
from src.utils.config import get_path, ensure_dir, compute_file_hash, load_state, save_state
from src.utils.logging_config import get_module_logger
from src.utils.env_config import enforce_cpu_only

# Ensure CPU-only execution at module load
enforce_cpu_only()

# Configure logger
logger = get_module_logger(__name__)

# Constants
SAMPLE_RATE = 16000  # Standard sample rate for Whisper-based models
MAX_DURATION_SECONDS = 30  # Maximum audio duration to process
CORRUPTED_FILES_LOG = "data/corrupted_files.json"
LABEL_INDEPENDENCE_REPORT = "data/label_independence_report.json"


def get_audio_duration(file_path: Path) -> float:
    """
    Get the duration of an audio file in seconds.

    Args:
        file_path: Path to the audio file

    Returns:
        Duration in seconds

    Raises:
        ValueError: If file cannot be read or is corrupted
    """
    try:
        # librosa.info reads metadata without loading full audio
        info = librosa.info(str(file_path))
        return info.duration
    except Exception as e:
        logger.error(f"Failed to get duration for {file_path}: {e}")
        raise ValueError(f"Cannot read audio file {file_path}: {e}")


def validate_audio_file(file_path: Path, max_duration: float = MAX_DURATION_SECONDS) -> Tuple[bool, Optional[str]]:
    """
    Validate an audio file for basic integrity.

    Checks:
    - File exists
    - File is readable by librosa
    - Duration is within acceptable bounds
    - File is not empty

    Args:
        file_path: Path to the audio file
        max_duration: Maximum allowed duration in seconds

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check file exists
    if not file_path.exists():
        return False, "File does not exist"

    # Check file size (must be > 0)
    if file_path.stat().st_size == 0:
        return False, "File is empty"

    # Try to load audio metadata
    try:
        info = librosa.info(str(file_path))
        if info.duration > max_duration:
            return False, f"Duration {info.duration:.2f}s exceeds maximum {max_duration}s"
        if info.duration <= 0:
            return False, "Invalid duration (0 or negative)"
    except Exception as e:
        return False, f"Cannot read audio: {str(e)}"

    return True, None


def load_audio_file(file_path: Path, target_sr: int = SAMPLE_RATE) -> Tuple[np.ndarray, int]:
    """
    Load an audio file and return waveform and sample rate.

    Args:
        file_path: Path to the audio file
        target_sr: Target sample rate (default: 16000)

    Returns:
        Tuple of (audio_waveform, sample_rate)

    Raises:
        ValueError: If file is corrupted or cannot be loaded
    """
    try:
        # Load audio with librosa, resampling if necessary
        y, sr = librosa.load(str(file_path), sr=target_sr, mono=True)
        return y, sr
    except Exception as e:
        logger.error(f"Failed to load audio file {file_path}: {e}")
        raise ValueError(f"Corrupted audio file {file_path}: {e}")


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file for integrity tracking.

    Args:
        file_path: Path to the file

    Returns:
        Hex string of SHA-256 hash
    """
    return compute_file_hash(file_path)


def preprocess_audio_batch(
    file_paths: List[Path],
    target_sr: int = SAMPLE_RATE
) -> Tuple[List[np.ndarray], List[Path], List[str]]:
    """
    Preprocess a batch of audio files.

    Loads each file, validates it, and returns the waveforms.
    Corrupted files are skipped and logged.

    Args:
        file_paths: List of paths to audio files
        target_sr: Target sample rate

    Returns:
        Tuple of:
            - List of audio waveforms (numpy arrays)
            - List of successfully processed file paths
            - List of error messages for failed files
    """
    waveforms = []
    valid_paths = []
    errors = []

    for file_path in file_paths:
        # Validate file first
        is_valid, error_msg = validate_audio_file(file_path)
        if not is_valid:
            errors.append(f"{file_path}: {error_msg}")
            logger.warning(f"Skipping corrupted file: {file_path} - {error_msg}")
            continue

        # Load audio
        try:
            y, sr = load_audio_file(file_path, target_sr)
            waveforms.append(y)
            valid_paths.append(file_path)
        except Exception as e:
            error_msg = f"Failed to load {file_path}: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

    return waveforms, valid_paths, errors


def validate_label_independence(
    data_dir: Path,
    labels_file: Path,
  ) -> Dict[str, Any]:
    """
    Validate that there is no latent-space correlation in dataset metadata.

    This function checks if labels are correlated with metadata fields that
    could introduce bias (e.g., file length, sample rate, file size).
    If significant correlation is detected, the pipeline should fail.

    Args:
        data_dir: Directory containing audio files
        labels_file: Path to JSON file containing labels and metadata

    Returns:
        Dictionary containing validation results:
            - passed: bool (True if no significant correlation)
            - correlations: dict of metadata field -> correlation coefficient
            - p_values: dict of metadata field -> p-value
            - significant_correlations: list of fields with p < 0.05 or r > 0.3
            - report_path: path to saved report
    """
    logger.info(f"Validating label independence for {labels_file}")

    # Load labels and metadata
    if not labels_file.exists():
        logger.error(f"Labels file not found: {labels_file}")
        return {
            "passed": False,
            "error": "Labels file not found",
            "correlations": {},
            "p_values": {},
            "significant_correlations": []
        }

    with open(labels_file, 'r') as f:
        data = json.load(f)

    # Extract metadata fields to check
    metadata_fields = ['duration', 'file_size', 'sample_rate']
    results = {
        "passed": True,
        "correlations": {},
        "p_values": {},
        "significant_correlations": []
    }

    # Extract labels and metadata
    labels = []
    metadata_values = {field: [] for field in metadata_fields}

    for item in data:
        labels.append(item.get('label', 0))
        for field in metadata_fields:
            if field in item:
                metadata_values[field].append(item[field])

    # Check correlation for each metadata field
    significant_fields = []
    for field in metadata_fields:
        values = metadata_values[field]
        if len(values) != len(labels) or len(values) < 10:
            continue

        # Calculate Pearson correlation
        try:
            r, p_value = stats.pearsonr(labels, values)
            results["correlations"][field] = float(r)
            results["p_values"][field] = float(p_value)

            # Check for significant correlation (p < 0.05 or r > 0.3)
            if p_value < 0.05 or abs(r) > 0.3:
                significant_fields.append(field)
                logger.warning(f"Significant correlation detected: {field} (r={r:.3f}, p={p_value:.4f})")
        except Exception as e:
            logger.warning(f"Could not compute correlation for {field}: {e}")
            continue

    results["significant_correlations"] = significant_fields

    # Determine if validation passed
    if significant_fields:
        results["passed"] = False
        logger.error(f"Label independence validation FAILED. Significant correlations found: {significant_fields}")
    else:
        logger.info("Label independence validation PASSED. No significant correlations detected.")

    # Save report
    report_path = get_path(LABEL_INDEPENDENCE_REPORT)
    ensure_dir(Path(report_path).parent)
    results["report_path"] = str(report_path)

    with open(report_path, 'w') as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """
    Main function to run preprocessing and label independence validation.

    This function:
    1. Loads the dataset metadata
    2. Validates audio files (skipping corrupted ones)
    3. Validates label independence
    4. Logs results and saves reports
    """
    logger.info("Starting preprocessing pipeline")

    # Enforce CPU-only
    enforce_cpu_only()

    # Get paths
    data_dir = get_path("data/raw")
    labels_file = get_path("data/labels.json")
    corrupted_log = get_path(CORRUPTED_FILES_LOG)

    # Ensure directories exist
    ensure_dir(data_dir)
    ensure_dir(Path(corrupted_log).parent)

    # Check if labels file exists
    if not labels_file.exists():
        logger.error(f"Labels file not found: {labels_file}")
        sys.exit(1)

    # Load metadata to get file list
    with open(labels_file, 'r') as f:
        labels_data = json.load(f)

    # Collect all file paths
    file_paths = []
    for item in labels_data:
        file_path = Path(data_dir) / item.get('file_path', '')
        if file_path.exists():
            file_paths.append(file_path)

    logger.info(f"Found {len(file_paths)} audio files to process")

    # Process files in batches
    batch_size = 32
    all_waveforms = []
    all_valid_paths = []
    all_errors = []
    corrupted_files = []

    for i in range(0, len(file_paths), batch_size):
        batch = file_paths[i:i+batch_size]
        logger.info(f"Processing batch {i//batch_size + 1} ({len(batch)} files)")

        waveforms, valid_paths, errors = preprocess_audio_batch(batch)

        all_waveforms.extend(waveforms)
        all_valid_paths.extend(valid_paths)
        all_errors.extend(errors)

        # Track corrupted files
        for error in errors:
            corrupted_files.append({
                "file": error.split(':')[0],
                "reason": ':'.join(error.split(':')[1:]).strip()
            })

    # Log corrupted files
    if corrupted_files:
        logger.warning(f"Found {len(corrupted_files)} corrupted files")
        with open(corrupted_log, 'w') as f:
            json.dump(corrupted_files, f, indent=2)
    else:
        logger.info("No corrupted files found")

    # Validate label independence
    logger.info("Validating label independence...")
    independence_results = validate_label_independence(data_dir, labels_file)

    # Save summary
    summary = {
        "total_files": len(file_paths),
        "processed_files": len(all_valid_paths),
        "corrupted_files": len(corrupted_files),
        "label_independence_passed": independence_results["passed"],
        "significant_correlations": independence_results["significant_correlations"],
        "timestamp": str(Path.cwd())
    }

    summary_path = get_path("data/preprocessing_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Preprocessing complete. Summary saved to {summary_path}")

    # Exit with error if label independence failed
    if not independence_results["passed"]:
        logger.error("Pipeline FAILED: Label independence validation failed")
        sys.exit(1)

    logger.info("Preprocessing pipeline completed successfully")


if __name__ == "__main__":
    main()
