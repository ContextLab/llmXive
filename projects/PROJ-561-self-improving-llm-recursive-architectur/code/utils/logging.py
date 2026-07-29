"""
Structured logging and checkpointing for self-improving LLM cycles.

This module provides functions to:
- Initialize cycle-specific loggers
- Write structured JSON logs for each cycle
- Checkpoint model states
- Log cycle summaries, errors, and warnings
- Retrieve cycle history
"""
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from config import get_config


def get_log_path() -> str:
    """Return the path to the logs directory."""
    config = get_config()
    return os.path.join(config.results_path, "logs")


def init_cycle_logger(cycle_number: int) -> logging.Logger:
    """
    Initialize a structured JSON logger for a specific cycle.

    Args:
        cycle_number: The current cycle number.

    Returns:
        A logger configured to write JSON-formatted logs to results/logs/cycle_{N}.log.
    """
    log_dir = get_log_path()
    os.makedirs(log_dir, exist_ok=True)

    log_file = os.path.join(log_dir, f"cycle_{cycle_number}.log")

    logger = logging.getLogger(f"cycle_{cycle_number}")
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplicates
    logger.handlers = []

    # Create file handler with JSON formatting
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.INFO)

    # Custom formatter to output JSON
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "cycle": cycle_number,
            }
            # Add extra fields if present
            if hasattr(record, "extra_data"):
                log_entry.update(record.extra_data)
            return json.dumps(log_entry)

    formatter = JsonFormatter()
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def update_cycle_log(logger: logging.Logger, message: str, extra_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Update the cycle log with a new entry.

    Args:
        logger: The logger instance for the cycle.
        message: The log message.
        extra_data: Optional dictionary of additional fields to include.
    """
    if extra_data:
        record = logger.makeRecord(
            logger.name, logging.INFO, "", 0, message, (), None
        )
        record.extra_data = extra_data
        logger.handle(record)
    else:
        logger.info(message)


def checkpoint_model_state(cycle_number: int, model_state: Dict[str, Any]) -> str:
    """
    Save a checkpoint of the model state to disk.

    Args:
        cycle_number: The current cycle number.
        model_state: The state dictionary to save.

    Returns:
        The path to the saved checkpoint file.
    """
    checkpoint_dir = os.path.join(get_config().results_path, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    checkpoint_path = os.path.join(checkpoint_dir, f"cycle_{cycle_number}_model.pt")

    # Save using standard torch format (assuming model_state is a state_dict)
    import torch
    torch.save(model_state, checkpoint_path)

    return checkpoint_path


def log_cycle_summary(
    logger: logging.Logger,
    cycle_number: int,
    metrics: Dict[str, float],
    modification_type: str,
    param_count: int,
    training_time_seconds: float,
    status: str = "completed"
) -> None:
    """
    Log a structured summary of the cycle.

    Args:
        logger: The cycle logger.
        cycle_number: The cycle number.
        metrics: Dictionary of benchmark metrics (e.g., GSM8K, ARC).
        modification_type: Type of architectural modification applied.
        param_count: Total parameter count after modification.
        training_time_seconds: Wall-clock time for the cycle.
        status: Status of the cycle (e.g., "completed", "timeout", "failed").
    """
    summary_data = {
        "cycle_number": cycle_number,
        "modification_type": modification_type,
        "param_count": param_count,
        "training_time_seconds": training_time_seconds,
        "status": status,
        "metrics": metrics,
    }
    update_cycle_log(
        logger,
        "Cycle summary",
        extra_data=summary_data
    )


def get_cycle_history() -> List[Dict[str, Any]]:
    """
    Read all cycle log files and return their history.

    Returns:
        A list of log entries from all cycle logs.
    """
    log_dir = get_log_path()
    history = []

    if not os.path.exists(log_dir):
        return history

    log_files = sorted([
        f for f in os.listdir(log_dir)
        if f.startswith("cycle_") and f.endswith(".log")
    ])

    for log_file in log_files:
        file_path = os.path.join(log_dir, log_file)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            history.append(entry)
                        except json.JSONDecodeError:
                            # Skip malformed lines
                            continue
        except IOError:
            continue

    return history


def log_error(logger: logging.Logger, error_msg: str, exception: Optional[Exception] = None) -> None:
    """
    Log an error message.

    Args:
        logger: The logger instance.
        error_msg: The error message.
        exception: Optional exception object to include details.
    """
    extra = {}
    if exception:
        extra["exception_type"] = type(exception).__name__
        extra["exception_message"] = str(exception)

    if extra:
        record = logger.makeRecord(
            logger.name, logging.ERROR, "", 0, error_msg, (), None
        )
        record.extra_data = extra
        logger.handle(record)
    else:
        logger.error(error_msg)


def log_warning(logger: logging.Logger, warning_msg: str) -> None:
    """
    Log a warning message.

    Args:
        logger: The logger instance.
        warning_msg: The warning message.
    """
    logger.warning(warning_msg)
