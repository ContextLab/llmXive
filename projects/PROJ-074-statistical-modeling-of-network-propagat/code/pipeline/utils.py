"""
Pipeline utility functions for the Bayesian Hierarchical Modeling of Misinformation Cascade Size project.

This module provides core infrastructure for:
- Logging setup and configuration
- Random seed initialization for reproducibility
- SHA-256 checksum computation for data integrity
- Timestamp normalization to UTC
- Cascade data loading and validation from JSON edge-list files
"""

import hashlib
import json
import logging
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ============================================================================
# Logging Infrastructure (T006)
# ============================================================================


def setup_logger(
    name: str = "pipeline",
    log_file: Optional[str] = "pipeline.log",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    Set up and return a logger with console and file handlers.

    Args:
        name: Logger name (default: "pipeline")
        log_file: Path to log file (default: "pipeline.log" in current directory)
        level: Logging level (default: logging.INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


# ============================================================================
# Random Seed Initialization (T060)
# ============================================================================


def set_global_seed(seed: int = 12345) -> None:
    """
    Set global random seeds for reproducibility across libraries.

    This function ensures consistent results by pinning seeds for:
    - Python's random module
    - NumPy
    - PyTorch (if available)

    Args:
        seed: Integer seed value (default: 12345)
    """
    random.seed(seed)
    np.random.seed(seed)

    # Set PyTorch seed if available
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    # Set NumPyro seed if available
    try:
        import numpyro

        numpyro.set_rng_seed(seed)
    except ImportError:
        pass


# ============================================================================
# Checksum Computation (T061)
# ============================================================================


def compute_checksum(path: str) -> str:
    """
    Compute SHA-256 checksum for a file.

    Args:
        path: Path to the file

    Returns:
        Hexadecimal string of SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


# ============================================================================
# Timestamp Normalization (T070)
# ============================================================================


def normalize_timestamp(
    timestamp: Any, input_format: Optional[str] = None
) -> str:
    """
    Normalize a timestamp to UTC ISO 8601 format.

    Args:
        timestamp: Timestamp value (string, datetime, or numeric)
        input_format: Optional format string for parsing (e.g., "%Y-%m-%d %H:%M:%S")

    Returns:
        Timestamp string in ISO 8601 UTC format (e.g., "2024-01-15T10:30:00Z")

    Raises:
        ValueError: If timestamp cannot be parsed or normalized
    """
    dt: datetime

    # Handle None
    if timestamp is None:
        raise ValueError("Timestamp cannot be None")

    # Already a datetime object
    if isinstance(timestamp, datetime):
        dt = timestamp
    # String timestamp
    elif isinstance(timestamp, str):
        # Try ISO format first
        try:
            # Handle various ISO formats
            if "T" in timestamp:
                # ISO format with timezone
                if timestamp.endswith("Z"):
                    timestamp = timestamp[:-1] + "+00:00"
                dt = datetime.fromisoformat(timestamp)
            else:
                # Try common formats
                for fmt in [
                    "%Y-%m-%d %H:%M:%S",
                    "%Y-%m-%dT%H:%M:%S",
                    "%Y-%m-%d",
                    "%d/%m/%Y %H:%M:%S",
                    "%m/%d/%Y %H:%M:%S",
                ]:
                    try:
                        dt = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    raise ValueError(f"Unable to parse timestamp: {timestamp}")
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Unable to parse timestamp '{timestamp}': {e}")
    # Numeric timestamp (Unix epoch)
    elif isinstance(timestamp, (int, float)):
        dt = datetime.utcfromtimestamp(timestamp)
    else:
        raise ValueError(f"Unsupported timestamp type: {type(timestamp)}")

    # Convert to UTC if timezone-aware
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc)
    else:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)

    # Return ISO 8601 format with Z suffix
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ============================================================================
# Cascade Loading and Validation (T080)
# ============================================================================


def load_cascade(
    file_path: str,
    logger: Optional[logging.Logger] = None,
    required_columns: Optional[List[str]] = None,
) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """
    Load and validate a cascade from a JSON edge-list file.

    This function implements T080 requirements:
    - Accepts JSON edge-list files only
    - Validates required columns (node_id, timestamp, cascade_id)
    - Normalizes timestamps to UTC
    - Logs validation errors

    Args:
        file_path: Path to the JSON edge-list file
        logger: Logger instance (creates default if None)
        required_columns: List of required column names (default: ["node_id", "timestamp", "cascade_id"])

    Returns:
        Tuple of (DataFrame or None if invalid, list of validation errors)

    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    if logger is None:
        logger = setup_logger()

    if required_columns is None:
        required_columns = ["node_id", "timestamp", "cascade_id"]

    errors: List[str] = []
    file_path_obj = Path(file_path)

    # Validate file extension (JSON only)
    if file_path_obj.suffix.lower() not in [".json"]:
        errors.append(
            f"File '{file_path}' is not a JSON file. Only .json files are accepted."
        )
        logger.error(errors[-1])
        return None, errors

    # Check file exists
    if not file_path_obj.exists():
        errors.append(f"File '{file_path}' does not exist.")
        logger.error(errors[-1])
        return None, errors

    # Load JSON
    try:
        with open(file_path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in '{file_path}': {e}")
        logger.error(errors[-1])
        return None, errors

    # Handle different JSON structures
    # Expected formats:
    # 1. List of edge records: [{"node_id": "...", "timestamp": "...", "cascade_id": "..."}, ...]
    # 2. Dict with "edges" key: {"edges": [...], ...}
    # 3. Dict with cascade_id as key: {"cascade_id": {...}}

    if isinstance(data, list):
        # Format 1: Direct list of records
        records = data
    elif isinstance(data, dict):
        if "edges" in data:
            # Format 2: Dict with edges key
            records = data["edges"]
        elif "nodes" in data:
            # Format 3: Nodes as records
            records = data["nodes"]
        else:
            # Try to find list value
            for key, value in data.items():
                if isinstance(value, list) and len(value) > 0:
                    records = value
                    break
            else:
                errors.append(
                    f"Cannot determine edge list structure in '{file_path}'. "
                    f"Expected list of records or dict with 'edges' key."
                )
                logger.error(errors[-1])
                return None, errors
    else:
        errors.append(
            f"Unexpected JSON structure in '{file_path}'. Expected list or dict."
        )
        logger.error(errors[-1])
        return None, errors

    if len(records) == 0:
        errors.append(f"Empty cascade data in '{file_path}'.")
        logger.warning(errors[-1])
        return None, errors

    # Convert to DataFrame
    try:
        df = pd.DataFrame(records)
    except Exception as e:
        errors.append(f"Failed to convert records to DataFrame: {e}")
        logger.error(errors[-1])
        return None, errors

    # Validate required columns exist
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        error_msg = (
            f"Missing required columns in '{file_path}': {missing_columns}. "
            f"Required columns: {required_columns}."
        )
        errors.append(error_msg)
        logger.error(error_msg)
        return None, errors

    # Validate column data types and normalize timestamps
    validated_records = []
    for idx, record in enumerate(df.to_dict("records")):
        record_errors = []

        # Validate node_id
        node_id = record.get("node_id")
        if node_id is None or (isinstance(node_id, str) and node_id.strip() == ""):
            record_errors.append(f"Record {idx}: node_id is missing or empty")

        # Validate cascade_id
        cascade_id = record.get("cascade_id")
        if cascade_id is None or (
            isinstance(cascade_id, str) and cascade_id.strip() == ""
        ):
            record_errors.append(f"Record {idx}: cascade_id is missing or empty")

        # Normalize timestamp
        timestamp = record.get("timestamp")
        try:
            normalized_ts = normalize_timestamp(timestamp)
            record["timestamp"] = normalized_ts
        except ValueError as e:
            record_errors.append(f"Record {idx}: timestamp validation failed - {e}")

        if record_errors:
            errors.extend(record_errors)
            logger.warning(f"Validation errors in '{file_path}': {record_errors}")
        else:
            validated_records.append(record)

    # Check if any records passed validation
    if len(validated_records) == 0:
        errors.append(f"No valid records in '{file_path}'.")
        logger.error(errors[-1])
        return None, errors

    # Return validated DataFrame
    result_df = pd.DataFrame(validated_records)
    logger.info(
        f"Successfully loaded {len(result_df)} records from '{file_path}' "
        f"({len(errors)} validation warnings)."
    )

    return result_df, errors


def validate_all_cascades(
    data_dir: str,
    logger: Optional[logging.Logger] = None,
    required_columns: Optional[List[str]] = None,
) -> Tuple[Dict[str, pd.DataFrame], Dict[str, List[str]]]:
    """
    Validate all JSON cascade files in a directory.

    Args:
        data_dir: Path to directory containing JSON cascade files
        logger: Logger instance
        required_columns: Required column names

    Returns:
        Tuple of (dict of valid DataFrames by filename, dict of errors by filename)
    """
    if logger is None:
        logger = setup_logger()

    if required_columns is None:
        required_columns = ["node_id", "timestamp", "cascade_id"]

    data_path = Path(data_dir)
    if not data_path.exists():
        logger.error(f"Data directory '{data_dir}' does not exist.")
        return {}, {}

    valid_cascades: Dict[str, pd.DataFrame] = {}
    all_errors: Dict[str, List[str]] = {}

    json_files = list(data_path.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files in '{data_dir}'.")

    for json_file in json_files:
        df, errors = load_cascade(str(json_file), logger, required_columns)
        if df is not None:
            valid_cascades[json_file.name] = df
        all_errors[json_file.name] = errors

    logger.info(
        f"Validated {len(valid_cascades)} of {len(json_files)} cascades."
    )

    return valid_cascades, all_errors


def validate_features(
    features_df: pd.DataFrame,
    logger: Optional[logging.Logger] = None,
    required_columns: Optional[List[str]] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate a features DataFrame against schema requirements.

    Args:
        features_df: Features DataFrame to validate
        logger: Logger instance
        required_columns: List of required column names

    Returns:
        Tuple of (is_valid, list of validation errors)
    """
    if logger is None:
        logger = setup_logger()

    if required_columns is None:
        required_columns = []

    errors: List[str] = []

    # Check for missing values
    if features_df.isnull().any().any():
        missing_cols = features_df.columns[features_df.isnull().any()].tolist()
        errors.append(f"Missing values found in columns: {missing_cols}")
        logger.warning(errors[-1])

    # Check required columns
    if required_columns:
        missing = [col for col in required_columns if col not in features_df.columns]
        if missing:
            errors.append(f"Missing required columns: {missing}")
            logger.error(errors[-1])

    # Check for empty DataFrame
    if features_df.empty:
        errors.append("Features DataFrame is empty.")
        logger.error(errors[-1])

    is_valid = len(errors) == 0
    if is_valid:
        logger.info("Features validation passed.")
    else:
        logger.warning(f"Features validation failed with {len(errors)} errors.")

    return is_valid, errors


# ============================================================================
# Main Entry Point (for testing)
# ============================================================================


def main() -> None:
    """
    Main entry point for standalone execution and testing.
    """
    # Set up logger
    logger = setup_logger()
    set_global_seed(12345)

    logger.info("Pipeline utilities module loaded successfully.")
    logger.info("Available functions: setup_logger, set_global_seed, compute_checksum, "
               "normalize_timestamp, load_cascade, validate_all_cascades, validate_features")

    # Example: Test checksum computation
    test_path = Path(__file__)
    if test_path.exists():
        checksum = compute_checksum(str(test_path))
        logger.info(f"Checksum of this file: {checksum[:16]}...")


if __name__ == "__main__":
    main()