"""
Z-Reward Dataset Download Module.

This module handles the fetching of the Z-Reward evaluation dataset.
It attempts to load the dataset from verified HuggingFace sources.
If the real dataset is unavailable, it raises a RuntimeError to fail loudly,
ensuring no synthetic data is silently used in the pipeline.
"""
import argparse
import csv
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

# Attempt to import datasets; if missing, we fail loudly at runtime
try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' package is required. "
        "Please install it via: pip install datasets"
    )

import pandas as pd

# Project root path (relative to where this script is run)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Expected columns for the Z-Reward dataset based on the spec
EXPECTED_COLUMNS = [
    "prompt",
    "image_url",
    "teacher_scores",
    "student_scalar",
    "human_annotations",
    "primary_dimension"
]

# Rubric dimensions required in teacher_scores and human_annotations
RUBRIC_DIMENSIONS = ["Alignment", "Realism", "Aesthetics", "Plausibility"]


def setup_logging() -> logging.Logger:
    """Configure logging for the download module."""
    logger = logging.getLogger("download_zreward")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def save_checksum(file_path: Path, checksum: str, checksum_file: Path) -> None:
    """Save the checksum to a JSON file."""
    with open(checksum_file, "w") as f:
        json.dump({"file": file_path.name, "sha256": checksum}, f, indent=2)


def verify_checksum(file_path: Path, checksum_file: Path) -> bool:
    """Verify the file checksum against a stored value."""
    if not checksum_file.exists():
        return False
    with open(checksum_file, "r") as f:
        data = json.load(f)
    stored_checksum = data.get("sha256")
    if not stored_checksum:
        return False
    current_checksum = calculate_sha256(file_path)
    return current_checksum == stored_checksum


def validate_columns(df: pd.DataFrame, logger: logging.Logger) -> bool:
    """
    Validate that the dataframe contains the required columns.
    Returns True if valid, raises RuntimeError otherwise.
    """
    missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_cols:
        error_msg = (
            f"Dataset missing required columns: {missing_cols}. "
            f"Expected: {EXPECTED_COLUMNS}. "
            f"Found: {list(df.columns)}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Validate teacher_scores structure if it's a dict-like column
    if "teacher_scores" in df.columns:
        # Check first non-null row
        sample = df["teacher_scores"].dropna().iloc[0] if len(df) > 0 else None
        if isinstance(sample, dict):
            missing_dims = [d for d in RUBRIC_DIMENSIONS if d not in sample]
            if missing_dims:
                error_msg = (
                    f"teacher_scores missing required dimensions: {missing_dims}. "
                    f"Expected: {RUBRIC_DIMENSIONS}"
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            error_msg = "teacher_scores column is not a dictionary type."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

    return True


def download_dataset(
    dataset_name: str = "Z-Reward",
    output_path: Optional[Path] = None,
    logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """
    Download the Z-Reward dataset from a verified source.
    
    This function attempts to load the dataset using the HuggingFace `datasets` library.
    It prioritizes verified sources. If the dataset is not found or invalid,
    it raises a RuntimeError immediately (no synthetic fallback).
    
    Args:
        dataset_name: Name of the dataset to load.
        output_path: Optional path to save the raw parquet file.
        logger: Logger instance.
    
    Returns:
        pd.DataFrame: The loaded dataset.
    
    Raises:
        RuntimeError: If the dataset cannot be loaded or validated.
        ImportError: If the `datasets` library is not installed.
    """
    if logger is None:
        logger = setup_logging()

    logger.info(f"Attempting to download dataset: {dataset_name}")
    
    # Ensure output directories exist
    DATA_RAW_DIR.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Verified Source Strategy:
    # 1. Try to load 'Z-Reward' directly.
    # 2. If that fails, try specific known IDs if available (e.g., 'z-reward/z-reward').
    #    Since the prompt implies a specific 'Z-Reward' dataset, we try variations.
    
    possible_ids = [
        "Z-Reward", 
        "z-reward/z-reward",
        "z-reward/evaluation",
        # Add other potential IDs if known, but we stick to the primary request
    ]

    ds = None
    last_error = None

    for ds_id in possible_ids:
        try:
            logger.info(f"Trying to load dataset ID: {ds_id}")
            # Use streaming=False to load into memory for validation
            # If the dataset is too large, we might need streaming=True and chunking,
            # but for initial validation of the schema, we try to load a slice or the whole thing.
            # Given the constraint of ~7GB RAM, we try to load the dataset.
            # If it's huge, we might need to use 'split' or limit rows.
            # For now, we assume it's loadable or we catch the error.
            ds = load_dataset(ds_id, split="train")
            logger.info(f"Successfully loaded dataset from: {ds_id}")
            break
        except Exception as e:
            last_error = e
            logger.warning(f"Failed to load {ds_id}: {e}")
            continue

    if ds is None:
        error_msg = (
            f"Failed to load Z-Reward dataset from any verified source. "
            f"Tried: {possible_ids}. "
            f"Last error: {last_error}. "
            "Cannot proceed without real data. No synthetic fallback allowed."
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Convert to DataFrame
    try:
        df = ds.to_pandas()
    except Exception as e:
        error_msg = f"Failed to convert dataset to pandas DataFrame: {e}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # Validate columns
    validate_columns(df, logger)

    # Save to parquet if output_path is provided
    if output_path is None:
        output_path = DATA_RAW_DIR / "zreward_raw.parquet"
    
    logger.info(f"Saving dataset to: {output_path}")
    df.to_parquet(output_path, index=False)

    # Calculate and save checksum
    checksum = calculate_sha256(output_path)
    checksum_file = DATA_RAW_DIR / "zreward_raw.parquet.sha256"
    save_checksum(output_path, checksum, checksum_file)
    logger.info(f"Checksum saved: {checksum}")

    logger.info("Dataset download and validation completed successfully.")
    return df


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Download and validate the Z-Reward evaluation dataset."
    )
    parser.add_argument(
        "--dataset-name",
        type=str,
        default="Z-Reward",
        help="Name of the dataset to load (default: Z-Reward)"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to save the raw parquet file (default: data/raw/zreward_raw.parquet)"
    )
    return parser.parse_args()


def main() -> None:
    """Main entry point for the download script."""
    args = parse_args()
    logger = setup_logging()
    
    output_path = Path(args.output_path) if args.output_path else None
    
    try:
        df = download_dataset(
            dataset_name=args.dataset_name,
            output_path=output_path,
            logger=logger
        )
        logger.info(f"Downloaded {len(df)} rows.")
    except RuntimeError as e:
        logger.error(f"Critical Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
