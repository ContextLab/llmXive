"""
Validator utilities for dataset integrity and schema validation.

This module provides functions for:
- SHA-256 checksum verification of files
- Variable presence validation for fairness analysis datasets

Per Constitution Principle III, all data integrity checks are performed
before any transformation to ensure reproducibility.
"""
import hashlib
from pathlib import Path
from typing import List, Optional, Tuple, Union

import pandas as pd

from utils.logging_utils import log_warning

# FR-008: Findings are associational only; no causal claims are made.

def compute_sha256(file_path: Union[str, Path]) -> str:
    """
    Compute SHA-256 hash of a file.

    This function reads a file in binary mode and computes its SHA-256 hash
    in chunks to handle large files efficiently.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.

    Example:
        >>> hash_val = compute_sha256("data/raw/adult.csv")
        >>> print(hash_val[:16])  # First 16 chars of hash
        'a3f2b8c1d4e5f678...'
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()

def verify_checksum(
    file_path: Union[str, Path], expected_hash: str
) -> Tuple[bool, str]:
    """
    Verify SHA-256 checksum of a file against an expected hash.

    This function computes the SHA-256 hash of a file and compares it
    to the expected hash value. Returns a tuple indicating success and
    a descriptive message.

    Per Constitution Principle III, this verification ensures that data
    files remain unchanged throughout the pipeline.

    Args:
        file_path: Path to the file to verify.
        expected_hash: Expected SHA-256 hash (hex string).

    Returns:
        Tuple of (is_valid: bool, message: str)

    Example:
        >>> is_valid, msg = verify_checksum("data/raw/adult.csv", "abc123...")
        >>> if not is_valid:
        ...     print(f"Checksum mismatch: {msg}")

    Note:
        FR-008: This integrity check supports associational analysis by
        ensuring data provenance.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        actual_hash = compute_sha256(file_path)
    except IOError as e:
        return False, f"Failed to read file: {e}"

    if actual_hash.lower() == expected_hash.lower():
        return True, f"Checksum verified: {actual_hash[:16]}..."
    else:
        return False, (
            f"Checksum mismatch. Expected: {expected_hash[:16]}..., "
            f"Actual: {actual_hash[:16]}..."
        )

def validate_variable_presence(
    df: pd.DataFrame,
    protected_attribute: str,
    outcome: str,
    predictions: Optional[str] = None,
    allowed_protected_values: Optional[List[Union[int, str]]] = None,
) -> Tuple[bool, List[str]]:
    """
    Validate presence of required variables for fairness analysis.

    This function checks that a DataFrame contains the required columns
    for fairness metric computation:
    - Protected attribute (e.g., gender, race)
    - Outcome variable (e.g., loan_approval, recidivism)
    - Predictions (optional, for model-based metrics)

    Args:
        df: pandas DataFrame to validate.
        protected_attribute: Name of the protected attribute column.
        outcome: Name of the outcome variable column.
        predictions: Optional name of the predictions column.
        allowed_protected_values: Optional list of allowed values for
            the protected attribute (e.g., [0, 1] for binary).

    Returns:
        Tuple of (is_valid: bool, errors: List[str])
            - is_valid: True if all required variables are present
            - errors: List of validation error messages (empty if valid)

    Raises:
        TypeError: If df is not a pandas DataFrame.

    Example:
        >>> is_valid, errors = validate_variable_presence(
        ...     df, "gender", "loan_approved", "predictions"
        ... )
        >>> if not is_valid:
        ...     for err in errors:
        ...         print(f"Validation error: {err}")

    Note:
        This validation is required before any fairness metric computation
        to ensure data schema compliance.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")

    errors: List[str] = []

    # Check protected attribute column
    if protected_attribute not in df.columns:
        errors.append(
            f"Protected attribute column '{protected_attribute}' not found. "
            f"Available columns: {list(df.columns)}"
        )
    elif allowed_protected_values is not None:
        unique_values = set(df[protected_attribute].dropna().unique())
        if not unique_values.issubset(set(allowed_protected_values)):
            invalid_vals = unique_values - set(allowed_protected_values)
            errors.append(
                f"Protected attribute '{protected_attribute}' contains "
                f"values outside allowed set: {invalid_vals}. "
                f"Allowed: {allowed_protected_values}"
            )

    # Check outcome column
    if outcome not in df.columns:
        errors.append(
            f"Outcome column '{outcome}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    # Check predictions column (optional)
    if predictions is not None and predictions not in df.columns:
        errors.append(
            f"Predictions column '{predictions}' not found. "
            f"Available columns: {list(df.columns)}"
        )

    is_valid = len(errors) == 0
    if not is_valid:
        log_warning(f"Variable validation failed: {errors}")

    return is_valid, errors

def get_required_columns(
    include_predictions: bool = False
) -> List[str]:
    """
    Get list of required column names for fairness analysis.

    Args:
        include_predictions: Whether to include predictions in required columns.

    Returns:
        List of required column names.

    Example:
        >>> cols = get_required_columns(include_predictions=True)
        >>> print(cols)
        ['protected_attribute', 'outcome', 'predictions']
    """
    required = ["protected_attribute", "outcome"]
    if include_predictions:
        required.append("predictions")
    return required