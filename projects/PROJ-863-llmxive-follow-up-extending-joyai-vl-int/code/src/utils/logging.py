"""
Logging utilities for the llmXive pipeline.

Implements FR-001.1: Execution logging for data sources, VLM API calls, and
pipeline stages. Ensures deterministic, traceable logs for reproducibility.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import os

# Global logger instance cache
_loggers: dict = {}

# Log format constants
STANDARD_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DETAILED_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"

# Custom log levels for pipeline events
DATA_LEVEL = 25  # Between INFO and WARNING
MODEL_LEVEL = 35 # Between INFO and ERROR

def _register_custom_levels():
    """Register custom log levels if not already registered."""
    if "DATA" not in logging._nameToLevel:
        logging.addLevelName(DATA_LEVEL, "DATA")
    if "MODEL" not in logging._nameToLevel:
        logging.addLevelName(MODEL_LEVEL, "MODEL")

def _ensure_log_dir(log_dir: Optional[Path] = None) -> Path:
    """Ensure the log directory exists."""
    if log_dir is None:
        # Default to project root logs/
        base = Path(__file__).resolve().parent.parent.parent
        log_dir = base / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir

def get_logger(
    name: str,
    log_dir: Optional[Path] = None,
    level: int = logging.INFO,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    detailed_format: bool = False
) -> logging.Logger:
    """
    Get or create a configured logger instance.

    Args:
        name: Logger name (typically __name__ of the caller)
        log_dir: Directory for log files (default: project_root/logs)
        level: Logging level
        enable_file_logging: Whether to write to file
        enable_console_logging: Whether to write to console
        detailed_format: Use detailed format with filename/lineno

    Returns:
        Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Pipeline started")
        logger.log(DATA_LEVEL, "Loaded dataset from %s", path)
    """
    _register_custom_levels()

    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logs from root handlers

    # Clear existing handlers
    logger.handlers.clear()

    formatter = logging.Formatter(
        DETAILED_FORMAT if detailed_format else STANDARD_FORMAT
    )

    # Console handler
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if enable_file_logging:
        log_dir = _ensure_log_dir(log_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{name.replace('.', '_')}_{timestamp}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger

def setup_project_logging(
    project_root: Optional[Path] = None,
    level: int = logging.INFO,
    detailed_format: bool = False
) -> logging.Logger:
    """
    Set up the root project logging configuration.

    This should be called once at the start of the main entry point
    to initialize logging for the entire pipeline.

    Args:
        project_root: Project root directory (default: auto-detect)
        level: Default logging level
        detailed_format: Use detailed format

    Returns:
        Root logger for the project
    """
    if project_root is None:
        # Auto-detect project root (go up from this file's location)
        project_root = Path(__file__).resolve().parent.parent.parent

    log_dir = _ensure_log_dir(project_root / "logs")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()

    formatter = logging.Formatter(
        DETAILED_FORMAT if detailed_format else STANDARD_FORMAT
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler for the whole project
    log_file = log_dir / f"project_{timestamp}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return root_logger

# Convenience functions for custom log levels
def log_data_event(logger: logging.Logger, msg: str, *args, **kwargs):
    """Log a data-related event (e.g., loading, processing)."""
    logger.log(DATA_LEVEL, msg, *args, **kwargs)

def log_model_event(logger: logging.Logger, msg: str, *args, **kwargs):
    """Log a model-related event (e.g., loading, inference)."""
    logger.log(MODEL_LEVEL, msg, *args, **kwargs)

def log_vlm_call(logger: logging.Logger, model_id: str, input_summary: str, duration_ms: float):
    """
    Log a VLM API call for audit trail.

    FR-001.1 requires tracking VLM calls to verify zero-call constraints
    in certain pipeline stages.

    Args:
        logger: Logger instance
        model_id: Identifier for the VLM model used
        input_summary: Brief description of the input
        duration_ms: API call duration in milliseconds
    """
    _register_custom_levels()
    entry = {
        "event": "vlm_api_call",
        "timestamp": datetime.now().isoformat(),
        "model_id": model_id,
        "input_summary": input_summary,
        "duration_ms": duration_ms
    }
    logger.log(MODEL_LEVEL, json.dumps(entry))

def log_no_vlm_call(logger: logging.Logger, stage_name: str):
    """
    Log that a stage explicitly did NOT use VLM calls.

    Useful for verifying FR-001.1 compliance in data labeling stages.

    Args:
        logger: Logger instance
        stage_name: Name of the pipeline stage
    """
    _register_custom_levels()
    entry = {
        "event": "vlm_api_call_skipped",
        "timestamp": datetime.now().isoformat(),
        "stage_name": stage_name,
        "reason": "Visual-only labeling (no VLM required)"
    }
    logger.log(DATA_LEVEL, json.dumps(entry))