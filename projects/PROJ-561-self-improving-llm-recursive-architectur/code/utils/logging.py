"""
utils/logging.py

Structured cycle logging and checkpointing for the self-improving LLM pipeline.
Provides functions to initialize cycle-specific loggers, update logs with metrics,
checkpoint model states, and retrieve cycle history.
"""

import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import get_config

# Constants
LOG_DIR = "results/logs"
CHECKPOINT_DIR = "data/checkpoints"
HISTORY_FILE = "results/cycle_history.json"

def get_log_path(cycle_number: int) -> str:
    """
    Construct the full path for a cycle's log file.

    Args:
        cycle_number: The integer cycle number.

    Returns:
        Full path to the log file (e.g., results/logs/cycle_1.log).
    """
    os.makedirs(LOG_DIR, exist_ok=True)
    return os.path.join(LOG_DIR, f"cycle_{cycle_number}.log")

def init_cycle_logger(cycle_number: int, level: int = logging.INFO) -> logging.Logger:
    """
    Initialize a structured logger for a specific cycle.

    Creates a file handler that appends to the cycle's log file and a
    stream handler for console output.

    Args:
        cycle_number: The integer cycle number.
        level: Logging level (default: INFO).

    Returns:
        Configured Logger instance.
    """
    log_path = get_log_path(cycle_number)
    logger_name = f"cycle_{cycle_number}"

    # Prevent duplicate handlers if logger already exists
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.handlers = []  # Clear existing handlers to avoid duplicates

    # File handler
    fh = logging.FileHandler(log_path, mode='a')
    fh.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # Stream handler
    sh = logging.StreamHandler()
    sh.setLevel(level)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    logger.info(f"Initialized logger for cycle {cycle_number}")
    return logger

def update_cycle_log(cycle_number: int, key: str, value: Any, logger: Optional[logging.Logger] = None) -> None:
    """
    Append a key-value pair to the cycle's log file.

    Args:
        cycle_number: The integer cycle number.
        key: The metric or event key.
        value: The value to log.
        logger: Optional logger instance. If None, creates a temporary one.
    """
    if logger is None:
        logger = init_cycle_logger(cycle_number)

    logger.info(f"{key}: {value}")

def checkpoint_model_state(
    cycle_number: int,
    model_state: Dict[str, Any],
    optimizer_state: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, Any]] = None,
    logger: Optional[logging.Logger] = None
) -> str:
    """
    Save model and optimizer states to disk.

    Args:
        cycle_number: The integer cycle number.
        model_state: Dictionary containing model state dict.
        optimizer_state: Optional dictionary containing optimizer state dict.
        metrics: Optional dictionary containing current cycle metrics.
        logger: Optional logger instance.

    Returns:
        Path to the saved checkpoint file.
    """
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    checkpoint_path = os.path.join(CHECKPOINT_DIR, f"cycle_{cycle_number}.pt")

    # Since we cannot use torch.save directly without torch in this file's imports,
    # and the API surface shows torch is available in utils.memory, we will assume
    # the caller handles the torch import if needed, but here we serialize to JSON
    # for metadata and structure if possible, or raise an error if complex tensors are present.
    # However, the task requires "checkpointing". The standard way in this project
    # implies using torch. Let's assume the caller passes a serializable dict
    # or we use a hybrid approach.
    # Given the constraints of "real code", we must use torch if we are saving weights.
    # But the API surface for utils/logging does not import torch.
    # We will implement a JSON-based metadata log and a placeholder for the binary state,
    # OR we assume the environment allows dynamic import.
    # To be safe and strictly follow "real runnable code", we will use torch if available,
    # otherwise we log a warning.
    # Actually, the task says "checkpointing". Let's try to import torch dynamically.
    try:
        import torch
        checkpoint = {
            'cycle': cycle_number,
            'timestamp': datetime.now().isoformat(),
            'model_state_dict': model_state,
            'optimizer_state_dict': optimizer_state,
            'metrics': metrics
        }
        torch.save(checkpoint, checkpoint_path)
    except ImportError:
        # Fallback: Save metadata as JSON if torch is not available (unlikely in this context)
        # But for a real checkpoint, we need torch. We will raise if torch is missing
        # and binary saving is required.
        raise RuntimeError("torch is required for model checkpointing.")

    if logger:
        logger.info(f"Checkpoint saved to {checkpoint_path}")
    else:
        print(f"Checkpoint saved to {checkpoint_path}")

    return checkpoint_path

def log_cycle_summary(
    cycle_number: int,
    metrics: Dict[str, Any],
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Log a structured summary of the cycle's performance.

    Args:
        cycle_number: The integer cycle number.
        metrics: Dictionary of metrics (e.g., loss, accuracy, time).
        logger: Optional logger instance.
    """
    if logger is None:
        logger = init_cycle_logger(cycle_number)

    logger.info(f"--- Cycle {cycle_number} Summary ---")
    for key, value in metrics.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"----------------------------------")

    # Also update the persistent history file
    history_entry = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics
    }

    history = get_cycle_history()
    history.append(history_entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

def get_cycle_history() -> List[Dict[str, Any]]:
    """
    Retrieve the history of all completed cycles.

    Returns:
        List of dictionaries, each representing a cycle's history entry.
        Returns an empty list if no history exists.
    """
    if not os.path.exists(HISTORY_FILE):
        return []

    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def log_error(cycle_number: int, error_message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log an error message for a specific cycle.

    Args:
        cycle_number: The integer cycle number.
        error_message: The error description.
        logger: Optional logger instance.
    """
    if logger is None:
        logger = init_cycle_logger(cycle_number)
    logger.error(f"ERROR: {error_message}")

def log_warning(cycle_number: int, warning_message: str, logger: Optional[logging.Logger] = None) -> None:
    """
    Log a warning message for a specific cycle.

    Args:
        cycle_number: The integer cycle number.
        warning_message: The warning description.
        logger: Optional logger instance.
    """
    if logger is None:
        logger = init_cycle_logger(cycle_number)
    logger.warning(f"WARNING: {warning_message}")
