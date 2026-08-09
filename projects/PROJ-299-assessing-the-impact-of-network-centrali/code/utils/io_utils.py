"""
Utility functions for CSV reading/writing and checksum validation.
Implements FR-001 Data Hygiene requirements.
"""
import csv
import hashlib
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, TextIO, BinaryIO


def calculate_file_checksum(
    file_path: Union[str, Path], algorithm: str = "sha256"
) -> str:
    """
    Calculate the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal checksum string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_func.update(chunk)

    return hash_func.hexdigest()


def verify_file_checksum(
    file_path: Union[str, Path], expected_checksum: str, algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected checksum value.
        algorithm: Hash algorithm used to generate the expected checksum.

    Returns:
        True if checksums match, False otherwise.
    """
    actual_checksum = calculate_file_checksum(file_path, algorithm)
    return actual_checksum.lower() == expected_checksum.lower()


def read_csv_as_dicts(
    file_path: Union[str, Path],
    delimiter: str = ",",
    encoding: str = "utf-8",
    skip_blank_lines: bool = True,
) -> List[Dict[str, Any]]:
    """
    Read a CSV file and return a list of dictionaries.

    Args:
        file_path: Path to the CSV file.
        delimiter: Field delimiter character.
        encoding: File encoding.
        skip_blank_lines: Whether to skip empty rows.

    Returns:
        List of dictionaries, one per row.

    Raises:
        FileNotFoundError: If the file does not exist.
        csv.Error: If the CSV is malformed.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    rows = []
    with open(file_path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            if skip_blank_lines and all(v.strip() == "" for v in row.values()):
                continue
            rows.append(dict(row))

    return rows


def write_dicts_to_csv(
    data: List[Dict[str, Any]],
    file_path: Union[str, Path],
    delimiter: str = ",",
    encoding: str = "utf-8",
    fieldnames: Optional[List[str]] = None,
    mode: str = "w",
) -> None:
    """
    Write a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to write.
        file_path: Output file path.
        delimiter: Field delimiter character.
        encoding: File encoding.
        fieldnames: Explicit list of field names (columns). If None, keys from
                    the first dict are used.
        mode: File open mode ('w' for write, 'a' for append).

    Raises:
        ValueError: If data is empty and fieldnames is not provided.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    if not data:
        if fieldnames:
            # Write empty file with headers
            with open(file_path, "w", encoding=encoding, newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
                writer.writeheader()
        return

    if fieldnames is None:
        fieldnames = list(data[0].keys())

    with open(file_path, mode, encoding=encoding, newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        if mode == "w":
            writer.writeheader()
        writer.writerows(data)


def read_json(
    file_path: Union[str, Path], encoding: str = "utf-8"
) -> Union[Dict[str, Any], List[Any]]:
    """
    Read a JSON file and return its contents.

    Args:
        file_path: Path to the JSON file.
        encoding: File encoding.

    Returns:
        Parsed JSON content (dict or list).

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding=encoding) as f:
        return json.load(f)


def write_json(
    data: Union[Dict[str, Any], List[Any]],
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    indent: Optional[int] = 2,
    sort_keys: bool = False,
) -> None:
    """
    Write data to a JSON file.

    Args:
        data: Data to write (dict or list).
        file_path: Output file path.
        encoding: File encoding.
        indent: Number of spaces for indentation (None for compact).
        sort_keys: Whether to sort dictionary keys.
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding=encoding) as f:
        json.dump(data, f, indent=indent, sort_keys=sort_keys)


def generate_checksum_file(
    source_file: Union[str, Path],
    output_file: Optional[Union[str, Path]] = None,
    algorithm: str = "sha256",
) -> Path:
    """
    Generate a checksum file for a given source file.

    Args:
        source_file: Path to the source file.
        output_file: Optional path for the checksum file. If None,
                     creates '{source_file}.sha256' in the same directory.
        algorithm: Hash algorithm to use.

    Returns:
        Path to the generated checksum file.
    """
    source_path = Path(source_file)
    if output_file is None:
        output_path = source_path.with_suffix(f"{source_path.suffix}.{algorithm}")
    else:
        output_path = Path(output_file)

    checksum = calculate_file_checksum(source_path, algorithm)
    # Format: <checksum>  <filename>
    content = f"{checksum}  {source_path.name}\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def verify_checksum_file(
    checksum_file: Union[str, Path],
    base_dir: Optional[Union[str, Path]] = None,
    algorithm: str = "sha256",
) -> Dict[str, bool]:
    """
    Verify files against a checksum file.

    Args:
        checksum_file: Path to the checksum file (format: '<hash>  <filename>').
        base_dir: Base directory to look for source files. If None, uses
                  the directory of the checksum file.
        algorithm: Expected hash algorithm.

    Returns:
        Dictionary mapping filenames to verification status (True/False).
    """
    checksum_path = Path(checksum_file)
    if base_dir is None:
        base_dir = checksum_path.parent
    else:
        base_dir = Path(base_dir)

    results = {}

    with open(checksum_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("  ", 1)
            if len(parts) != 2:
                continue

            expected_hash, filename = parts
            file_path = base_dir / filename

            if not file_path.exists():
                results[filename] = False
            else:
                actual_hash = calculate_file_checksum(file_path, algorithm)
                results[filename] = actual_hash.lower() == expected_hash.lower()

    return results