"""
I/O utilities for the project.

Provides robust file loading and saving functions for CSV, JSON, YAML, and
checksum verification.
"""

import csv
import json
import os
import sys
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Attempt to import yaml; if not available, provide a fallback or raise clear error
try:
    import yaml
except ImportError:
    # Define a clear error class to be raised if yaml is needed but missing
    class YamlMissingError(ImportError):
        """Raised when PyYAML is required but not installed."""
        pass

    def _yaml_missing(*args, **kwargs):
        raise YamlMissingError(
            "PyYAML is required for YAML operations. "
            "Install it via: pip install pyyaml"
        )

    # Mock functions to fail loudly if called without yaml
    yaml = type('MockYaml', (), {
        'safe_load': _yaml_missing,
        'safe_dump': _yaml_missing,
        'dump': _yaml_missing,
        'load': _yaml_missing
    })()


class IOLoadError(Exception):
    """Custom exception for I/O loading errors."""
    pass


class IOSaveError(Exception):
    """Custom exception for I/O saving errors."""
    pass


def ensure_dir(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: Path to the directory.

    Returns:
        The Path object for the directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def file_exists(path: Union[str, Path]) -> bool:
    """
    Check if a file exists.

    Args:
        path: Path to the file.

    Returns:
        True if the file exists, False otherwise.
    """
    return Path(path).is_file()


def load_csv(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load a CSV file into a list of dictionaries.

    Args:
        path: Path to the CSV file.

    Returns:
        List of dictionaries representing rows.

    Raises:
        IOLoadError: If the file cannot be read.
    """
    path = Path(path)
    if not path.exists():
        raise IOLoadError(f"File not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception as e:
        raise IOLoadError(f"Failed to load CSV {path}: {e}")


def save_csv(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a CSV file.

    Args:
        data: List of dictionaries to save.
        path: Path to the output CSV file.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    path = Path(path)
    ensure_dir(path.parent)

    if not data:
        # Write empty file if no data
        with open(path, 'w', encoding='utf-8') as f:
            pass
        return

    try:
        fieldnames = list(data[0].keys())
        with open(path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
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
        Parsed JSON content.

    Raises:
        IOLoadError: If the file cannot be read or parsed.
    """
    path = Path(path)
    if not path.exists():
        raise IOLoadError(f"File not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise IOLoadError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise IOLoadError(f"Failed to load JSON {path}: {e}")


def save_json(data: Any, path: Union[str, Path]) -> None:
    """
    Save data to a JSON file.

    Args:
        data: Data to save (must be JSON serializable).
        path: Path to the output JSON file.

    Raises:
        IOSaveError: If the file cannot be written.
    """
    path = Path(path)
    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    except Exception as e:
        raise IOSaveError(f"Failed to save JSON {path}: {e}")


def load_yaml(path: Union[str, Path]) -> Any:
    """
    Load a YAML file.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML content.

    Raises:
        IOLoadError: If yaml module is missing, file not found, or parsing fails.
    """
    path = Path(path)
    if not path.exists():
        raise IOLoadError(f"File not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except YamlMissingError:
        raise
    except Exception as e:
        raise IOLoadError(f"Failed to load YAML {path}: {e}")


def save_yaml(data: Any, path: Union[str, Path]) -> None:
    """
    Save data to a YAML file.

    Args:
        data: Data to save.
        path: Path to the output YAML file.

    Raises:
        IOSaveError: If yaml module is missing or file cannot be written.
    """
    path = Path(path)
    ensure_dir(path.parent)

    try:
        with open(path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
    except YamlMissingError:
        raise
    except Exception as e:
        raise IOSaveError(f"Failed to save YAML {path}: {e}")


def load_jsonl(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Load a JSONL (JSON Lines) file.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of dictionaries.

    Raises:
        IOLoadError: If the file cannot be read.
    """
    path = Path(path)
    if not path.exists():
        raise IOLoadError(f"File not found: {path}")

    data = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        raise IOLoadError(f"Invalid JSON on line {line_num} in {path}: {e}")
    except Exception as e:
        if isinstance(e, IOLoadError):
            raise
        raise IOLoadError(f"Failed to load JSONL {path}: {e}")

    return data


def save_jsonl(data: List[Dict[str, Any]], path: Union[str, Path]) -> None:
    """
    Save a list of dictionaries to a JSONL file.

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
                f.write(json.dumps(item, default=str) + '\n')
    except Exception as e:
        raise IOSaveError(f"Failed to save JSONL {path}: {e}")


def compute_sha256(path: Union[str, Path]) -> str:
    """
    Compute the SHA256 checksum of a file.

    Args:
        path: Path to the file.

    Returns:
        Hexadecimal string of the SHA256 hash.

    Raises:
        IOLoadError: If the file cannot be read.
    """
    path = Path(path)
    if not path.exists():
        raise IOLoadError(f"File not found: {path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise IOLoadError(f"Failed to compute checksum for {path}: {e}")


def verify_checksums(checksums_file: Union[str, Path]) -> Dict[str, bool]:
    """
    Verify file checksums against a checksums file.

    The checksums file should be a JSON file with structure:
    {
      "relative/path/to/file": "sha256_hash",
      ...
    }

    Args:
        checksums_file: Path to the checksums JSON file.

    Returns:
        Dictionary mapping file paths to verification status (True/False).

    Raises:
        IOLoadError: If the checksums file cannot be read.
    """
    checksums_file = Path(checksums_file)
    if not checksums_file.exists():
        raise IOLoadError(f"Checksums file not found: {checksums_file}")

    try:
        checksums = load_json(checksums_file)
    except IOLoadError:
        raise

    results = {}
    base_dir = checksums_file.parent

    for rel_path, expected_hash in checksums.items():
        file_path = base_dir / rel_path
        if not file_path.exists():
            results[rel_path] = False
            continue

        try:
            actual_hash = compute_sha256(file_path)
            results[rel_path] = (actual_hash == expected_hash)
        except IOLoadError:
            results[rel_path] = False

    return results


def main():
    """Main entry point for CLI verification."""
    import argparse

    parser = argparse.ArgumentParser(description="I/O utilities CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # verify-checksums command
    verify_parser = subparsers.add_parser("verify-checksums", help="Verify file checksums")
    verify_parser.add_argument("checksums_file", help="Path to checksums JSON file")

    args = parser.parse_args()

    if args.command == "verify-checksums":
        try:
            results = verify_checksums(args.checksums_file)
            all_valid = all(results.values())
            print(f"Verification results: {results}")
            print(f"All valid: {all_valid}")
            sys.exit(0 if all_valid else 1)
        except IOLoadError as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
