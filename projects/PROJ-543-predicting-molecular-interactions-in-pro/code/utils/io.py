"""
Robust logging infrastructure for memory and time tracking.

This module provides utilities to:
- Track wall-clock time for experiment phases.
- Monitor memory footprint (RSS) to ensure compliance with SC-005 (7 GB limit).
- Log structured JSON events to `data/results/experiment_log.jsonl`.
- Raise exceptions if memory limits are exceeded.
"""

import json
import os
import time
import resource
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from utils.config import ConfigManager

# Constants
MEMORY_LIMIT_GB = 7.0
LOG_FILE_NAME = "experiment_log.jsonl"
LOGS_DIR = Path("data/results")

# Ensure log directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def get_memory_usage_mb() -> float:
    """
    Returns the current Resident Set Size (RSS) memory usage in MB.
    Uses resource.getrusage for Unix-like systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def check_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> bool:
    """
    Checks if current memory usage is within the specified limit.
    Returns True if within limit, False otherwise.
    """
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024.0
    return current_mb < limit_mb

def enforce_memory_limit(limit_gb: float = MEMORY_LIMIT_GB) -> None:
    """
    Checks memory usage and raises a MemoryError if the limit is exceeded.
    This enforces SC-005.
    """
    current_mb = get_memory_usage_mb()
    limit_mb = limit_gb * 1024.0
    if current_mb >= limit_mb:
        raise MemoryError(
            f"Memory limit exceeded: Current usage {current_mb:.2f} MB "
            f">= Limit {limit_mb:.2f} MB (SC-005 violation)."
        )

class Timer:
    """
    Context manager and utility for tracking wall-clock time.
    """
    def __init__(self, label: str = "Operation"):
        self.label = label
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        log_event(
            event_type="timer_stop",
            data={
                "label": self.label,
                "duration_seconds": self.duration,
                "timestamp": datetime.now().isoformat()
            }
        )
        return False

    def elapsed(self) -> float:
        """Returns elapsed time in seconds so far."""
        if self.start_time is None:
            return 0.0
        current = time.time()
        if self.end_time is not None:
            return self.end_time - self.start_time
        return current - self.start_time

def log_event(event_type: str, data: Dict[str, Any]) -> None:
    """
    Appends a structured JSON log entry to the experiment log file.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data
    }
    log_path = LOGS_DIR / LOG_FILE_NAME
    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def initialize_logging(config: Optional[ConfigManager] = None) -> logging.Logger:
    """
    Configures the root logger and returns a project-specific logger.
    Logs are also written to console and file.
    """
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGS_DIR / "experiment.log")
        ]
    )
    logger = logging.getLogger("llmXive")

    if config:
        log_event(
            event_type="experiment_start",
            data={
                "config_seed": config.seed,
                "hyperparameters": config.hyperparameters,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    return logger