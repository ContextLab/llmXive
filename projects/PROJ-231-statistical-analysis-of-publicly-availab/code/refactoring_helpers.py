"""
Refactoring helpers to reduce code duplication across the pipeline.

This module provides reusable utilities for common operations:
- Standardized error handling
- Logging wrappers
- Data validation patterns
- Resource management

These helpers should be used in place of duplicated code in:
- ingestion.py
- basis.py
- fpca.py
- robustness.py
- visualize.py
"""
import os
import logging
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, TypeVar, Union
from functools import wraps

from config import get_project_root, get_data_dir, get_artifacts_dir

logger = logging.getLogger(__name__)

T = TypeVar('T')


class PipelineError(Exception):
    """Base exception for pipeline-related errors."""
    pass


class DataValidationError(PipelineError):
    """Raised when data validation fails."""
    pass


class ConfigurationError(PipelineError):
    """Raised when configuration is invalid."""
    pass


def log_operation(operation_name: str, level: int = logging.INFO):
    """
    Decorator to log operation start and completion.
    
    Args:
        operation_name: Name of the operation for logging
        level: Logging level for the operation
        
    Example:
        @log_operation("process_data")
        def process_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.log(level, f"Starting operation: {operation_name}")
            try:
                result = func(*args, **kwargs)
                logger.log(level, f"Completed operation: {operation_name}")
                return result
            except Exception as e:
                logger.error(f"Failed operation: {operation_name} - {e}")
                raise
        return wrapper
    return decorator


def validate_input_path(path: Union[str, Path], must_exist: bool = True) -> Path:
    """
    Validate and normalize input path.
    
    Args:
        path: Path to validate
        must_exist: Whether the path must exist
        
    Returns:
        Normalized Path object
        
    Raises:
        DataValidationError: If validation fails
    """
    path_obj = Path(path)
    
    if must_exist and not path_obj.exists():
        raise DataValidationError(f"Required path does not exist: {path}")
    
    if not path_obj.is_absolute():
        # Resolve relative to project root
        path_obj = get_project_root() / path_obj
    
    logger.debug(f"Validated input path: {path_obj}")
    return path_obj


def validate_output_path(path: Union[str, Path], ensure_parent: bool = True) -> Path:
    """
    Validate and normalize output path.
    
    Args:
        path: Path to validate
        ensure_parent: Whether to create parent directories
        
    Returns:
        Normalized Path object
        
    Raises:
        ConfigurationError: If validation fails
    """
    path_obj = Path(path)
    
    if not path_obj.is_absolute():
        path_obj = get_project_root() / path_obj
    
    if ensure_parent:
        path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    logger.debug(f"Validated output path: {path_obj}")
    return path_obj


def safe_json_load(file_path: Union[str, Path], default: Optional[Dict] = None) -> Dict:
    """
    Safely load JSON with error handling.
    
    Args:
        file_path: Path to JSON file
        default: Default value if file doesn't exist or is invalid
        
    Returns:
        Parsed JSON data or default
    """
    path = validate_input_path(file_path, must_exist=False)
    
    if not path.exists():
        if default is not None:
            logger.warning(f"File not found, returning default: {file_path}")
            return default
        raise DataValidationError(f"JSON file not found: {file_path}")
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.debug(f"Loaded JSON from: {file_path}")
            return data
    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON in {file_path}: {e}"
        logger.error(error_msg)
        if default is not None:
            return default
        raise DataValidationError(error_msg)


def safe_json_save(data: Dict, file_path: Union[str, Path]) -> None:
    """
    Safely save data to JSON with error handling.
    
    Args:
        data: Data to save
        file_path: Path to save to
        
    Raises:
        PipelineError: If save fails
    """
    path = validate_output_path(file_path)
    
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        logger.info(f"Saved JSON to: {file_path}")
    except Exception as e:
        error_msg = f"Failed to save JSON to {file_path}: {e}"
        logger.error(error_msg)
        raise PipelineError(error_msg)


def safe_pickle_load(file_path: Union[str, Path], default: Optional[Any] = None) -> Any:
    """
    Safely load pickle file with error handling.
    
    Args:
        file_path: Path to pickle file
        default: Default value if file doesn't exist
        
    Returns:
        Unpickled data or default
    """
    path = validate_input_path(file_path, must_exist=False)
    
    if not path.exists():
        if default is not None:
            logger.warning(f"Pickled file not found, returning default: {file_path}")
            return default
        raise DataValidationError(f"Pickle file not found: {file_path}")
    
    try:
        with open(path, 'rb') as f:
            data = pickle.load(f)
            logger.debug(f"Loaded pickle from: {file_path}")
            return data
    except Exception as e:
        error_msg = f"Failed to load pickle from {file_path}: {e}"
        logger.error(error_msg)
        if default is not None:
            return default
        raise DataValidationError(error_msg)


def safe_pickle_save(data: Any, file_path: Union[str, Path]) -> None:
    """
    Safely save data to pickle with error handling.
    
    Args:
        data: Data to save
        file_path: Path to save to
        
    Raises:
        PipelineError: If save fails
    """
    path = validate_output_path(file_path)
    
    try:
        with open(path, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)
        logger.info(f"Saved pickle to: {file_path}")
    except Exception as e:
        error_msg = f"Failed to save pickle to {file_path}: {e}"
        logger.error(error_msg)
        raise PipelineError(error_msg)


def ensure_directory_exists(dir_path: Union[str, Path]) -> Path:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        dir_path: Path to directory
        
    Returns:
        Path object for the directory
    """
    path = Path(dir_path)
    if not path.is_absolute():
        path = get_project_root() / path
    
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
    return path


def get_relative_path(full_path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> Path:
    """
    Get the relative path from a base directory.
    
    Args:
        full_path: Full path to convert
        base: Base directory (defaults to project root)
        
    Returns:
        Relative path
    """
    path = Path(full_path)
    base_path = Path(base) if base else get_project_root()
    
    try:
        return path.relative_to(base_path)
    except ValueError:
        # Path is not relative to base
        return path


def format_size(size_bytes: int) -> str:
    """
    Format byte size to human-readable string.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def log_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Log information about a file and return stats.
    
    Args:
        file_path: Path to file
        
    Returns:
        Dictionary with file statistics
    """
    path = validate_input_path(file_path)
    stat = path.stat()
    
    info = {
        "path": str(path),
        "size_bytes": stat.st_size,
        "size_human": format_size(stat.st_size),
        "modified": stat.st_mtime,
    }
    
    logger.info(f"File info: {info}")
    return info


def validate_required_keys(data: Dict, required_keys: List[str], context: str = "data") -> None:
    """
    Validate that a dictionary contains all required keys.
    
    Args:
        data: Dictionary to validate
        required_keys: List of required key names
        context: Context for error messages
        
    Raises:
        DataValidationError: If any required key is missing
    """
    missing = [key for key in required_keys if key not in data]
    if missing:
        error_msg = f"Missing required keys in {context}: {missing}"
        logger.error(error_msg)
        raise DataValidationError(error_msg)
    logger.debug(f"Validated required keys in {context}: {required_keys}")


def merge_dicts(base: Dict, override: Dict) -> Dict:
    """
    Deep merge two dictionaries, with override taking precedence.
    
    Args:
        base: Base dictionary
        override: Dictionary with values to override
        
    Returns:
        Merged dictionary
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def main() -> int:
    """
    Main entry point for refactoring helpers validation.
    
    Returns:
        Exit code (0 for success)
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Refactoring helpers module loaded successfully.")
    logger.info("Available utilities:")
    logger.info("  - PipelineError, DataValidationError, ConfigurationError")
    logger.info("  - log_operation decorator")
    logger.info("  - validate_input_path, validate_output_path")
    logger.info("  - safe_json_load, safe_json_save")
    logger.info("  - safe_pickle_load, safe_pickle_save")
    logger.info("  - ensure_directory_exists")
    logger.info("  - format_size, log_file_info")
    logger.info("  - validate_required_keys, merge_dicts")
    return 0


if __name__ == "__main__":
    exit(main())
