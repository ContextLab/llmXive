"""
Robust File I/O utilities for the llmXive pipeline.

Provides functions for loading/saving CSV, JSON, YAML, and JSONL files,
as well as directory and checksum operations.
"""

import csv
import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, TextIO

try:
    import yaml
except ImportError:
    yaml = None

# Configure logging for this module
logger = logging.getLogger(__name__)


class IOLoadError(Exception):
    """Raised when a file load operation fails."""
    pass


class IOSaveError(Exception):
    """Raised when a file save operation fails."""
    pass


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists. Creates it if it doesn't.

    Args:
        path: Path to the directory.

    Returns:
        The Path object for the directory.

    Raises:
        IOSaveError: If the directory cannot be created.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {dir_path}")
        return dir_path
    except OSError as e:
        raise IOSaveError(f"Failed to create directory {dir_path}: {e}")


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if a file exists.

    Args:
        path: Path to the file.

    Returns:
        True if the file exists, False otherwise.
    """
    return Path(path).is_file()


def load_csv(path: Union[str, Path], **kwargs) -> List[Dict[str, Any]]:
    """
    Load a CSV file into a list of dictionaries.

    Args:
        path: Path to the CSV file.
        **kwargs: Additional arguments passed to csv.DictReader.

    Returns:
        A list of dictionaries, one per row.

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise IOLoadError(f"CSV file not found: {file_path}")

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f, **kwargs)
            data = list(reader)
        logger.info(f"Loaded {len(data)} rows from {file_path}")
        return data
    except Exception as e:
        raise IOLoadError(f"Failed to load CSV {file_path}: {e}")


def save_csv(data: List[Dict[str, Any]], path: Union[str, Path], **kwargs) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        path: Path to the output CSV file.
        **kwargs: Additional arguments passed to csv.DictWriter.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    file_path = Path(path)
    ensure_dir(file_path.parent)

    if not data:
        logger.warning(f"Attempting to save empty data to {file_path}")
        # Create an empty file or handle as needed
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            pass
        return

    try:
        fieldnames = data[0].keys()
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, **kwargs)
            writer.writeheader()
            writer.writerows(data)
        logger.info(f"Saved {len(data)} rows to {file_path}")
    except Exception as e:
        raise IOSaveError(f"Failed to save CSV {file_path}: {e}")


def load_json(path: Union[str, Path]) -> Any:
    """
    Load a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        The parsed JSON object (dict, list, etc.).

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise IOLoadError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON from {file_path}")
        return data
    except json.JSONDecodeError as e:
        raise IOLoadError(f"Invalid JSON in {file_path}: {e}")
    except Exception as e:
        raise IOLoadError(f"Failed to load JSON {file_path}: {e}")


def save_json(data: Any, path: Union[str, Path], indent: int = 2) -> None:
    """
    Save an object to a JSON file.

    Args:
        data: Object to save (must be JSON serializable).
        path: Path to the output JSON file.
        indent: Indentation level for pretty printing.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    file_path = Path(path)
    ensure_dir(file_path.parent)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, default=str)
        logger.debug(f"Saved JSON to {file_path}")
    except Exception as e:
        raise IOSaveError(f"Failed to save JSON {file_path}: {e}")


def load_yaml(path: Union[str, Path]) -> Any:
    """
    Load a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        The parsed YAML object.

    Raises:
        IOLoadError: If yaml module is missing, file not found, or parse error.
    """
    if yaml is None:
        raise IOLoadError("PyYAML is not installed. Install via 'pip install pyyaml'")

    file_path = Path(path)
    if not file_path.exists():
        raise IOLoadError(f"YAML file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        logger.debug(f"Loaded YAML from {file_path}")
        return data
    except yaml.YAMLError as e:
        raise IOLoadError(f"Invalid YAML in {file_path}: {e}")
    except Exception as e:
        raise IOLoadError(f"Failed to load YAML {file_path}: {e}")


def save_yaml(data: Any, path: Union[str, Path]) -> None:
    """
    Save an object to a YAML file.

    Args:
        data: Object to save.
        path: Path to the output YAML file.

    Raises:
        IOSaveError: If yaml module is missing or file cannot be written.
    """
    if yaml is None:
        raise IOSaveError("PyYAML is not installed. Install via 'pip install pyyaml'")

    file_path = Path(path)
    ensure_dir(file_path.parent)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        logger.debug(f"Saved YAML to {file_path}")
    except Exception as e:
        raise IOSaveError(f"Failed to save YAML {file_path}: {e}")


def load_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load a JSON Lines file.

    Args:
        path: Path to the JSONL file.

    Returns:
        A list of dictionaries.

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise IOLoadError(f"JSONL file not found: {file_path}")

    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise IOLoadError(f"Invalid JSON on line {line_num} in {file_path}: {e}")
        logger.info(f"Loaded {len(data)} lines from {file_path}")
        return data
    except Exception as e:
        if isinstance(e, IOLoadError):
            raise
        raise IOLoadError(f"Failed to load JSONL {file_path}: {e}")


def save_jsonl(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a JSON Lines file.

    Args:
        data: List of dictionaries to save.
        path: Path to the output JSONL file.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    file_path = Path(path)
    ensure_dir(file_path.parent)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
        logger.debug(f"Saved {len(data)} lines to {file_path}")
    except Exception as e:
        raise IOSaveError(f"Failed to save JSONL {file_path}: {e}")


def compute_sha256(path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        path: Path to the file.
        chunk_size: Size of chunks to read at a time.

    Returns:
        The hexadecimal SHA256 hash string.

    Raises:
        IOLoadError: If the file cannot be read.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise IOLoadError(f"File not found for hashing: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOLoadError(f"Failed to compute hash for {file_path}: {e}")


def verify_checksums(checksum_file: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify file checksums against a stored checksum file.

    The checksum file is expected to be a JSON file with a structure like:
    {
        "relative/path/file.txt": "sha256_hash_string",
        ...
    }

    Args:
        checksum_file: Path to the JSON file containing checksums.

    Returns:
        A dictionary mapping file paths to verification status (True/False).

    Raises:
        IOLoadError: If the checksum file is missing or invalid.
    """
    file_path = Path(checksum_file)
    if not file_path.exists():
        raise IOLoadError(f"Checksum file not found: {file_path}")

    try:
        checksums = load_json(file_path)
    except IOLoadError:
        raise

    results = {}
    base_dir = file_path.parent

    for rel_path, expected_hash in checksums.items():
        full_path = base_dir / rel_path
        if not full_path.exists():
            results[rel_path] = False
            logger.warning(f"File missing for checksum verification: {full_path}")
            continue

        try:
            actual_hash = compute_sha256(full_path)
            is_valid = actual_hash == expected_hash
            results[rel_path] = is_valid
            if not is_valid:
                logger.error(f"Checksum mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")
            else:
                logger.debug(f"Checksum verified for {rel_path}")
        except IOLoadError as e:
            results[rel_path] = False
            logger.error(f"Error verifying {rel_path}: {e}")

    return results


def main() -> None:
    """
    Command-line interface for the io module.

    Usage:
        python -m code.utils.io verify-checksums --path <checksum_file>

    Currently supports:
        - verify-checksums: Verify files against a JSON checksum manifest.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Utilities for file I/O and checksum verification."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # verify-checksums command
    verify_parser = subparsers.add_parser(
        "verify-checksums",
        help="Verify file checksums against a JSON manifest."
    )
    verify_parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Path to the JSON file containing checksums."
    )

    args = parser.parse_args()

    if args.command == "verify-checksums":
        try:
            results = verify_checksums(args.path)
            all_valid = all(results.values())
            
            # Output results
            if all_valid:
                print("All checksums verified successfully.")
                sys.exit(0)
            else:
                failed = [k for k, v in results.items() if not v]
                print(f"Verification failed for {len(failed)} files:")
                for f in failed:
                    print(f"  - {f}")
                sys.exit(1)
        except IOLoadError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()