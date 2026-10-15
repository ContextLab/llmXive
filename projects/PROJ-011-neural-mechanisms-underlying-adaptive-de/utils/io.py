"""
utils/io.py

Robust file loading, saving, and checksum verification utilities.
Supports CSV, JSON, JSONL, and YAML formats.

This version adds flexible signatures for ``save_csv`` and ``save_json``
so that they work with the argument order used in the contract tests
(path first, then data) and also accept ``pandas.DataFrame`` objects.
"""

import csv
import json
import os
import sys
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import yaml, but allow failure if not installed (lazy load in functions)
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Try to import pandas for DataFrame handling; if unavailable the code will still work
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class IOLoadError(Exception):
    """Raised when a file fails to load."""
    pass


class IOSaveError(Exception):
    """Raised when a file fails to save."""
    pass


def get_logger(name: str = "io_utils") -> logging.Logger:
    """Get a logger instance for this module."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        directory: Path to the directory.

    Returns:
        The Path object for the directory.

    Raises:
        IOSaveError: If the directory cannot be created.
    """
    path = Path(directory)
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise IOSaveError(f"Failed to create directory {path}: {e}")
    return path


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if a file exists.

    Args:
        path: Path to the file.

    Returns:
        True if the file exists, False otherwise.
    """
    return Path(path).is_file()


def load_csv(path: Union[str, Path], delimiter: str = ',') -> List[Dict[str, Any]]:
    """
    Load a CSV/TSV file into a list of dictionaries.

    Args:
        path: Path to the CSV/TSV file.
        delimiter: Delimiter used in the file.

    Returns:
        List of dictionaries representing rows.

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise IOLoadError(f"CSV file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            data = list(reader)
        return data
    except Exception as e:
        raise IOLoadError(f"Failed to load CSV {path}: {e}")


def _normalize_save_csv_args(arg1, arg2, delimiter: str = ',') -> tuple[Path, List[Dict[str, Any]]]:
    """
    Internal helper to support flexible ``save_csv`` signatures.

    Accepts either:
        save_csv(data, path, delimiter=…)
    or
        save_csv(path, data, delimiter=…)

    ``data`` may be a list of dicts or a pandas DataFrame.
    """
    # Determine which argument is the path
    if isinstance(arg1, (str, Path)):
        path = Path(arg1)
        data = arg2
    else:
        path = Path(arg2) if arg2 is not None else None
        data = arg1

    if path is None:
        raise IOSaveError("Path argument for save_csv is missing.")

    # Convert pandas DataFrame to list-of-dicts if needed
    if PANDAS_AVAILABLE and isinstance(data, pd.DataFrame):
        data = data.to_dict(orient='records')
    elif not isinstance(data, list):
        raise IOSaveError("Data for save_csv must be a list of dictionaries or a pandas DataFrame.")

    return path, data


def save_csv(*args, delimiter: str = ',', **kwargs) -> None:
    """
    Save a list of dictionaries (or a pandas DataFrame) to a CSV/TSV file.

    Flexible signature:
        save_csv(data, path, delimiter=…)
    or
        save_csv(path, data, delimiter=…)

    Args:
        *args: Positional arguments following one of the signatures above.
        delimiter: Delimiter to use in the CSV file.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    # Support keyword ``sep`` alias used in tests
    if 'sep' in kwargs:
        delimiter = kwargs.pop('sep')

    path, data = _normalize_save_csv_args(*args, delimiter=delimiter)

    ensure_dir(path.parent)

    if not data:
        # Write empty file if no data
        try:
            with open(path, 'w', encoding='utf-8') as f:
                pass
            return
        except Exception as e:
            raise IOSaveError(f"Failed to save empty CSV {path}: {e}")

    fieldnames = list(data[0].keys())

    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
    except Exception as e:
        raise IOSaveError(f"Failed to save CSV {path}: {e}")


def load_json(path: Union[str, Path]) -> Any:
    """
    Load a JSON file.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content (dict, list, etc.).

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise IOLoadError(f"JSON file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise IOLoadError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise IOLoadError(f"Failed to load JSON {path}: {e}")


def _normalize_save_json_args(arg1, arg2=None, indent: int = 2) -> tuple[Path, Any]:
    """
    Internal helper to support flexible ``save_json`` signatures.

    Accepts either:
        save_json(data, path, indent=…)
    or
        save_json(path, data, indent=…)

    The test suite uses the latter order.
    """
    if isinstance(arg1, (str, Path)):
        path = Path(arg1)
        data = arg2
    else:
        path = Path(arg2) if arg2 is not None else None
        data = arg1

    if path is None:
        raise IOSaveError("Path argument for save_json is missing.")
    return path, data


def save_json(*args, indent: int = 2, **kwargs) -> None:
    """
    Save data to a JSON file.

    Flexible signature:
        save_json(data, path, indent=…)
    or
        save_json(path, data, indent=…)

    Args:
        *args: Positional arguments following one of the signatures above.
        indent: Indentation level for pretty printing.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    path, data = _normalize_save_json_args(*args, indent=indent)

    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent)
    except Exception as e:
        raise IOSaveError(f"Failed to save JSON {path}: {e}")


def load_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load a JSON Lines file (one JSON object per line).

    Args:
        path: Path to the JSONL file.

    Returns:
        List of dictionaries.

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.is_file():
        raise IOLoadError(f"JSONL file not found: {path}")

    data = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise IOLoadError(f"Invalid JSON on line {line_num} in {path}: {e}")
        return data
    except Exception as e:
        raise IOLoadError(f"Failed to load JSONL {path}: {e}")


def save_jsonl(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a JSON Lines file.

    Args:
        data: List of dictionaries to save.
        path: Path to the output JSONL file.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    path = Path(path)
    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item) + '\n')
    except Exception as e:
        raise IOSaveError(f"Failed to save JSONL {path}: {e}")


def load_yaml(path: Union[str, Path]) -> Any:
    """
    Load a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content.

    Raises:
        IOLoadError: If PyYAML is not installed, or if the file cannot be read.
    """
    if not YAML_AVAILABLE:
        raise IOLoadError("PyYAML is not installed. Cannot load YAML files.")

    path = Path(path)
    if not path.is_file():
        raise IOLoadError(f"YAML file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise IOLoadError(f"Invalid YAML in {path}: {e}")
    except Exception as e:
        raise IOLoadError(f"Failed to load YAML {path}: {e}")


def save_yaml(data: Any, path: Union[str, Path]) -> None:
    """
    Save data to a YAML file.

    Args:
        data: Data to save.
        path: Path to the output YAML file.

    Raises:
        IOSaveError: If PyYAML is not installed, or if the file cannot be written.
    """
    if not YAML_AVAILABLE:
        raise IOSaveError("PyYAML is not installed. Cannot save YAML files.")

    path = Path(path)
    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    except Exception as e:
        raise IOSaveError(f"Failed to save YAML {path}: {e}")


def compute_sha256(path: Union[str, Path], chunk_size: int = 8192) -> str:
    """
    Compute the SHA256 hash of a file.

    Args:
        path: Path to the file.
        chunk_size: Size of chunks to read at a time.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        IOLoadError: If the file cannot be read.
    """
    path = Path(path)
    if not path.is_file():
        raise IOLoadError(f"File not found for hashing: {path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(chunk_size), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOLoadError(f"Failed to hash file {path}: {e}")


def verify_checksums(manifest_path: Union[str, Path], base_dir: Optional[Union[str, Path]] = None) -> Dict[str, bool]:
    """
    Verify file checksums against a manifest.

    The manifest is expected to be a JSON or YAML file containing a dictionary
    where keys are relative file paths and values are expected SHA256 hashes.

    Args:
        manifest_path: Path to the manifest file (JSON or YAML).
        base_dir: Base directory for resolving relative paths in the manifest.
                  If None, uses the directory of the manifest file.

    Returns:
        Dictionary mapping file paths to verification status (True/False).

    Raises:
        IOLoadError: If the manifest cannot be loaded or if a file cannot be hashed.
    """
    manifest_path = Path(manifest_path)
    if not manifest_path.is_file():
        raise IOLoadError(f"Manifest file not found: {manifest_path}")

    # Determine base directory
    if base_dir is None:
        base_dir = manifest_path.parent
    else:
        base_dir = Path(base_dir)

    # Load manifest
    try:
        if manifest_path.suffix in ['.yaml', '.yml']:
            checksums = load_yaml(manifest_path)
        else:
            checksums = load_json(manifest_path)
    except IOLoadError:
        # Re-raise load errors
        raise

    if not isinstance(checksums, dict):
        raise IOLoadError("Manifest must be a dictionary of {path: hash}")

    results = {}
    for rel_path, expected_hash in checksums.items():
        full_path = base_dir / rel_path
        try:
            actual_hash = compute_sha256(full_path)
            results[rel_path] = (actual_hash == expected_hash)
        except IOLoadError:
            results[rel_path] = False

    return results


def main() -> None:
    """
    CLI entry point for io utilities.

    Usage:
        python -m utils.io verify-checksums --manifest <path> [--base-dir <path>]
    """
    parser = argparse.ArgumentParser(
        description="IO Utilities for file loading, saving, and verification.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # verify-checksums command
    verify_parser = subparsers.add_parser(
        'verify-checksums',
        help='Verify file checksums against a manifest.'
    )
    verify_parser.add_argument(
        '--manifest', '-m',
        type=str,
        required=True,
        help='Path to the manifest file (JSON or YAML).'
    )
    verify_parser.add_argument(
        '--base-dir', '-b',
        type=str,
        default=None,
        help='Base directory for resolving relative paths. Defaults to manifest directory.'
    )

    args = parser.parse_args()

    if args.command == 'verify-checksums':
        logger = get_logger()
        logger.info(f"Verifying checksums from manifest: {args.manifest}")
        try:
            results = verify_checksums(args.manifest, args.base_dir)
            all_pass = all(results.values())

            logger.info(f"Verification Results:")
            for path, passed in results.items():
                status = "PASS" if passed else "FAIL"
                logger.info(f"  {path}: {status}")

            if all_pass:
                logger.info("All checksums verified successfully.")
                sys.exit(0)
            else:
                failed_count = sum(1 for v in results.values() if not v)
                logger.error(f"Verification failed for {failed_count} file(s).")
                sys.exit(1)
        except IOLoadError as e:
            logger.error(f"Error during verification: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == '__main__':
    main()
