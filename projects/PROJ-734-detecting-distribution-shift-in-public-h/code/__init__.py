"""
llmXive - Distribution Shift Detection Pipeline

This package provides the core infrastructure for detecting distribution shifts
in public health surveillance data using Kernel Two-Sample Tests.
"""

import logging
import sys
import os
from datetime import datetime
from typing import Any, Dict, Optional
import json

# Ensure the package directory is in the path for relative imports if running as script
# though typically this is handled by the runner.
_package_dir = os.path.dirname(os.path.abspath(__file__))
if _package_dir not in sys.path:
    sys.path.insert(0, _package_dir)

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_handler_added = False

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves or creates a logger for the llmXive pipeline.

    Args:
        name: The name of the logger (defaults to 'llmXive').

    Returns:
        A configured logging.Logger instance.
    """
    global _logger, _log_handler_added

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        # Prevent adding handlers multiple times if this module is re-imported
        if not _log_handler_added:
            # Create a console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)

            # Create a formatter with timestamp, level, and message
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
            console_handler.setFormatter(formatter)

            _logger.addHandler(console_handler)
            _log_handler_added = True

    return _logger

def log_runtime_params(params: Dict[str, Any], seed: Optional[int] = None) -> None:
    """
    Logs runtime parameters and the random seed used for reproducibility.

    This function formats the provided parameters into a JSON string and logs
    them at the INFO level. It is intended to be called at the start of the
    pipeline execution.

    Args:
        params: A dictionary of configuration parameters (e.g., window_size, alpha).
        seed: The random seed used for the experiment.
    """
    logger = get_logger()
    logger.info("Initializing pipeline with runtime parameters:")

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "seed": seed,
        "parameters": params
    }

    # Log the JSON string for structured parsing if needed, or just the dict repr
    # Using json.dumps for clean formatting
    logger.info(json.dumps(log_entry, indent=2))

def log_seed(seed: int) -> None:
    """
    Convenience function to log just the random seed.

    Args:
        seed: The integer seed value.
    """
    logger = get_logger()
    logger.info(f"Random seed set to: {seed}")

def log_event(event_name: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs a specific event with optional details.

    Args:
        event_name: A string identifier for the event (e.g., "DATA_LOAD_START").
        details: Optional dictionary of event-specific details.
    """
    logger = get_logger()
    msg = f"Event: {event_name}"
    if details:
        msg += f" | Details: {json.dumps(details)}"
    logger.info(msg)

__all__ = [
    "get_logger",
    "log_runtime_params",
    "log_seed",
    "log_event"
]
