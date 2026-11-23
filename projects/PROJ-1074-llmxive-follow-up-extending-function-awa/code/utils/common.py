"""
Common utilities for the llmXive automated science pipeline.
Provides shared logging configuration, error handling, and helper functions.
"""
import logging
import sys
from pathlib import Path
from typing import Any, Optional, Dict, List

# ----------------------------------------------------------------------
# Logging Configuration
# ----------------------------------------------------------------------

_logger_initialized = False
_default_log_level = logging.INFO
_default_log_format = (
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

def configure_logging(
    level: Optional[int] = None,
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    name: str = "llmXive",
) -> logging.Logger:
    """
    Configure the root logger for the project.

    Args:
        level: Logging level (e.g., logging.DEBUG, logging.INFO). Defaults to INFO.
        format_string: Log format string. Defaults to a standard format.
        log_file: Optional path to a log file. If provided, logs are also written to this file.
        name: Name of the logger to configure (default: "llmXive").

    Returns:
        The configured logger instance.
    """
    global _logger_initialized

    if level is None:
        level = _default_log_level
    if format_string is None:
        format_string = _default_log_format

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        # If handlers already exist, we assume logging was configured elsewhere
        # or we don't want to duplicate handlers on subsequent calls.
        return logger

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File Handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _logger_initialized = True
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a logger instance. If the root logger hasn't been configured yet,
    this will configure it with default settings.

    Args:
        name: Name of the child logger to retrieve.

    Returns:
        A logger instance.
    """
    global _logger_initialized
    if not _logger_initialized:
        configure_logging()
    return logging.getLogger(name)

# ----------------------------------------------------------------------
# Error Handling Utilities
# ----------------------------------------------------------------------

class PipelineError(Exception):
    """Base exception for pipeline-related errors."""

    def __init__(self, message: str, code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        if self.code:
            return f"[{self.code}] {self.message}"
        return self.message

class DataLoadError(PipelineError):
    """Raised when data loading fails."""
    pass

class ValidationError(PipelineError):
    """Raised when data validation fails."""
    pass

class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""
    pass

class ModelError(PipelineError):
    """Raised when model operations fail."""
    pass

def safe_run(
    func: callable,
    default: Any = None,
    on_error: Optional[callable] = None,
    log_error: bool = True,
) -> Any:
    """
    Safely execute a function, catching exceptions and optionally logging them.

    Args:
        func: The function to execute.
        default: Value to return if an exception occurs.
        on_error: Optional callback to execute if an error occurs (receives the exception).
        log_error: Whether to log the exception using the default logger.

    Returns:
        The result of func, or the default value if an exception occurred.
    """
    try:
        return func()
    except Exception as e:
        if log_error:
            logger = get_logger()
            logger.error(f"Error in safe_run: {e}", exc_info=True)
        if on_error:
            on_error(e)
        return default

# ----------------------------------------------------------------------
# File System Helpers
# ----------------------------------------------------------------------

def ensure_dir(path: str | Path) -> Path:
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

def read_json(path: str | Path) -> Dict:
    """
    Read a JSON file and return its contents as a dictionary.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid JSON.
    """
    import json
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {path}: {e}")

def write_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """
    Write data to a JSON file.

    Args:
        data: Data to write (must be JSON serializable).
        path: Path to the output file.
        indent: Indentation level for pretty printing.
    """
    import json
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)

def read_yaml(path: str | Path) -> Dict:
    """
    Read a YAML file and return its contents as a dictionary.

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML data.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is not valid YAML.
    """
    import yaml
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {path}: {e}")

def write_yaml(data: Any, path: str | Path) -> None:
    """
    Write data to a YAML file.

    Args:
        data: Data to write (must be YAML serializable).
        path: Path to the output file.
    """
    import yaml
    path = Path(path)
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, default_flow_style=False)

# ----------------------------------------------------------------------
# Type Checking Helpers
# ----------------------------------------------------------------------

def is_iterable(obj: Any, exclude_str: bool = True) -> bool:
    """
    Check if an object is iterable.

    Args:
        obj: Object to check.
        exclude_str: If True, strings are not considered iterable.

    Returns:
        True if the object is iterable, False otherwise.
    """
    if exclude_str and isinstance(obj, str):
        return False
    try:
        iter(obj)
        return True
    except TypeError:
        return False

def flatten_list(nested_list: List[List[Any]]) -> List[Any]:
    """
    Flatten a nested list one level deep.

    Args:
        nested_list: A list of lists.

    Returns:
        A flattened list.
    """
    return [item for sublist in nested_list for item in sublist]