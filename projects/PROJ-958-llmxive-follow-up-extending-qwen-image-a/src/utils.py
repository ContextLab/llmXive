"""
llmXive Utility Module
Provides logging infrastructure, error handling wrappers, and domain stratification helpers.
"""

import logging
import os
import sys
import json
from typing import Any, Callable, TypeVar, Optional, List, Dict
from functools import wraps
from pathlib import Path

# Import project configuration
from src.config import LOG_LEVEL, LOG_DIR, SEED, PROJECT_ROOT

T = TypeVar('T')


# --- Logging Infrastructure ---

_loggers: Dict[str, logging.Logger] = {}

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves or creates a configured logger.
    Ensures consistent formatting and file output.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Prevent duplicate handlers if called multiple times in same process
    if logger.handlers:
        _loggers[name] = logger
        return logger

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    if LOG_DIR:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_file = os.path.join(LOG_DIR, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


# --- Error Handling Wrappers ---

class PipelineError(Exception):
    """Base exception for pipeline-specific errors."""
    pass

class DataFetchError(PipelineError):
    """Raised when real data fetch fails."""
    pass

class SchemaValidationError(PipelineError):
    """Raised when data schema does not match expected structure."""
    pass

class ProcessingError(PipelineError):
    """Raised during data processing or transformation."""
    pass


def handle_errors(
    default: Optional[T] = None,
    logger_name: str = "llmXive",
    raise_on_failure: bool = False
) -> Callable[[Callable[..., T]], Callable[..., Optional[T]]]:
    """
    Decorator to wrap function calls with error handling.

    Args:
        default: Value to return on failure (if raise_on_failure is False).
        logger_name: Name of the logger to use.
        raise_on_failure: If True, re-raise the exception instead of returning default.

    Returns:
        Wrapped function.
    """
    logger = get_logger(logger_name)

    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
                if raise_on_failure:
                    raise
                return default
        return wrapper
    return decorator


# --- Domain Stratification Helpers ---

def stratify_by_complexity(
    data: List[Dict[str, Any]],
    score_field: str = "syntactic_complexity_score",
    thresholds: tuple = (0.2, 0.6)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Stratifies a list of data records based on a complexity score.

    Args:
        data: List of dictionaries containing records.
        score_field: Key in the dictionary holding the complexity score.
        thresholds: Tuple (low_threshold, high_threshold).
                    < low_threshold -> "low"
                    low <= score <= high -> "medium"
                    > high_threshold -> "high"

    Returns:
        Dictionary mapping category names to lists of records.
    """
    low_thresh, high_thresh = thresholds
    strata = {"low": [], "medium": [], "high": []}

    for record in data:
        score = record.get(score_field)
        if score is None:
            # Log warning or handle missing score as needed
            continue

        if score < low_thresh:
            strata["low"].append(record)
        elif score <= high_thresh:
            strata["medium"].append(record)
        else:
            strata["high"].append(record)

    return strata


def save_stratified_metadata(
    strata: Dict[str, List[Dict[str, Any]]],
    output_path: str
) -> None:
    """
    Saves stratification metadata to a JSON file.

    Args:
        strata: Dictionary of stratified data.
        output_path: Path to save the JSON file.
    """
    metadata = {
        "categories": {
            cat: {
                "count": len(items),
                "sample_ids": [item.get("id", "unknown") for item in items[:5]]
            }
            for cat, items in strata.items()
        }
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)

    logger = get_logger()
    logger.info(f"Stratification metadata saved to {output_path}")