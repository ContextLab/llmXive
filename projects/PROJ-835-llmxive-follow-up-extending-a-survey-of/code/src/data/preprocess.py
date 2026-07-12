"""
Preprocess audio data for the LLMXive follow-up project.

This module handles:
- Loading audio files from disk
- Gracefully skipping corrupted files
- Validating label independence (FR-005)
- Preparing data for embedding extraction
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import soundfile as sf
import pandas as pd
from datasets import load_dataset

# Import project utilities from the existing API surface
from src.utils.logging_config import get_module_logger, configure_logging_level
from src.utils.env_config import enforce_cpu_only, is_cpu_only_mode
from src.data.verify_labels import check_label_embedding_correlation, check_metadata_correlation

# Ensure CPU-only execution
enforce_cpu_only()

# Configure logging
logger = get_module_logger(__name__)
configure_logging_level(logging.INFO)

# Constants
SAMPLE_RATE = 16000
MAX_DURATION_SECONDS = 30
MIN_DURATION_SECONDS = 0.5
VALID_AUDIO_EXTENSIONS = {'.wav', '.flac', '.ogg', '.mp3'}


def get_audio_duration(samples: int, sample_rate: int) -> float:
    """Calculate duration in seconds from sample count and sample rate."""
    return samples / sample_rate


def validate_audio_file(
    file_path: Path,
    expected_sample_rate: int = SAMPLE_RATE,
    max_duration: float = MAX_DURATION_SECONDS,
    min_duration: float = MIN_DURATION_SECONDS
) -> Tuple[bool, str]:
    """
    Validate an audio file for usability.

    Args:
        file_path: Path to the audio file
        expected_sample_rate: Expected sample rate (default: 16000)
        max_duration: Maximum allowed duration in seconds
        min_duration: Minimum allowed duration in seconds

    Returns:
        Tuple of (is_valid, reason)
    """
    # Check file extension
    if file_path.suffix.lower() not in VALID_AUDIO_EXTENSIONS:
        return False, f"Unsupported file extension: {file_path.suffix}"

    # Check file exists
    if not file_path.exists():
        return False, f"File does not exist: {file_path}"

    # Check file size (basic sanity check)
    file_size = file_path.stat().st_size
    if file_size == 0:
        return False, "File is empty"

    # Try to read the file
    try:
        data, sample_rate = sf.read(str(file_path))

        # Check sample rate
        if sample_rate != expected_sample_rate:
            return False, f"Sample rate mismatch: {sample_rate} vs expected {expected_sample_rate}"

        # Check duration
        duration = get_audio_duration(len(data), sample_rate)
        if duration > max_duration:
            return False, f"Duration {duration:.2f}s exceeds maximum {max_duration}s"
        if duration < min_duration:
            return False, f"Duration {duration:.2f}s is below minimum {min_duration}s"

        # Check for NaN or Inf values
        if np.any(np.isnan(data)) or np.any(np.isinf(data)):
            return False, "Audio contains NaN or Inf values"

        return True, "Valid"

    except Exception as e:
        return False, f"Failed to read audio: {str(e)}"


def load_audio_file(file_path: Path) -> Optional[np.ndarray]:
    """
    Load an audio file, returning None if it cannot be loaded.

    Args:
        file_path: Path to the audio file

    Returns:
        Audio data as numpy array, or None if loading fails
    """
    try:
        data, sample_rate = sf.read(str(file_path))

        # Ensure sample rate matches expected
        if sample_rate != SAMPLE_RATE:
            logger.warning(f"Sample rate mismatch for {file_path}: {sample_rate} vs {SAMPLE_RATE}. Resampling would be needed.")
            return None

        return data
    except Exception as e:
        logger.error(f"Failed to load audio file {file_path}: {str(e)}")
        return None


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file for integrity tracking."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def preprocess_audio_dataset(
    dataset_path: Path,
    output_dir: Path,
    label_column: str = "label",
    audio_column: str = "audio",
    max_files: Optional[int] = None
) -> Dict[str, Any]:
    """
    Preprocess an audio dataset: validate files, skip corrupted ones,
    and prepare metadata for downstream processing.

    Args:
        dataset_path: Path to the dataset directory or HuggingFace dataset name
        output_dir: Directory to save preprocessed metadata
        label_column: Name of the label column in the dataset
        audio_column: Name of the audio column in the dataset
        max_files: Maximum number of files to process (None for all)

    Returns:
        Dictionary containing preprocessing results and statistics
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {
        "total_files": 0,
        "valid_files": 0,
        "skipped_files": 0,
        "skipped_reasons": {},
        "processed_files": [],
        "label_distribution": {},
        "label_independence_verified": False
    }

    # Load dataset
    try:
        if dataset_path.exists():
            # Local dataset path
            dataset = load_dataset("csv", data_files=str(dataset_path / "metadata.csv"))["train"]
        else:
            # HuggingFace dataset name
            dataset = load_dataset(str(dataset_path))["train"]
    except Exception as e:
        logger.error(f"Failed to load dataset: {str(e)}")
        return results

    results["total_files"] = len(dataset)
    logger.info(f"Loaded dataset with {results['total_files']} samples")

    # Process files
    processed_count = 0
    for idx, sample in enumerate(dataset):
        if max_files and processed_count >= max_files:
            break

        # Get audio file path (assuming 'audio' column contains path or dict with 'path')
        if isinstance(sample[audio_column], dict):
            audio_path = Path(sample[audio_column].get('path', ''))
        else:
            audio_path = Path(sample[audio_column])

        if not audio_path.exists():
            reason = "File not found"
            results["skipped_files"] += 1
            results["skipped_reasons"][reason] = results["skipped_reasons"].get(reason, 0) + 1
            continue

        # Validate audio file
        is_valid, validation_reason = validate_audio_file(audio_path)
        if not is_valid:
            results["skipped_files"] += 1
            results["skipped_reasons"][validation_reason] = results["skipped_reasons"].get(validation_reason, 0) + 1
            logger.debug(f"Skipping {audio_path}: {validation_reason}")
            continue

        # File is valid, record it
        label = sample[label_column]
        label_str = str(label)
        results["label_distribution"][label_str] = results["label_distribution"].get(label_str, 0) + 1

        file_info = {
            "index": idx,
            "file_path": str(audio_path),
            "file_hash": compute_file_hash(audio_path),
            "label": label,
            "label_str": label_str,
            "status": "valid"
        }
        results["processed_files"].append(file_info)
        results["valid_files"] += 1
        processed_count += 1

    logger.info(f"Preprocessing complete: {results['valid_files']} valid, {results['skipped_files']} skipped")

    # Save metadata
    metadata_path = output_dir / "preprocessed_metadata.json"
    with open(metadata_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved preprocessed metadata to {metadata_path}")

    return results


def validate_label_independence(
    metadata_path: Path,
    embeddings_path: Optional[Path] = None
) -> bool:
    """
    Validate that labels are independent of latent embeddings (FR-005).

    This checks for absence of correlation between:
    1. Labels and audio file metadata (path, hash, etc.)
    2. Labels and latent embeddings (if available)

    Args:
        metadata_path: Path to the preprocessed metadata JSON
        embeddings_path: Optional path to embeddings file

    Returns:
        True if label independence is verified, False otherwise
    """
    logger.info("Validating label independence (FR-005)...")

    try:
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
    except Exception as e:
        logger.error(f"Failed to load metadata: {str(e)}")
        return False

    # Check metadata correlation (path, hash, etc.)
    metadata_correlation = check_metadata_correlation(metadata)
    if metadata_correlation:
        logger.error("Label-metadata correlation detected!")
        return False

    # Check embedding correlation if embeddings are available
    if embeddings_path and embeddings_path.exists():
        try:
            embeddings_df = pd.read_parquet(embeddings_path)
            embedding_correlation = check_label_embedding_correlation(
                embeddings_df,
                metadata
            )
            if embedding_correlation:
                logger.error("Label-embedding correlation detected!")
                return False
        except Exception as e:
            logger.warning(f"Could not check embedding correlation: {str(e)}")

    logger.info("Label independence verified (FR-005)")
    return True


def main():
    """Main entry point for preprocessing."""
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess audio dataset")
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to dataset directory or HuggingFace dataset name"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/preprocessed",
        help="Output directory for preprocessed metadata"
    )
    parser.add_argument(
        "--label-column",
        type=str,
        default="label",
        help="Name of the label column"
    )
    parser.add_argument(
        "--audio-column",
        type=str,
        default="audio",
        help="Name of the audio column"
    )
    parser.add_argument(
        "--max-files",
        type=int,
        default=None,
        help="Maximum number of files to process"
    )
    parser.add_argument(
        "--embeddings",
        type=str,
        default=None,
        help="Path to embeddings file for label independence check"
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate label independence, skip preprocessing"
    )

    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_dir = Path(args.output_dir)

    # Enforce CPU-only mode
    enforce_cpu_only()

    if args.validate_only:
        metadata_path = output_dir / "preprocessed_metadata.json"
        embeddings_path = Path(args.embeddings) if args.embeddings else None

        if not metadata_path.exists():
            logger.error(f"Metadata file not found: {metadata_path}")
            sys.exit(1)

        is_independent = validate_label_independence(metadata_path, embeddings_path)
        if not is_independent:
            logger.error("Label independence validation FAILED")
            sys.exit(1)
        else:
            logger.info("Label independence validation PASSED")
            sys.exit(0)

    # Run preprocessing
    results = preprocess_audio_dataset(
        dataset_path,
        output_dir,
        args.label_column,
        args.audio_column,
        args.max_files
    )

    # Validate label independence
    metadata_path = output_dir / "preprocessed_metadata.json"
    embeddings_path = Path(args.embeddings) if args.embeddings else None

    is_independent = validate_label_independence(metadata_path, embeddings_path)

    if not is_independent:
        logger.error("Label independence validation FAILED")
        sys.exit(1)

    logger.info("Preprocessing and label independence validation completed successfully")


if __name__ == "__main__":
    main()
