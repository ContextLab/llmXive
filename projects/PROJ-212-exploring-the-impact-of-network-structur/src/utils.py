"""
Utility functions for the network synchronization pipeline.
"""

import json
import logging
from pathlib import Path
from typing import Optional, Any, Dict

import jsonschema
import yaml


def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.

    Parameters
    ----------
    name : str
        Logger name (typically __name__).
    log_file : str, optional
        Path to a log file. If provided, logs will be written to this file.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers
    if logger.hasHandlers():
        return logger

    # Set log level
    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file is specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def save_json(
    obj: Any,
    path: Path,
    schema_path: Optional[Path] = None,
) -> None:
    """
    Save an object to a JSON file with optional schema validation.

    Parameters
    ----------
    obj : Any
        The object to serialize.
    path : Path
        The output file path.
    schema_path : Path, optional
        Path to a YAML schema file for validation. If provided, the object
        will be validated against the schema before writing.

    Raises
    ------
    jsonschema.ValidationError
        If the object does not conform to the provided schema.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Validate against schema if provided
    if schema_path:
        schema_path = Path(schema_path)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, "r") as f:
            schema = yaml.safe_load(f)

        jsonschema.validate(instance=obj, schema=schema)

    # Write JSON with indentation
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def load_json(path: Path) -> Any:
    """
    Load a JSON file.

    Parameters
    ----------
    path : Path
        The input file path.

    Returns
    -------
    Any
        The deserialized JSON object.
    """
    path = Path(path)
    with open(path, "r") as f:
        return json.load(f)


def load_yaml(path: Path) -> Any:
    """
    Load a YAML file.

    Parameters
    ----------
    path : Path
        The input file path.

    Returns
    -------
    Any
        The deserialized YAML object.
    """
    path = Path(path)
    with open(path, "r") as f:
        return yaml.safe_load(f)