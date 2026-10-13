import logging
import os
from pathlib import Path
from typing import Optional, Union

# Project root and directory paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"

# Random seed for reproducibility
RANDOM_SEED = 42

# Batch size constants
# Primary batch size for LLM inference (as required by the task)
LLM_BATCH_SIZE = 10
# Existing name used throughout the codebase – keep for compatibility
LLM_BATCH_SIZE_MAX = LLM_BATCH_SIZE

# Resource‑monitoring batch‑size limit (from the plan/spec)
FR008_BATCH_SIZE_LIMIT = 50

# Commonly‑used file paths (exposed as constants for ease of import)
STATIC_BASELINE_PATH = DATA_DIR / "static_baseline.csv"
SEMANTIC_RESULTS_PATH = DATA_PROCESSED_DIR / "semantic_results.json"
RESOURCE_METRICS_PATH = RESULTS_DIR / "resource_metrics.json"

def _ensure_results_dir_exists() -> None:
    """
    Ensure that the results directory exists before any file handlers are created.
    This helper is used internally by the logging configuration.
    """
    if not RESULTS_DIR.exists():
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)

def setup_logging(
    name: Optional[Union[str, None]] = None,
    level: Optional[int] = None
) -> logging.Logger:
    """
    Configure and return a logger instance.

    This function is designed to be tolerant of various call signatures
    found across the codebase:
    - setup_logging()
    - setup_logging("module_name")
    - setup_logging(__name__)
    - setup_logging("module_name", logging.INFO)

    In addition to the existing StreamHandler, this implementation adds a
    FileHandler that writes logs to ``results/run.log``. The log format
    includes timestamp, logger name, level and message.

    Args:
        name: Optional logger name. If None, returns the root logger.
        level: Optional logging level (e.g., logging.INFO). If None, uses default.

    Returns:
        logging.Logger: Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Determine logging level
    if level is not None:
        logger.setLevel(level)
    else:
        logger.setLevel(logging.INFO)

    # Define a consistent log format
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Add a StreamHandler if none exist (or if only a FileHandler exists)
    has_stream = any(isinstance(h, logging.StreamHandler) for h in logger.handlers)
    if not has_stream:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Add a FileHandler (one per logger) if not already present
    has_file = any(isinstance(h, logging.FileHandler) for h in logger.handlers)
    if not has_file:
        _ensure_results_dir_exists()
        log_file_path = RESULTS_DIR / "run.log"
        file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent log messages from being propagated to the root logger multiple times
    logger.propagate = False

    return logger

def get_path(relative_path: str) -> Path:
    """
    Get an absolute path relative to the project root.

    Args:
        relative_path: Path relative to project root.

    Returns:
        Path: Absolute path.
    """
    return PROJECT_ROOT / relative_path

def get_data_path(filename: str) -> Path:
    """
    Get path to a file in the data directory.

    Args:
        filename: Name of the file in data/ directory.

    Returns:
        Path: Absolute path to the file.
    """
    return DATA_DIR / filename

def get_processed_path(filename: str) -> Path:
    """
    Get path to a file in the processed data directory.

    Args:
        filename: Name of the file in data/processed/ directory.

    Returns:
        Path: Absolute path.
    """
    return DATA_PROCESSED_DIR / filename

def get_results_path(filename: Optional[str] = None) -> Path:
    """
    Get path to a file in the results directory.

    Args:
        filename: Optional name of the file in results/ directory.
                 If omitted, the path to the results directory itself is returned.

    Returns:
        Path: Absolute path to the file or directory.
    """
    if filename:
        return RESULTS_DIR / filename
    return RESULTS_DIR