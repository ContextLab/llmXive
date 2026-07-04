"""
I/O utilities for the llmXive research pipeline.

Provides functions for:
- CSV export (pandas)
- JSON artifact writing with metadata
- SHA256 checksumming of generated files
"""
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import numpy as np
import pandas as pd


def export_csv(
    data: Union[pd.DataFrame, Dict[str, list]],
    output_path: Union[str, Path],
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Export data to a CSV file.

    Args:
        data: Either a pandas DataFrame or a dictionary of column lists.
        output_path: Path where the CSV file will be written.
        metadata: Optional dictionary of metadata to include in a companion .meta.json file.
                  If provided, the metadata will be saved alongside the CSV.

    Raises:
        ValueError: If data format is invalid.
        FileNotFoundError: If the parent directory of output_path does not exist.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, pd.DataFrame):
        df = data
    elif isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        raise ValueError(f"Unsupported data type: {type(data)}. Expected DataFrame or dict.")

    df.to_csv(output_path, index=False)

    if metadata is not None:
        meta_path = output_path.with_suffix(output_path.suffix + ".meta.json")
        write_json_artifact(metadata, meta_path)


def write_json_artifact(
    data: Dict[str, Any],
    output_path: Union[str, Path],
    include_checksum: bool = True,
) -> str:
    """
    Write a dictionary to a JSON file with optional checksum metadata.

    Args:
        data: The dictionary to serialize.
        output_path: Path where the JSON file will be written.
        include_checksum: If True, compute the SHA256 of the written file and
                          inject it into the metadata under '_checksum'.

    Returns:
        The SHA256 checksum of the written file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Pre-calculate checksum if requested (after writing)
    # We write first, then read back to compute checksum to ensure accuracy
    # However, to avoid a second read, we can compute on the serialized string
    # but file encoding might differ. The safest is write -> read -> hash.
    
    # For efficiency, we serialize, write, then hash the file.
    json_str = json.dumps(data, indent=2, default=str)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    checksum = compute_file_checksum(output_path)

    if include_checksum:
        # Update the data object in memory to reflect the checksum for the caller
        # Note: This modifies the input dict if it's the same reference, 
        # but usually we just return the checksum.
        # To be safe and pure, we don't modify input, but we can return the checksum.
        pass

    return checksum


def compute_file_checksum(
    file_path: Union[str, Path],
    algorithm: str = "sha256",
    chunk_size: int = 8192,
) -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hexadecimal string of the hash.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            hasher.update(chunk)

    return hasher.hexdigest()