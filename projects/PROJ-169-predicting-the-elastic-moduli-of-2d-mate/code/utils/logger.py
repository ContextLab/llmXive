import logging
import sys
import json
from pathlib import Path
from typing import Any, Dict, Optional
from rich.console import Console

_logger_instance = None
_console = Console()

def configure_log_file(log_path: Path):
    """Configure file logging."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logging.getLogger().addHandler(file_handler)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get a configured logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        _logger_instance.setLevel(logging.INFO)
        if not _logger_instance.handlers:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(logging.Formatter(
                '%(levelname)s: %(message)s'
            ))
            _logger_instance.addHandler(console_handler)
    return _logger_instance

def log_bias_check(logger: logging.Logger, report: Dict[str, Any]):
    """Log bias check results."""
    logger.info(f"Bias Check Report: {json.dumps(report, indent=2)}")

def log_exclusion_reason(logger: logging.Logger, reason: str, count: int):
    """Log exclusion reasons for data filtering."""
    logger.info(f"Exclusion: {reason} (count: {count})")
