"""Data loading and hygiene module for UCI datasets.

Provides functions to fetch, load, and clean datasets from the UCI repository,
ensuring data quality, consistency, and integrity for statistical analysis.
"""
import pandas as pd
import numpy as np
from typing import List, Tuple, Optional, Dict, Any
import requests
from io import StringIO
import os
import hashlib
import json

# Constants
UCI_BASE_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases"
VALIDATION_THRESHOLD = 3  # Minimum number of valid datasets required
CHECKSUM_FILE = "data/raw/checksums.json"

def _calculate_sha256(file_path: str) -> str:
    """Calculate SHA256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal SHA256 hash string.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def _load_checksums() -> Dict[str, str]:
    """Load stored checksums from disk.

    Returns:
        Dictionary mapping dataset identifiers to their SHA256 hashes.
    """
    if not os.path.exists(CHECKSUM_FILE):
        return {}
    try:
        with open(CHECKSUM_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _save_checksums(checksums: Dict[str, str]) -> None:
    """Save checksums to disk.

    Args:
        checksums: Dictionary mapping dataset identifiers to SHA256 hashes.
    """
    os.makedirs(os.path.dirname(CHECKSUM_FILE), exist_ok=True)
    with open(CHECKSUM_FILE, 'w') as f:
        json.dump(checksums, f, indent=2)

def _verify_checksum(dataset_identifier: str, file_path: str) -> bool:
    """Verify file integrity against stored checksum.

    Args:
        dataset_identifier: Unique identifier for the dataset.
        file_path: Path to the downloaded file.

    Returns:
        True if checksum matches or is new, False if mismatch.

    Raises:
        ValueError: If checksum mismatch detected (Constitution I compliance).
    """
    stored_checksums = _load_checksums()
    current_hash = _calculate_sha256(file_path)

    if dataset_identifier in stored_checksums:
        if stored_checksums[dataset_identifier] != current_hash:
            raise ValueError(
                f"Checksum mismatch for dataset '{dataset_identifier}'. "
                f"Expected: {stored_checksums[dataset_identifier]}, "
                f"Got: {current_hash}. Data integrity compromised."
            )
        return True
    else:
        # New dataset, store the checksum
        stored_checksums[dataset_identifier] = current_hash
        _save_checksums(stored_checksums)
        return True

def fetch_uci_dataset(dataset_name: str, filename: str) -> Optional[pd.DataFrame]:
    """Fetch a dataset from the UCI repository and verify integrity.

    Args:
        dataset_name: Name of the dataset directory at UCI.
        filename: Name of the CSV file within the dataset directory.

    Returns:
        DataFrame containing the dataset, or None if fetch fails.

    Raises:
        FileNotFoundError: If the dataset URL is invalid or file not found.
        ValueError: If the download fails or checksum verification fails.
    """
    url = f"{UCI_BASE_URL}/{dataset_name}/{filename}"
    dataset_identifier = f"{dataset_name}/{filename}"
    temp_path = f"data/raw/{dataset_name}_{filename}"

    # Ensure data/raw directory exists
    os.makedirs("data/raw", exist_ok=True)

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # Write to temporary file for checksumming
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(response.text)

        # Verify integrity via checksum
        _verify_checksum(dataset_identifier, temp_path)

        # Load into DataFrame
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        return df

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            raise FileNotFoundError(f"Dataset not found at URL: {url}") from e
        raise ValueError(f"Failed to download dataset: {e}") from e
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Network error while fetching dataset: {e}") from e
    except ValueError as e:
        # Re-raise checksum errors as-is
        raise e
    finally:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)

def load_dataset_from_path(file_path: str) -> pd.DataFrame:
    """Load a dataset from a local file path and verify integrity.

    Args:
        file_path: Path to the CSV file.

    Returns:
        DataFrame containing the dataset.

    Raises:
        ValueError: If checksum verification fails.
    """
    dataset_identifier = os.path.basename(file_path)
    
    # Verify checksum if stored exists
    stored_checksums = _load_checksums()
    if dataset_identifier in stored_checksums:
        current_hash = _calculate_sha256(file_path)
        if stored_checksums[dataset_identifier] != current_hash:
            raise ValueError(
                f"Checksum mismatch for file '{file_path}'. "
                f"Expected: {stored_checksums[dataset_identifier]}, "
                f"Got: {current_hash}. Data integrity compromised."
            )
    else:
        # Store checksum for future verification
        stored_checksums[dataset_identifier] = _calculate_sha256(file_path)
        _save_checksums(stored_checksums)

    return pd.read_csv(file_path)

def drop_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """Drop rows with any missing values.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with rows containing missing values removed.
    """
    return df.dropna()

def detect_constant_variables(df: pd.DataFrame) -> List[str]:
    """Identify variables with zero variance (constant values).

    Args:
        df: Input DataFrame.

    Returns:
        List of column names that are constant.
    """
    constant_vars = []
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].nunique() == 1:
                constant_vars.append(col)
    return constant_vars

def exclude_constant_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Remove constant variables from the DataFrame.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with constant variables removed.
    """
    constant_vars = detect_constant_variables(df)
    return df.drop(columns=constant_vars, errors='ignore')

def filter_continuous_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only continuous (numeric) variables.

    Args:
        df: Input DataFrame.

    Returns:
        DataFrame with only numeric columns.
    """
    return df.select_dtypes(include=[np.number])

def validate_dataset_dimensions(df: pd.DataFrame, min_vars: int = 20) -> bool:
    """Check if the dataset has sufficient continuous variables.

    Args:
        df: Input DataFrame.
        min_vars: Minimum required number of continuous variables.

    Returns:
        True if the dataset meets the requirement, False otherwise.
    """
    return len(df.columns) >= min_vars

def apply_hygiene_pipeline(df: pd.DataFrame, min_vars: int = 20) -> Optional[pd.DataFrame]:
    """Apply a full hygiene pipeline to a dataset.

    Steps:
    1. Drop rows with missing values.
    2. Filter to continuous variables only.
    3. Exclude constant variables.
    4. Validate dimension requirements.

    Args:
        df: Input DataFrame.
        min_vars: Minimum required number of continuous variables.

    Returns:
        Cleaned DataFrame if valid, None otherwise.
    """
    # Drop missing values
    df_clean = drop_missing_values(df)

    if df_clean.empty:
        return None

    # Filter continuous variables
    df_continuous = filter_continuous_variables(df_clean)

    if df_continuous.empty:
        return None

    # Exclude constant variables
    df_final = exclude_constant_variables(df_continuous)

    if df_final.empty:
        return None

    # Validate dimensions
    if not validate_dataset_dimensions(df_final, min_vars):
        return None

    return df_final

def load_and_hygiene_dataset(
    dataset_name: str, filename: str, min_vars: int = 20
) -> Optional[pd.DataFrame]:
    """Fetch, verify integrity, and apply hygiene pipeline to a UCI dataset.

    Args:
        dataset_name: Name of the dataset directory at UCI.
        filename: Name of the CSV file within the dataset directory.
        min_vars: Minimum required number of continuous variables.

    Returns:
        Cleaned DataFrame if valid, None otherwise.

    Raises:
        ValueError: If checksum verification fails.
    """
    df = fetch_uci_dataset(dataset_name, filename)
    if df is None:
        return None
    return apply_hygiene_pipeline(df, min_vars)
