"""
Utility functions for the llmXive research pipeline.

This module provides logging infrastructure, environment configuration management,
and other shared utilities.
"""
import hashlib
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def setup_logging(
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    name: str = "llmXive"
) -> logging.Logger:
    """
    Configure and return a logger with timestamped, level-based output.

    Args:
        log_file: Optional path to a log file. If None, logs only to console.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
        name: Name of the logger instance.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def load_config(
    config_path: Optional[str] = None,
    env_prefix: str = "LLMXIVE_"
) -> Dict[str, Any]:
    """
    Load configuration from a YAML file and override with environment variables.

    This function supports the following precedence:
    1. Default values (if any)
    2. Values from the YAML config file
    3. Values from environment variables (overrides YAML)

    Environment variables are expected to be prefixed with `env_prefix` (default: "LLMXIVE_").
    Nested keys in the YAML are flattened with underscores for environment variable matching.
    Example: `database.host` in YAML -> `LLMXIVE_DATABASE_HOST` in env.

    Args:
        config_path: Path to the configuration YAML file. If None, defaults to 'config.yaml'.
        env_prefix: Prefix for environment variables.

    Returns:
        Dictionary containing the merged configuration.

    Raises:
        FileNotFoundError: If the config file does not exist and no defaults are provided.
        yaml.YAMLError: If the config file contains invalid YAML.
    """
    if config_path is None:
        config_path = "config.yaml"

    config: Dict[str, Any] = {}

    # Load from YAML file if it exists
    config_file = Path(config_path)
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                loaded_config = yaml.safe_load(f)
                if loaded_config is not None:
                    config.update(loaded_config)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing config file {config_path}: {e}")
    else:
        # If no config file exists, start with empty config
        # (Environment variables will still be checked)
        pass

    # Override with environment variables
    def update_from_env(current_config: Dict[str, Any], prefix: str) -> None:
        for key, value in os.environ.items():
            if key.startswith(prefix):
                env_key = key[len(prefix):].lower()
                # Handle nested keys (e.g., DATABASE_HOST -> database: host)
                parts = env_key.split("_")
                if len(parts) == 1:
                    current_config[parts[0]] = _parse_env_value(value)
                else:
                    # Navigate/create nested dict
                    nested = current_config
                    for part in parts[:-1]:
                        if part not in nested:
                            nested[part] = {}
                        elif not isinstance(nested[part], dict):
                            # If the key exists but is not a dict, convert it
                            nested[part] = {"_value": nested[part]}
                        nested = nested[part]
                    nested[parts[-1]] = _parse_env_value(value)

    update_from_env(config, env_prefix)

    return config


def _parse_env_value(value: str) -> Any:
    """
    Parse an environment variable string into an appropriate Python type.

    Handles:
    - Booleans (true/false, yes/no, 1/0)
    - Integers
    - Floats
    - None (null, none, "")
    - Strings (default)

    Args:
        value: The string value from the environment variable.

    Returns:
        Parsed value in the appropriate type.
    """
    if not value:
        return None

    lower_value = value.lower()

    # Check for boolean
    if lower_value in ("true", "yes", "1"):
        return True
    if lower_value in ("false", "no", "0"):
        return False

    # Check for None
    if lower_value in ("null", "none", ""):
        return None

    # Check for integer
    try:
        return int(value)
    except ValueError:
        pass

    # Check for float
    try:
        return float(value)
    except ValueError:
        pass

    # Default to string
    return value


def compute_file_checksum(
    file_path: str,
    algorithm: str = "sha256",
    chunk_size: int = 8192
) -> str:
    """
    Compute the cryptographic checksum of a file using the specified algorithm.

    This utility is essential for verifying the integrity of raw data downloads
    and ensuring reproducibility. It reads the file in chunks to handle large
    datasets without excessive memory usage.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: "sha256"). Supported:
                   "md5", "sha1", "sha256", "sha512".
        chunk_size: Number of bytes to read at a time. Default is 8KB.

    Returns:
        Hexadecimal string representation of the file's checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    if not Path(file_path).exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        hasher = hashlib.new(algorithm)
    except ValueError:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}. "
                         f"Supported: md5, sha1, sha256, sha512")

    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)

    return hasher.hexdigest()


def verify_checksum(
    file_path: str,
    expected_checksum: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: The expected hexadecimal checksum string.
        algorithm: Hash algorithm used to generate the expected checksum.

    Returns:
        True if the computed checksum matches the expected checksum, False otherwise.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    computed = compute_file_checksum(file_path, algorithm)
    # Normalize case for comparison (hexdigest is lowercase, but input might vary)
    return computed.lower() == expected_checksum.lower()


# Initialize a default logger for the project
logger = setup_logging(
    log_file="data/pipeline.log",
    level=logging.INFO,
    name="llmXive"
)
