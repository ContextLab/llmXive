"""
Structured logging and checkpointing for self-improving LLM cycles.

This module provides functions to:
- Initialize a structured JSON logger for each cycle.
- Update log entries with cycle metrics.
- Save model checkpoints to disk.
- Retrieve historical cycle data.
"""

import json
import os
import time
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_config, get_log_path, ensure_directories

# Global state for the current cycle logger
_current_logger: Optional[logging.Logger] = None
_current_log_path: Optional[str] = None
_cycle_history: List[Dict[str, Any]] = []

def get_log_path(cycle_number: int) -> str:
    """
    Generate the log file path for a specific cycle.

    Args:
        cycle_number: The cycle index (0-based or 1-based, consistent with caller).

    Returns:
        Full path to the log file.
    """
    config = get_config()
    log_dir = config.path_config.log_dir
    os.makedirs(log_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cycle_{cycle_number}_{timestamp}.log"
    return os.path.join(log_dir, filename)

def init_cycle_logger(cycle_number: int, log_level: int = logging.INFO) -> logging.Logger:
    """
    Initialize a structured JSON logger for a specific cycle.

    This creates a new log file with a JSON formatter. It also sets up the
    global _current_logger reference.

    Args:
        cycle_number: The cycle index.
        log_level: Logging level (default INFO).

    Returns:
        The configured logger instance.
    """
    global _current_logger, _current_log_path

    log_path = get_log_path(cycle_number)
    _current_log_path = log_path

    # Create logger
    logger = logging.getLogger(f"cycle_{cycle_number}")
    logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with JSON formatter
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(log_level)

    # Custom JSON formatter
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_record = {
                "timestamp": datetime.now().isoformat(),
                "cycle": cycle_number,
                "level": record.levelname,
                "message": record.getMessage(),
            }
            # Add extra fields if present
            if hasattr(record, 'extra_data'):
                log_record.update(record.extra_data)
            return json.dumps(log_record)

    file_handler.setFormatter(JsonFormatter())
    logger.addHandler(file_handler)

    _current_logger = logger
    return logger

def update_cycle_log(cycle_number: int, data: Dict[str, Any]) -> None:
    """
    Append a structured entry to the current cycle's log file.

    Args:
        cycle_number: The cycle index.
        data: Dictionary of metrics/fields to log.
    """
    global _current_logger

    if _current_logger is None:
        # Fallback: init if not already done
        _current_logger = init_cycle_logger(cycle_number)

    # Create a log record with extra data
    record = _current_logger.makeRecord(
        _current_logger.name,
        logging.INFO,
        "",
        0,
        "Cycle update",
        (),
        None
    )
    record.extra_data = data
    _current_logger.handle(record)

def checkpoint_model_state(
    cycle_number: int,
    model_state: Dict[str, Any],
    optimizer_state: Optional[Dict[str, Any]] = None
) -> str:
    """
    Save model and optimizer states to disk.

    Args:
        cycle_number: The cycle index.
        model_state: State dict of the model.
        optimizer_state: Optional state dict of the optimizer.

    Returns:
        Path to the saved checkpoint file.
    """
    config = get_config()
    checkpoint_dir = config.path_config.checkpoint_dir
    os.makedirs(checkpoint_dir, exist_ok=True)

    filename = f"cycle_{cycle_number}_checkpoint.pt"
    filepath = os.path.join(checkpoint_dir, filename)

    checkpoint = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "model_state": model_state,
    }
    if optimizer_state is not None:
        checkpoint["optimizer_state"] = optimizer_state

    # Note: In a real implementation, this would use torch.save.
    # Since we are in a generic logging module, we serialize to JSON for portability
    # unless torch is available and tensors are passed.
    try:
        import torch
        torch.save(checkpoint, filepath)
    except (ImportError, TypeError):
        # Fallback to JSON if torch is not available or states are not tensors
        # This handles cases where state is already a dict of primitives
        with open(filepath, 'w') as f:
            json.dump(checkpoint, f, indent=2, default=str)

    return filepath

def log_cycle_summary(
    cycle_number: int,
    metrics: Dict[str, float],
    status: str = "completed"
) -> None:
    """
    Log a summary of the cycle execution.

    Args:
        cycle_number: The cycle index.
        metrics: Dictionary of final metrics (e.g., accuracy, loss).
        status: Execution status (e.g., "completed", "failed", "early_stop").
    """
    global _current_logger

    if _current_logger is None:
        _current_logger = init_cycle_logger(cycle_number)

    summary_data = {
        "status": status,
        "metrics": metrics,
        "summary": True
    }
    update_cycle_log(cycle_number, summary_data)

    # Also add to in-memory history
    entry = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "metrics": metrics
    }
    _cycle_history.append(entry)

def get_cycle_history() -> List[Dict[str, Any]]:
    """
    Retrieve the in-memory history of all logged cycles.

    Returns:
        List of cycle summary dictionaries.
    """
    return _cycle_history.copy()

def log_error(cycle_number: int, error_message: str, exception: Optional[Exception] = None) -> None:
    """
    Log an error event for a specific cycle.

    Args:
        cycle_number: The cycle index.
        error_message: Description of the error.
        exception: Optional exception instance for traceback.
    """
    global _current_logger

    if _current_logger is None:
        _current_logger = init_cycle_logger(cycle_number)

    log_data = {
        "error": error_message,
        "exception_type": type(exception).__name__ if exception else None,
        "exception_msg": str(exception) if exception else None,
    }
    update_cycle_log(cycle_number, log_data)
    _current_logger.error(error_message, exc_info=exception)

def log_warning(cycle_number: int, warning_message: str) -> None:
    """
    Log a warning event for a specific cycle.

    Args:
        cycle_number: The cycle index.
        warning_message: Description of the warning.
    """
    global _current_logger

    if _current_logger is None:
        _current_logger = init_cycle_logger(cycle_number)

    update_cycle_log(cycle_number, {"warning": warning_message})
    _current_logger.warning(warning_message)
