"""
Structured cycle logging and checkpointing for the self-improving LLM pipeline.

This module provides utilities for:
- Creating structured log files per refinement cycle
- Logging cycle summaries with metrics
- Checkpointing model states and intermediate results
- Retrieving cycle history for trajectory analysis
"""
import json
import os
import time
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import path config to ensure consistency with project structure
# We assume config.py is in the root code/ directory
try:
    from config import get_config
except ImportError:
    # Fallback for direct execution without config
    class FallbackConfig:
        def get_path_config(self):
            return type('obj', (object,), {'results_dir': 'results', 'data_dir': 'data'})()
    _config = FallbackConfig()

# Constants
LOG_EXTENSION = ".log"
CHECKPOINT_EXTENSION = ".pt"
SUMMARY_FILE = "cycle_summary.json"
HISTORY_FILE = "cycle_history.json"


def get_log_path(cycle_number: int, log_dir: Optional[str] = None) -> str:
    """
    Generate the full path for a cycle log file.
    
    Args:
        cycle_number: The cycle number (integer)
        log_dir: Optional override for the log directory. Defaults to results/logs/
    
    Returns:
        Full path to the log file
    """
    if log_dir is None:
        try:
            config = get_config()
            log_dir = os.path.join(config.results_dir, "logs")
        except (ImportError, AttributeError):
            log_dir = "results/logs"
    
    os.makedirs(log_dir, exist_ok=True)
    return os.path.join(log_dir, f"cycle_{cycle_number}{LOG_EXTENSION}")


def init_cycle_logger(cycle_number: int, log_file: Optional[str] = None) -> logging.Logger:
    """
    Initialize a structured logger for a specific refinement cycle.
    
    Args:
        cycle_number: The cycle number
        log_file: Optional override for the log file path
    
    Returns:
        Configured logger instance
    """
    if log_file is None:
        log_file = get_log_path(cycle_number)
    
    logger_name = f"cycle_{cycle_number}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='w')
    file_handler.setLevel(logging.INFO)
    
    # Structured formatter with ISO timestamp and cycle info
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Also log to console for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Initialized logger for cycle {cycle_number}")
    return logger


def update_cycle_log(cycle_number: int, message: str, log_file: Optional[str] = None, level: str = "INFO") -> None:
    """
    Update an existing cycle log with a new message.
    
    Args:
        cycle_number: The cycle number
        message: The log message
        log_file: Optional override for the log file path
        level: Log level (INFO, WARNING, ERROR, DEBUG)
    """
    if log_file is None:
        log_file = get_log_path(cycle_number)
    
    logger_name = f"cycle_{cycle_number}"
    logger = logging.getLogger(logger_name)
    
    if not logger.handlers:
        logger = init_cycle_logger(cycle_number, log_file)
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message)


def checkpoint_model_state(
    cycle_number: int,
    model_state: Dict[str, Any],
    optimizer_state: Optional[Dict[str, Any]] = None,
    metrics: Optional[Dict[str, float]] = None,
    checkpoint_dir: Optional[str] = None
) -> str:
    """
    Save a checkpoint of the model state and associated metadata.
    
    Args:
        cycle_number: The current cycle number
        model_state: The model's state_dict or equivalent
        optimizer_state: Optional optimizer state_dict
        metrics: Optional dictionary of metrics to store with the checkpoint
        checkpoint_dir: Optional override for checkpoint directory
    
    Returns:
        Path to the saved checkpoint file
    """
    if checkpoint_dir is None:
        try:
            config = get_config()
            checkpoint_dir = os.path.join(config.data_dir, "checkpoints")
        except (ImportError, AttributeError):
            checkpoint_dir = "data/checkpoints"
    
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    checkpoint_path = os.path.join(checkpoint_dir, f"cycle_{cycle_number}{CHECKPOINT_EXTENSION}")
    
    checkpoint_data = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "model_state": model_state,
    }
    
    if optimizer_state is not None:
        checkpoint_data["optimizer_state"] = optimizer_state
    
    if metrics is not None:
        checkpoint_data["metrics"] = metrics
    
    # Use torch.save if available, otherwise fallback to json for dicts
    try:
        import torch
        torch.save(checkpoint_data, checkpoint_path)
    except ImportError:
        # Fallback to JSON for pure dict structures (less efficient for tensors)
        with open(checkpoint_path.replace(CHECKPOINT_EXTENSION, ".json"), 'w') as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        checkpoint_path = checkpoint_path.replace(CHECKPOINT_EXTENSION, ".json")
    
    return checkpoint_path


def log_cycle_summary(
    cycle_number: int,
    metrics: Dict[str, float],
    modification_proposal: Optional[Dict[str, Any]] = None,
    duration_seconds: Optional[float] = None,
    trajectory_file: Optional[str] = None
) -> None:
    """
    Log a summary of a completed cycle to the trajectory file and cycle log.
    
    Args:
        cycle_number: The cycle number
        metrics: Dictionary of metrics (e.g., accuracy, loss, FLOPs)
        modification_proposal: The modification proposal applied in this cycle
        duration_seconds: Total time taken for the cycle
        trajectory_file: Optional override for the trajectory file path
    """
    summary = {
        "cycle_number": cycle_number,
        "timestamp": datetime.now().isoformat(),
        "metrics": metrics,
        "modification_proposal": modification_proposal,
        "duration_seconds": duration_seconds,
    }
    
    # Log to cycle-specific log file
    logger = init_cycle_logger(cycle_number)
    logger.info(f"Cycle {cycle_number} summary: {json.dumps(metrics)}")
    
    # Append to trajectory file
    if trajectory_file is None:
        try:
            config = get_config()
            trajectory_file = os.path.join(config.results_dir, "trajectory.json")
        except (ImportError, AttributeError):
            trajectory_file = "results/trajectory.json"
    
    os.makedirs(os.path.dirname(trajectory_file), exist_ok=True)
    
    # Read existing trajectory or initialize
    trajectory_data = []
    if os.path.exists(trajectory_file):
        try:
            with open(trajectory_file, 'r') as f:
                trajectory_data = json.load(f)
        except json.JSONDecodeError:
            trajectory_data = []
    
    trajectory_data.append(summary)
    
    with open(trajectory_file, 'w') as f:
        json.dump(trajectory_data, f, indent=2)
    
    logger.info(f"Appended summary to trajectory file: {trajectory_file}")


def get_cycle_history(
    trajectory_file: Optional[str] = None,
    start_cycle: Optional[int] = None,
    end_cycle: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Retrieve the history of all cycles from the trajectory file.
    
    Args:
        trajectory_file: Optional override for the trajectory file path
        start_cycle: Optional start cycle number (inclusive)
        end_cycle: Optional end cycle number (inclusive)
    
    Returns:
        List of cycle summary dictionaries
    """
    if trajectory_file is None:
        try:
            config = get_config()
            trajectory_file = os.path.join(config.results_dir, "trajectory.json")
        except (ImportError, AttributeError):
            trajectory_file = "results/trajectory.json"
    
    if not os.path.exists(trajectory_file):
        return []
    
    try:
        with open(trajectory_file, 'r') as f:
            history = json.load(f)
    except json.JSONDecodeError:
        return []
    
    # Filter by cycle range if specified
    if start_cycle is not None:
        history = [entry for entry in history if entry.get("cycle_number", 0) >= start_cycle]
    if end_cycle is not None:
        history = [entry for entry in history if entry.get("cycle_number", 0) <= end_cycle]
    
    return history