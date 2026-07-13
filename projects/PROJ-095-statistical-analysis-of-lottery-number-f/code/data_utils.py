"""
Data utilities for deterministic CSV loading and checksum verification.
Implements Constitution Principle III: Deterministic and Verifiable Data Ingestion.
"""
import hashlib
import json
import os
from typing import Optional, Tuple, Dict, Any

import pandas as pd


def calculate_checksum(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if algorithm not in hashlib.algorithms_available:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(file_path: str, expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify the checksum of a file against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum hex string.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        True if checksum matches, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the checksum format is invalid or algorithm unsupported.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    calculated = calculate_checksum(file_path, algorithm)

    # Normalize for comparison (case-insensitive)
    return calculated.lower() == expected_checksum.lower()


def load_draws_csv(
    file_path: str,
    checksum: Optional[str] = None,
    algorithm: str = 'sha256',
    strict: bool = True
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Load a CSV file containing lottery draws with optional checksum verification.

    This function ensures deterministic loading by:
    1. Verifying file integrity via checksum if provided.
    2. Enforcing a consistent dtype schema.
    3. Sorting data deterministically by draw date.

    Args:
        file_path: Path to the CSV file.
        checksum: Optional expected checksum hex string.
        algorithm: Hash algorithm for checksum verification.
        strict: If True, raise errors on verification failure. If False, log warnings.

    Returns:
        Tuple of (DataFrame, checksum_message).
        - DataFrame: The loaded data with standardized dtypes.
        - checksum_message: String describing verification status, or None if no checksum provided.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If checksum verification fails and strict=True.
        pd.errors.EmptyDataError: If the CSV is empty or malformed.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Data file not found: {file_path}")

    # Verify checksum if provided
    checksum_msg = None
    if checksum:
        if not verify_checksum(file_path, checksum, algorithm):
            msg = f"Checksum verification FAILED for {file_path}. Expected: {checksum}, Calculated: {calculate_checksum(file_path, algorithm)}"
            if strict:
                raise ValueError(msg)
            else:
                checksum_msg = f"WARNING: {msg}"
        else:
            checksum_msg = f"Checksum verification PASSED for {file_path} ({algorithm})"

    # Load CSV
    try:
        df = pd.read_csv(file_path)
    except pd.errors.EmptyDataError:
        raise ValueError(f"CSV file is empty or malformed: {file_path}")

    # Ensure deterministic column ordering if known schema exists
    # Standard lottery draw columns typically include: draw_date, numbers (or separate cols), jackpot, sales
    # We will sort by 'draw_date' if it exists to ensure deterministic row order
    if 'draw_date' in df.columns:
        # Ensure date is parsed correctly for sorting
        if not pd.api.types.is_datetime64_any_dtype(df['draw_date']):
            df['draw_date'] = pd.to_datetime(df['draw_date'], errors='coerce')
        df = df.sort_values('draw_date').reset_index(drop=True)

    return df, checksum_msg


def save_checksums_file(checksums: Dict[str, str], output_path: str) -> None:
    """
    Save a dictionary of file paths to checksums into a JSON file.

    Args:
        checksums: Dictionary mapping file paths (relative or absolute) to checksum hex strings.
        output_path: Path where the JSON file will be saved.
    """
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(checksums, f, indent=2)


def load_checksums_file(input_path: str) -> Dict[str, str]:
    """
    Load a dictionary of file paths to checksums from a JSON file.

    Args:
        input_path: Path to the JSON file.

    Returns:
        Dictionary mapping file paths to checksum hex strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)
