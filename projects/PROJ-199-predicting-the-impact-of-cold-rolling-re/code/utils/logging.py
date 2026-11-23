import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

_logger_instance: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Returns a configured logger instance.
    Ensures a single logger configuration per process.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = logging.getLogger(name)
        if not _logger_instance.handlers:
            _logger_instance.setLevel(logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            _logger_instance.addHandler(handler)
    return _logger_instance

def setup_logging():
    """
    Basic setup for logging infrastructure.
    Called by entry points to ensure logging is ready.
    """
    pass

def configure_lineage(step_name: str, artifact_path: str):
    """
    Placeholder for lineage tracking.
    In a full implementation, this would log data provenance.
    """
    logger = get_logger()
    logger.info(f"Lineage: Step '{step_name}' produced '{artifact_path}'")

class LineageAdapter(logging.LoggerAdapter):
    """Adapter to add lineage context to log messages."""
    def process(self, msg, kwargs):
        return f"[Lineage] {msg}", kwargs
