"""
Refactored utility functions for code cleanup and standardization.

This module consolidates common patterns found across the codebase:
1. Type hinting enforcement
2. Docstring standardization
3. Error handling wrappers
4. Logging utility helpers
5. Path normalization utilities

This file addresses T039: Code cleanup and refactoring.
"""
import os
import sys
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union, Tuple
from functools import wraps
import json

# Local imports using verified API surface
from utils.logger import get_logger, log_error
from config import get_mode, is_ci_mode
from config_env import get_env_config

T = TypeVar('T')

class RefactorError(Exception):
    """Base exception for refactoring utilities."""
    pass

class PathValidationError(RefactorError):
    """Raised when path validation fails."""
    pass

class TypeHintError(RefactorError):
    """Raised when type hint validation fails."""
    pass

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path to the directory.
        
    Returns:
        The validated Path object.
        
    Raises:
        PathValidationError: If the path cannot be created or is not a directory.
    """
    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        if not dir_path.is_dir():
            raise PathValidationError(f"Path exists but is not a directory: {dir_path}")
        return dir_path
    except Exception as e:
        raise PathValidationError(f"Failed to ensure directory {path}: {e}") from e

def safe_json_load(path: Union[str, Path], default: Optional[Dict] = None) -> Dict:
    """
    Safely load a JSON file with error handling.
    
    Args:
        path: Path to the JSON file.
        default: Default value to return if file not found or invalid.
        
    Returns:
        Parsed JSON data as a dictionary.
        
    Raises:
        RefactorError: If default is None and file cannot be loaded.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        if default is not None:
            return default
        raise RefactorError(f"File not found: {path}")
    except json.JSONDecodeError as e:
        if default is not None:
            return default
        raise RefactorError(f"Invalid JSON in {path}: {e}")

def safe_json_save(data: Dict, path: Union[str, Path], indent: int = 2) -> None:
    """
    Safely save data to a JSON file.
    
    Args:
        data: Dictionary to save.
        path: Target file path.
        indent: Indentation level for formatting.
        
    Raises:
        RefactorError: If saving fails.
    """
    try:
        dir_path = Path(path).parent
        dir_path.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, sort_keys=True)
    except Exception as e:
        raise RefactorError(f"Failed to save JSON to {path}: {e}") from e

def timed_operation(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator to log execution time of a function.
    
    Args:
        func: The function to wrap.
        
    Returns:
        Wrapped function with timing logging.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> T:
        logger = get_logger("refactor")
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start_time
            logger.debug(f"Function {func.__name__} completed in {elapsed:.4f}s")
            return result
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            logger.error(f"Function {func.__name__} failed after {elapsed:.4f}s: {e}")
            raise
    return wrapper

def validate_non_empty_list(items: List[Any], field_name: str) -> List[Any]:
    """
    Validate that a list is not empty.
    
    Args:
        items: The list to validate.
        field_name: Name of the field for error messages.
        
    Returns:
        The validated list.
        
    Raises:
        RefactorError: If the list is empty.
    """
    if not items:
        raise RefactorError(f"Field '{field_name}' cannot be an empty list")
    return items

def validate_non_empty_dict(data: Dict[str, Any], field_name: str) -> Dict[str, Any]:
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
        raise RefactorError(f"Field '{field_name}' cannot be an empty dictionary")
    return data

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root (parent of 'code').
    """
    current_file = Path(__file__).resolve()
    # Assuming this file is in code/utils/, so root is 2 levels up
    return current_file.parent.parent.parent

def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path to be absolute and clean.
    
    Args:
        path: Input path.
        
    Returns:
        Normalized absolute Path.
    """
    p = Path(path)
    if not p.is_absolute():
        p = get_project_root() / p
    return p.resolve()

def log_mode_info() -> None:
    """
    Log current execution mode (CI vs Research) to the logger.
    
    This is a refactored utility to ensure consistent mode logging.
    """
    logger = get_logger("refactor")
    mode = get_mode()
    is_ci = is_ci_mode()
    env_config = get_env_config()
    
    logger.info(f"Execution Mode: {mode}")
    logger.info(f"CI Mode Active: {is_ci}")
    logger.info(f"Data Path: {env_config.data_path}")
    logger.info(f"Results Path: {env_config.results_path}")

def cleanup_temp_files(pattern: str = "*.tmp", directory: Optional[Union[str, Path]] = None) -> List[Path]:
    """
    Find and return paths of temporary files matching a pattern.
    
    Note: This function only returns paths; it does not delete files to prevent
    accidental data loss. Use with caution in production.
    
    Args:
        pattern: Glob pattern for files to find.
        directory: Directory to search (defaults to project root).
        
    Returns:
        List of matching file paths.
    """
    search_dir = Path(directory) if directory else get_project_root()
    if not search_dir.exists():
        return []
    
    return list(search_dir.rglob(pattern))

def validate_required_keys(data: Dict[str, Any], required_keys: List[str], context: str = "") -> Dict[str, Any]:
    """
    Validate that a dictionary contains all required keys.
    
    Args:
        data: Dictionary to validate.
        required_keys: List of keys that must be present.
        context: Context string for error messages (e.g., "config", "dataset").
        
    Returns:
        The validated dictionary.
        
    Raises:
        RefactorError: If any required key is missing.
    """
    missing = [k for k in required_keys if k not in data]
    if missing:
        context_str = f" ({context})" if context else ""
        raise RefactorError(f"Missing required keys{context_str}: {missing}")
    return data

def retry_on_failure(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retry attempts.
        delay: Delay in seconds between retries.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator
