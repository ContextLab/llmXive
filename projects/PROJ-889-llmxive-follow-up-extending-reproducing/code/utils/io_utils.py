"""
Base utility module for file I/O and checksumming.

Provides robust, reusable functions for reading/writing common data formats
(JSON, CSV, YAML) and computing/verifying SHA-256 checksums for data integrity.
"""

import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure the directory for the given path exists.

    Args:
        path: File or directory path.

    Returns:
        The resolved Path object.

    Raises:
        OSError: If the directory cannot be created.
    """
    dir_path = Path(path).parent
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def read_json(path: Union[str, Path]) -> Any:
    """
    Read and parse a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content (dict, list, etc.).

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Union[str, Path], data: Any, indent: int = 2) -> None:
    """
    Write data to a JSON file.

    Args:
        path: Path to the output JSON file.
        data: Data to serialize (dict, list, etc.).
        indent: Indentation level for pretty-printing.

    Raises:
        TypeError: If data is not JSON serializable.
        OSError: If the file cannot be written.
    """
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)


def read_csv(
    path: Union[str, Path],
    delimiter: str = ",",
    encoding: str = "utf-8",
    skip_blank_lines: bool = True,
) -> List[Dict[str, str]]:
    """
    Read a CSV file and return a list of dictionaries.

    Args:
        path: Path to the CSV file.
        delimiter: Field delimiter character.
        encoding: File encoding.
        skip_blank_lines: Whether to skip empty rows.

    Returns:
        List of row dictionaries.

    Raises:
        FileNotFoundError: If the file does not exist.
        csv.Error: If the CSV is malformed.
    """
    rows = []
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            if skip_blank_lines and all(v == "" for v in row.values()):
                continue
            rows.append(row)
    return rows


def write_csv(
    path: Union[str, Path],
    data: List[Dict[str, Any]],
    delimiter: str = ",",
    encoding: str = "utf-8",
    fieldnames: Optional[List[str]] = None,
) -> None:
    """
    Write a list of dictionaries to a CSV file.

    Args:
        path: Path to the output CSV file.
        data: List of row dictionaries.
        delimiter: Field delimiter character.
        encoding: File encoding.
        fieldnames: Explicit column names. If None, inferred from the first row.

    Raises:
        ValueError: If data is empty and fieldnames not provided.
        OSError: If the file cannot be written.
    """
    ensure_dir(path)
    if not data:
        raise ValueError("Cannot write empty CSV without explicit fieldnames.")

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(path, "w", encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        for row in data:
            # Convert non-string values to string for CSV safety
            safe_row = {k: str(v) if v is not None else "" for k, v in row.items()}
            writer.writerow(safe_row)


def compute_sha256(path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        path: Path to the file.
        chunk_size: Size of chunks to read (default 8KB).

    Returns:
        Hexadecimal SHA-256 hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_sha256(
    path: Union[str, Path], expected_hash: str, chunk_size: int = 8192
) -> bool:
    """
    Verify a file's SHA-256 hash against an expected value.

    Args:
        path: Path to the file.
        expected_hash: Expected hexadecimal SHA-256 hash.
        chunk_size: Size of chunks to read.

    Returns:
        True if the hash matches, False otherwise.
    """
    actual_hash = compute_sha256(path, chunk_size)
    return actual_hash == expected_hash.lower()


def read_yaml(path: Union[str, Path]) -> Any:
    """
    Read and parse a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def write_yaml(
    path: Union[str, Path], data: Any, default_flow_style: bool = False
) -> None:
    """
    Write data to a YAML file.

    Args:
        path: Path to the output YAML file.
        data: Data to serialize.
        default_flow_style: Use flow style (inline) for collections.

    Raises:
        TypeError: If data is not YAML serializable.
        OSError: If the file cannot be written.
    """
    ensure_dir(path)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=default_flow_style, allow_unicode=True)
