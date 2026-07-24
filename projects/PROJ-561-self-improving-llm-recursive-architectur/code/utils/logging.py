"""
utils/logging.py

Structured cycle logging and checkpointing for the self-improving LLM pipeline.
Provides utilities to initialize cycle-specific loggers, update logs with metrics,
checkpoint model states, and retrieve historical cycle data.
"""
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from config import PathConfig

# Constants
LOG_LEVEL = logging.INFO
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_log_path(cycle_number: int, config: Optional[PathConfig] = None) -> str:
    """
    Generate the file path for a specific cycle's log.

    Args:
        cycle_number: The integer cycle number (e.g., 1, 2, 3).
        config: PathConfig instance. If None, uses default config.

    Returns:
        Absolute path to the log file for the given cycle.
    """
    if config is None:
        config = PathConfig()
    os.makedirs(config.results_dir, exist_ok=True)
    return os.path.join(config.results_dir, f"cycle_{cycle_number}.log")

def init_cycle_logger(cycle_number: int, config: Optional[PathConfig] = None) -> logging.Logger:
    """
    Initialize a dedicated logger for a specific cycle.

    Creates a file handler that writes to results/cycle_N.log and a console
    handler for immediate feedback.

    Args:
        cycle_number: The integer cycle number.
        config: PathConfig instance.

    Returns:
        Configured logging.Logger instance.
    """
    if config is None:
        config = PathConfig()

    logger_name = f"cycle_{cycle_number}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(LOG_LEVEL)

    # Prevent duplicate handlers if logger is reused
    if logger.handlers:
        logger.handlers.clear()

    # File handler
    log_path = get_log_path(cycle_number, config)
    file_handler = logging.FileHandler(log_path, mode='w')
    file_handler.setLevel(LOG_LEVEL)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)

    # Formatter
    formatter = logging.Formatter(
        f'%(asctime)s [%(levelname)s] [Cycle {cycle_number}] %(message)s',
        datefmt=DATE_FORMAT
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.info(f"Initialized logging for cycle {cycle_number}")
    logger.info(f"Log file: {log_path}")

    return logger

def update_cycle_log(
    logger: logging.Logger,
    cycle_number: int,
    metrics: Dict[str, Any],
    status: str = "running",
    message: Optional[str] = None,
    config: Optional[PathConfig] = None
) -> None:
    """
    Update the cycle log with new metrics and status.

    Args:
        logger: The initialized logger for this cycle.
        cycle_number: The cycle number.
        metrics: Dictionary of key-value metrics to log.
        status: Current status string (e.g., 'running', 'completed', 'failed').
        message: Optional human-readable message.
        config: PathConfig instance.
    """
    if message:
        logger.info(message)

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "cycle_number": cycle_number,
        "status": status,
        "metrics": metrics
    }

    # Log metrics as a JSON string for structured parsing later
    logger.info(f"Metrics update: {json.dumps(metrics)}")

    # Optionally append to a rolling summary file if needed
    summary_path = os.path.join(config.results_dir if config else "results", "cycle_summary.jsonl")
    os.makedirs(os.path.dirname(summary_path), exist_ok=True)
    with open(summary_path, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

def checkpoint_model_state(
    cycle_number: int,
    model_state: Dict[str, Any],
    optimizer_state: Optional[Dict[str, Any]] = None,
    config: Optional[PathConfig] = None
) -> str:
    """
    Save the model and optimizer state to disk.

    Args:
        cycle_number: The current cycle number.
        model_state: The model's state_dict.
        optimizer_state: The optimizer's state_dict (optional).
        config: PathConfig instance.

    Returns:
        Path to the saved checkpoint file.
    """
    if config is None:
        config = PathConfig()

    checkpoint_dir = os.path.join(config.data_dir, "checkpoints")
    os.makedirs(checkpoint_dir, exist_ok=True)

    checkpoint_path = os.path.join(checkpoint_dir, f"cycle_{cycle_number}.pt")

    checkpoint_data = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "model_state": model_state,
        "optimizer_state": optimizer_state
    }

    # Using torch.save would be ideal but we are restricted to standard lib + existing imports
    # Since config imports torch, we assume torch is available for saving complex dicts
    try:
        import torch
        torch.save(checkpoint_data, checkpoint_path)
    except ImportError:
        # Fallback to JSON if torch is somehow unavailable (unlikely given config)
        # Note: torch tensors cannot be serialized to JSON directly.
        # This fallback is a safety net; in practice, torch.save is expected.
        raise RuntimeError("Torch is required for checkpointing model states.")

    return checkpoint_path

def log_cycle_summary(
    cycle_number: int,
    final_metrics: Dict[str, Any],
    duration_seconds: float,
    status: str = "completed",
    config: Optional[PathConfig] = None
) -> None:
    """
    Log the final summary for a completed cycle.

    Args:
        cycle_number: The cycle number.
        final_metrics: Final metrics dictionary.
        duration_seconds: Total time taken for the cycle.
        status: Final status (e.g., 'completed', 'failed', 'timeout').
        config: PathConfig instance.
    """
    if config is None:
        config = PathConfig()

    logger = init_cycle_logger(cycle_number, config)
    
    summary = {
        "cycle_number": cycle_number,
        "status": status,
        "duration_seconds": duration_seconds,
        "final_metrics": final_metrics,
        "timestamp": datetime.now().isoformat()
    }

    logger.info(f"Cycle {cycle_number} finished with status: {status}")
    logger.info(f"Duration: {duration_seconds:.2f}s")
    logger.info(f"Final Metrics: {json.dumps(final_metrics)}")

    # Append to trajectory summary if not already done by run_single_cycle
    # This ensures a persistent log of cycle summaries
    summary_path = os.path.join(config.results_dir, "cycle_summaries.jsonl")
    with open(summary_path, 'a') as f:
        f.write(json.dumps(summary) + "\n")

def get_cycle_history(cycle_number: int, config: Optional[PathConfig] = None) -> List[Dict[str, Any]]:
    """
    Retrieve the history of log entries for a specific cycle or all previous cycles.

    Args:
        cycle_number: If specified, returns history for this cycle. 
                      If None, returns history for all cycles.
        config: PathConfig instance.

    Returns:
        List of log entries (dicts) parsed from the summary file.
    """
    if config is None:
        config = PathConfig()

    summary_path = os.path.join(config.results_dir, "cycle_summaries.jsonl")
    history = []

    if not os.path.exists(summary_path):
        return history

    with open(summary_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if cycle_number is None or entry.get("cycle_number") == cycle_number:
                    history.append(entry)
            except json.JSONDecodeError:
                continue

    return history