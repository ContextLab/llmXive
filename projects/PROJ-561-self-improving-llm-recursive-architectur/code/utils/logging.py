"""
Structured cycle logging and checkpointing utilities for the self-improving LLM pipeline.

Provides functions to:
- Initialize cycle-specific loggers with JSON formatting
- Log structured events (errors, warnings, summaries)
- Checkpoint model states with metadata
- Retrieve cycle history
"""
import json
import os
import time
import logging
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_config, get_log_path, ensure_directories

# Global logger cache to avoid re-initialization
_loggers: Dict[str, logging.Logger] = {}

def _get_json_formatter() -> logging.Formatter:
    """Return a JSON formatter for structured logging."""
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "message": record.getMessage(),
                "cycle": getattr(record, 'cycle', None),
                "component": getattr(record, 'component', 'unknown')
            }
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj)
    return JsonFormatter()

def init_cycle_logger(cycle_number: int, log_dir: Optional[str] = None) -> logging.Logger:
    """
    Initialize a structured JSON logger for a specific cycle.

    Args:
        cycle_number: The current cycle number (int).
        log_dir: Optional directory override. Uses config if None.

    Returns:
        A configured logger instance.
    """
    config = get_config()
    if log_dir is None:
        log_dir = os.path.join(config.paths.results, "logs")

    ensure_directories([log_dir])

    log_filename = f"cycle_{cycle_number}.log"
    log_path = os.path.join(log_dir, log_filename)

    logger_name = f"cycle_{cycle_number}_logger"

    if logger_name in _loggers:
        logger = _loggers[logger_name]
        # Update handler path if needed (in case of restarts)
        if logger.handlers:
            logger.handlers[0].baseFilename = log_path
        return logger

    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setFormatter(_get_json_formatter())
    logger.addHandler(file_handler)

    # Add a console handler for immediate feedback during dev
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    _loggers[logger_name] = logger
    return logger

def get_logger(cycle_number: int) -> logging.Logger:
    """Retrieve or initialize the logger for a given cycle."""
    return init_cycle_logger(cycle_number)

def get_cycle_history(cycle_number: int, log_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Read and parse the log file for a specific cycle to return history.

    Args:
        cycle_number: The cycle number to read.
        log_dir: Optional directory override.

    Returns:
        List of log entries as dictionaries.
    """
    config = get_config()
    if log_dir is None:
        log_dir = os.path.join(config.paths.results, "logs")

    log_path = os.path.join(log_dir, f"cycle_{cycle_number}.log")

    if not os.path.exists(log_path):
        return []

    history = []
    with open(log_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                history.append(entry)
            except json.JSONDecodeError:
                # Skip malformed lines
                continue
    return history

def log_cycle_summary(logger: logging.Logger, cycle_number: int, metrics: Dict[str, Any]) -> None:
    """
    Log a structured summary of a completed cycle.

    Args:
        logger: The logger instance.
        cycle_number: The cycle number.
        metrics: Dictionary of metrics (accuracy, loss, time, etc.).
    """
    extra = {'cycle': cycle_number, 'component': 'summary'}
    logger.info(f"Cycle {cycle_number} completed.", extra=extra)
    logger.info(json.dumps(metrics), extra=extra)

def log_error(logger: logging.Logger, cycle_number: int, error_msg: str, exc_info: Optional[Exception] = None) -> None:
    """
    Log a structured error event.

    Args:
        logger: The logger instance.
        cycle_number: The cycle number.
        error_msg: The error message.
        exc_info: Optional exception object for traceback.
    """
    extra = {'cycle': cycle_number, 'component': 'error'}
    logger.error(error_msg, extra=extra, exc_info=exc_info is not None)

def log_warning(logger: logging.Logger, cycle_number: int, warning_msg: str) -> None:
    """
    Log a structured warning event.

    Args:
        logger: The logger instance.
        cycle_number: The cycle number.
        warning_msg: The warning message.
    """
    extra = {'cycle': cycle_number, 'component': 'warning'}
    logger.warning(warning_msg, extra=extra)

def checkpoint_model_state(model: Any, cycle_number: int, checkpoint_dir: Optional[str] = None) -> str:
    """
    Save a model state dictionary to a checkpoint file and return the path.

    Args:
        model: The PyTorch model (or object with .state_dict()).
        cycle_number: The current cycle number.
        checkpoint_dir: Optional directory override.

    Returns:
        The absolute path to the saved checkpoint file.
    """
    import torch
    config = get_config()
    if checkpoint_dir is None:
        checkpoint_dir = os.path.join(config.paths.data, "checkpoints")

    ensure_directories([checkpoint_dir])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cycle_{cycle_number}_{timestamp}.pt"
    path = os.path.join(checkpoint_dir, filename)

    state = {
        'cycle': cycle_number,
        'timestamp': timestamp,
        'state_dict': model.state_dict() if hasattr(model, 'state_dict') else model,
        'config': str(config)
    }

    torch.save(state, path)
    return path

def update_cycle_log(cycle_number: int, event_type: str, details: Dict[str, Any]) -> None:
    """
    Append a structured event to the current cycle's log file directly.
    Useful for low-level logging without a logger instance.

    Args:
        cycle_number: The cycle number.
        event_type: Type of event (e.g., 'start', 'end', 'progress').
        details: Dictionary of event details.
    """
    config = get_config()
    log_dir = os.path.join(config.paths.results, "logs")
    ensure_directories([log_dir])

    log_path = os.path.join(log_dir, f"cycle_{cycle_number}.log")

    entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "details": details
    }

    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')
