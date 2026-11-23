"""
Refactoring and utility functions for the llmXive project.
This module provides safe operations for file I/O, path validation,
and common refactoring tasks to ensure code cleanliness and reliability.
"""
import os
import sys
import logging
import time
import json
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union, Tuple

from utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar('T')

class RefactorError(Exception):
    """Base exception for refactoring utilities."""
    pass

class PathValidationError(RefactorError):
    """Raised when a path validation fails."""
    pass

class TypeHintError(RefactorError):
    """Raised when type hint validation fails."""
    pass

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.

    Args:
        path: The directory path to ensure exists.

    Returns:
        The Path object for the directory.

    Raises:
        PathValidationError: If the path cannot be created or is not a directory.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        if not dir_path.is_dir():
            raise PathValidationError(f"Path exists but is not a directory: {dir_path}")
        return dir_path
    except OSError as e:
        raise PathValidationError(f"Failed to create directory {dir_path}: {e}")

def safe_json_load(path: Union[str, Path]) -> Dict[str, Any]:
    """
    Safely load a JSON file with error handling.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed JSON content as a dictionary.

    Raises:
        RefactorError: If the file cannot be read or parsed.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise RefactorError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                logger.warning(f"JSON file {file_path} does not contain a top-level object. Got: {type(data)}")
            return data
    except json.JSONDecodeError as e:
        raise RefactorError(f"Failed to parse JSON in {file_path}: {e}")
    except IOError as e:
        raise RefactorError(f"Failed to read file {file_path}: {e}")

def safe_json_save(data: Dict[str, Any], path: Union[str, Path], indent: int = 2) -> None:
    """
    Safely save a dictionary to a JSON file with error handling.

    Args:
        data: The dictionary to save.
        path: Path to the output JSON file.
        indent: Indentation level for pretty-printing.

    Raises:
        RefactorError: If the file cannot be written.
    """
    file_path = Path(path)
    try:
        ensure_directory(file_path.parent)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, sort_keys=True)
        logger.debug(f"Successfully saved JSON to {file_path}")
    except (IOError, TypeError) as e:
        raise RefactorError(f"Failed to write JSON to {file_path}: {e}")

def timed_operation(operation: Callable[..., T], name: str = "Operation") -> Tuple[T, float]:
    """
    Execute an operation and measure its execution time.

    Args:
        operation: The callable to execute.
        name: Name of the operation for logging.

    Returns:
        A tuple of (result, elapsed_time_seconds).
    """
    start_time = time.perf_counter()
    try:
        result = operation()
        elapsed = time.perf_counter() - start_time
        logger.debug(f"{name} completed in {elapsed:.4f}s")
        return result, elapsed
    except Exception as e:
        elapsed = time.perf_counter() - start_time
        logger.error(f"{name} failed after {elapsed:.4f}s: {e}")
        raise

def validate_non_empty_list(data: List[Any], field_name: str = "list") -> List[Any]:
    """
    Validate that a list is not empty.

    Args:
        data: The list to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated list.

    Raises:
        RefactorError: If the list is empty.
    """
    if not data:
        raise RefactorError(f"{field_name} cannot be empty")
    return data

def validate_non_empty_dict(data: Dict[str, Any], field_name: str = "dict") -> Dict[str, Any]:
    """
    Validate that a dictionary is not empty.

    Args:
        data: The dictionary to validate.
        field_name: Name of the field for error messages.

    Returns:
        The validated dictionary.

    Raises:
        RefactorError: If the dictionary is empty.
    """
    if not data:
        raise RefactorError(f"{field_name} cannot be empty")
    return data

def get_project_root() -> Path:
    """
    Determine the project root directory.

    Returns:
        Path to the project root (assumes 'code' is a subdirectory).
    """
    current = Path(__file__).resolve()
    # Navigate up to find 'code' directory, then up one more for root
    if current.name == 'refactor_utils.py':
        code_dir = current.parent
        if code_dir.name == 'code':
            return code_dir.parent
    # Fallback: assume current working directory is root
    return Path.cwd()

def normalize_path(path: Union[str, Path], base: Optional[Path] = None) -> Path:
    """
    Normalize a path relative to a base directory.

    Args:
        path: The path to normalize.
        base: Base directory (defaults to project root).

    Returns:
        Normalized absolute Path.
    """
    p = Path(path)
    if not p.is_absolute():
        if base is None:
            base = get_project_root()
        p = base / p
    return p.resolve()

def log_mode_info() -> None:
    """Log the current execution mode (CI vs Research) for debugging."""
    try:
        from config import get_mode, is_ci_mode, is_research_mode
        mode = get_mode()
        logger.info(f"Current mode: {mode}")
        logger.info(f"Is CI mode: {is_ci_mode()}")
        logger.info(f"Is Research mode: {is_research_mode()}")
    except ImportError:
        logger.warning("Could not import config module to log mode info.")

def cleanup_temp_files(pattern: str = "*.tmp", base_dir: Optional[Path] = None) -> int:
    """
    Clean up temporary files matching a pattern.

    Args:
        pattern: Glob pattern for files to delete (default: *.tmp).
        base_dir: Directory to search in (default: project root).

    Returns:
        Number of files deleted.
    """
    if base_dir is None:
        base_dir = get_project_root()

    count = 0
    for file_path in base_dir.rglob(pattern):
        try:
            if file_path.is_file():
                file_path.unlink()
                count += 1
                logger.debug(f"Deleted temp file: {file_path}")
        except OSError as e:
            logger.warning(f"Could not delete {file_path}: {e}")
    return count

def validate_required_keys(data: Dict[str, Any], required_keys: List[str], context: str = "Data") -> Dict[str, Any]:
    """
    Validate that a dictionary contains all required keys.

    Args:
        data: The dictionary to validate.
        required_keys: List of keys that must be present.
        context: Context string for error messages.

    Returns:
        The validated dictionary.

    Raises:
        RefactorError: If any required keys are missing.
    """
    missing = [k for k in required_keys if k not in data]
    if missing:
        raise RefactorError(f"{context} is missing required keys: {missing}")
    return data

def retry_on_failure(func: Callable[..., T], max_retries: int = 3, delay: float = 1.0) -> Callable[..., T]:
    """
    Decorator to retry a function on failure.

    Args:
        func: The function to wrap.
        max_retries: Maximum number of retry attempts.
        delay: Delay in seconds between retries.

    Returns:
        The wrapped function.
    """
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        last_exception = None
        for attempt in range(1, max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}. Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.error(f"All {max_retries} attempts failed for {func.__name__}")
        raise last_exception

    return wrapper