"""
Structured logging infrastructure.
Provides configurable loggers with support for structured bias checks.
"""
import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console
from rich.logging import RichHandler

# Global flag to enable/disable file output for bias checks
_log_file_path: Optional[Path] = None
_file_handler: Optional[logging.FileHandler] = None

def configure_log_file(output_path: Path) -> None:
    """
    Configure a file handler for structured logging (e.g., bias checks).
    Call this once at pipeline startup to enable file logging.
    """
    global _log_file_path, _file_handler

    if _file_handler:
        return  # Already configured

    _log_file_path = output_path
    _file_handler = logging.FileHandler(output_path)
    _file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    
    # Add to root logger so all children inherit it
    root_logger = logging.getLogger()
    if not any(isinstance(h, logging.FileHandler) for h in root_logger.handlers):
        root_logger.addHandler(_file_handler)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a configured logger instance.
    Uses Rich for pretty console output.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler with Rich
    console_handler = RichHandler(
        console=Console(stderr=False),
        show_time=True,
        show_path=False,
        markup=True,
    )
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(console_handler)

    return logger

def log_bias_check(logger: logging.Logger, check_name: str, details: Dict[str, Any], status: str = "PASS") -> None:
    """
    Log a structured bias check entry.
    
    Args:
        logger: The logger instance to use.
        check_name: Name of the bias check performed.
        details: Dictionary of key-value pairs describing the check results.
        status: Status of the check ('PASS', 'FAIL', 'WARN').
    """
    log_data = {
        "event": "bias_check",
        "check_name": check_name,
        "status": status,
        "details": details
    }
    
    # Log as JSON for structured parsing if file handler is active
    if _file_handler:
        logger.info(json.dumps(log_data))
    else:
        # Fallback to standard logging if no file configured
        logger.info(f"Bias Check [{status}]: {check_name} - {details}")

def log_exclusion_reason(logger: logging.Logger, entry_id: str, reason: str, category: str) -> None:
    """
    Log a specific exclusion reason for a dataset entry.
    
    Args:
        logger: The logger instance.
        entry_id: Unique identifier for the material entry.
        reason: The reason for exclusion.
        category: Category of the exclusion (e.g., 'missing_tensor', 'non_2d').
    """
    log_data = {
        "event": "entry_exclusion",
        "entry_id": entry_id,
        "category": category,
        "reason": reason
    }
    
    if _file_handler:
        logger.info(json.dumps(log_data))
    else:
        logger.warning(f"Excluded {entry_id}: {reason} (Category: {category})")