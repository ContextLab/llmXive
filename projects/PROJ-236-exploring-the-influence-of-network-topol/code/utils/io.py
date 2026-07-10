"""
I/O utilities for the network topology heat transport project.
Includes configuration loading, file handling, and checksumming.
"""
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_simulation_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the simulation configuration from a YAML file.

    Args:
        config_path: Path to the configuration file. Defaults to
                     `code/simulation_config.yaml` relative to the project root.

    Returns:
        A dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
        ValueError: If the configuration file is empty.
    """
    if config_path is None:
        # Default path relative to project root (assuming code/ is project root or sibling)
        # The task specifies `code/simulation_config.yaml`
        base_dir = Path(__file__).resolve().parent.parent
        config_path = base_dir / "simulation_config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    if config is None:
        raise ValueError(f"Configuration file is empty: {config_path}")

    return config


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Retrieve a value from the config dictionary using a dot-separated key path.

    Args:
        config: The configuration dictionary.
        key_path: Dot-separated string (e.g., "network_generation.cutoff_factor").
        default: Value to return if the key path is not found.

    Returns:
        The value at the key path, or the default.
    """
    keys = key_path.split(".")
    current = config
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: 'sha256'). Supported:
                   'md5', 'sha1', 'sha256'.

    Returns:
        Hexadecimal string of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    supported_algorithms = ["md5", "sha1", "sha256"]
    if algorithm not in supported_algorithms:
        raise ValueError(f"Unsupported algorithm: {algorithm}. Choose from {supported_algorithms}")

    hasher = hashlib.new(algorithm)

    with open(file_path, "rb") as f:
        # Read in chunks to handle large files efficiently
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_file_checksum(file_path: Path, expected_checksum: str, algorithm: str = "sha256") -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected hexadecimal checksum string.
        algorithm: Hash algorithm used for the checksum.

    Returns:
        True if the computed checksum matches the expected checksum, False otherwise.
    """
    try:
        computed = compute_file_checksum(file_path, algorithm)
        return computed.lower() == expected_checksum.lower()
    except FileNotFoundError:
        return False
    except ValueError:
        return False
