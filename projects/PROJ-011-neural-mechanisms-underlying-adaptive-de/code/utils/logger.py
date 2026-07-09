"""
Logging utility for the project.
Provides a centralized logger configuration to track QC failures and model convergence.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# Global logger instance
_logger: Optional[logging.Logger] = None

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves or creates a logger with the specified name.
    Configures it to output to stdout and optionally to a file if configured.
    """
    global _logger
    
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.INFO)
        
        # Avoid adding handlers multiple times if called repeatedly
        if not _logger.handlers:
            # Console handler
            ch = logging.StreamHandler(sys.stdout)
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            ch.setFormatter(formatter)
            _logger.addHandler(ch)
    
    return logging.getLogger(name)

def setup_file_logging(log_file: Path, level: int = logging.INFO):
    """
    Configures file logging for the project.
    """
    global _logger
    if _logger is None:
        _logger = get_logger()
    
    if not _logger.handlers or not any(isinstance(h, logging.FileHandler) for h in _logger.handlers):
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        _logger.addHandler(fh)