"""
I/O Helpers for strict CSV/Parquet I/O and checksum verification.

This module provides robust functions for reading and writing data
with integrity checks, adhering to the project's data contracts.
"""
import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Optional, Union, Dict, Any, Literal

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from src.config.constants import PROJECT_ROOT
from src.config.schemas import validate_dataset_schema, validate_regression_output

# Configure logging
logger = logging.getLogger(__name__)

# Supported checksum algorithms
CHECKSUM_ALGORITHMS = {'md5', 'sha256'}


class IntegrityError(Exception):
    """Raised when data integrity checks fail."""
    pass


class FatalError(Exception):
    """Raised for unrecoverable errors (e.g., missing real data)."""
    pass


def _calculate_checksum(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use ('md5' or 'sha256').

    Returns:
        Hexadecimal digest of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if algorithm not in CHECKSUM_ALGORITHMS:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Use {CHECKSUM_ALGORITHMS}.")

    hasher = hashlib.new(algorithm)
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found for checksum calculation: {path}")

    with open(path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


def _verify_checksum(file_path: Union[str, Path], expected_checksum: str, algorithm: str = 'sha256') -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file.
        expected_checksum: Expected hexadecimal checksum.
        algorithm: Hash algorithm used for the expected checksum.

    Returns:
        True if checksums match.

    Raises:
        IntegrityError: If checksums do not match.
    """
    actual_checksum = _calculate_checksum(file_path, algorithm)
    if actual_checksum != expected_checksum:
        raise IntegrityError(
            f"Checksum mismatch for {file_path}.\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}"
        )
    return True


def read_csv_strict(
    path: Union[str, Path],
    checksum: Optional[str] = None,
    algorithm: str = 'sha256',
    schema_validation: bool = True
) -> pd.DataFrame:
    """
    Read a CSV file with optional checksum verification and schema validation.

    Args:
        path: Path to the CSV file.
        checksum: Expected checksum. If provided, the file is verified before loading.
        algorithm: Hash algorithm for checksum verification.
        schema_validation: If True, validate against dataset schema.

    Returns:
        Loaded DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        IntegrityError: If checksum verification fails.
        ValueError: If schema validation fails.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")

    if checksum:
        logger.info(f"Verifying checksum for {path}...")
        _verify_checksum(path, checksum, algorithm)

    try:
        df = pd.read_csv(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read CSV {path}: {e}")

    if schema_validation:
        # Validate against the expected dataset schema
        # Assuming the schema is defined in contracts/dataset.schema.yaml
        # and we have a validator function available
        try:
            # This is a placeholder for actual schema validation logic
            # In a real implementation, we would load the schema from YAML
            # and validate the DataFrame columns and types
            validate_dataset_schema(df)
        except Exception as e:
            raise ValueError(f"Schema validation failed for {path}: {e}")

    logger.info(f"Successfully loaded {path} with {len(df)} rows.")
    return df


def write_csv_strict(
    df: pd.DataFrame,
    path: Union[str, Path],
    checksum_path: Optional[Union[str, Path]] = None,
    algorithm: str = 'sha256'
) -> Dict[str, str]:
    """
    Write a DataFrame to CSV with optional checksum generation.

    Args:
        df: DataFrame to write.
        path: Output path for the CSV file.
        checksum_path: Optional path to save the checksum file (.checksum).
        algorithm: Hash algorithm to use for checksum.

    Returns:
        Dictionary containing 'path' and 'checksum'.

    Raises:
        IOError: If writing fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df.to_csv(path, index=False)
    except Exception as e:
        raise IOError(f"Failed to write CSV to {path}: {e}")

    checksum_value = _calculate_checksum(path, algorithm)

    result = {
        'path': str(path),
        'checksum': checksum_value,
        'algorithm': algorithm
    }

    if checksum_path:
        checksum_path = Path(checksum_path)
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checksum_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Checksum saved to {checksum_path}")

    logger.info(f"Successfully wrote {len(df)} rows to {path}.")
    return result


def read_parquet_strict(
    path: Union[str, Path],
    checksum: Optional[str] = None,
    algorithm: str = 'sha256',
    schema_validation: bool = True
) -> pd.DataFrame:
    """
    Read a Parquet file with optional checksum verification and schema validation.

    Args:
        path: Path to the Parquet file.
        checksum: Expected checksum. If provided, the file is verified before loading.
        algorithm: Hash algorithm for checksum verification.
        schema_validation: If True, validate against dataset schema.

    Returns:
        Loaded DataFrame.

    Raises:
        FileNotFoundError: If the file does not exist.
        IntegrityError: If checksum verification fails.
        ValueError: If schema validation fails.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")

    if checksum:
        logger.info(f"Verifying checksum for {path}...")
        _verify_checksum(path, checksum, algorithm)

    try:
        df = pd.read_parquet(path)
    except Exception as e:
        raise RuntimeError(f"Failed to read Parquet {path}: {e}")

    if schema_validation:
        try:
            validate_dataset_schema(df)
        except Exception as e:
            raise ValueError(f"Schema validation failed for {path}: {e}")

    logger.info(f"Successfully loaded {path} with {len(df)} rows.")
    return df


def write_parquet_strict(
    df: pd.DataFrame,
    path: Union[str, Path],
    checksum_path: Optional[Union[str, Path]] = None,
    algorithm: str = 'sha256'
) -> Dict[str, str]:
    """
    Write a DataFrame to Parquet with optional checksum generation.

    Args:
        df: DataFrame to write.
        path: Output path for the Parquet file.
        checksum_path: Optional path to save the checksum file (.checksum).
        algorithm: Hash algorithm to use for checksum.

    Returns:
        Dictionary containing 'path' and 'checksum'.

    Raises:
        IOError: If writing fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Write to Parquet using PyArrow
        table = pa.Table.from_pandas(df)
        pq.write_table(table, path)
    except Exception as e:
        raise IOError(f"Failed to write Parquet to {path}: {e}")

    checksum_value = _calculate_checksum(path, algorithm)

    result = {
        'path': str(path),
        'checksum': checksum_value,
        'algorithm': algorithm
    }

    if checksum_path:
        checksum_path = Path(checksum_path)
        checksum_path.parent.mkdir(parents=True, exist_ok=True)
        with open(checksum_path, 'w') as f:
            json.dump(result, f, indent=2)
        logger.info(f"Checksum saved to {checksum_path}")

    logger.info(f"Successfully wrote {len(df)} rows to {path}.")
    return result


def load_json_strict(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON file with error handling.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON data as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in {path}: {e.msg}", e.doc, e.pos)


def write_json_strict(data: Dict[str, Any], path: Union[str, Path]) -> None:
    """
    Write data to a JSON file.

    Args:
        data: Data to write.
        path: Output path for the JSON file.

    Raises:
        IOError: If writing fails.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        raise IOError(f"Failed to write JSON to {path}: {e}")

    logger.info(f"Successfully wrote JSON to {path}.")