import logging
import sys
from pathlib import Path
from typing import Optional

_logger = None

def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """Configure logging for the project."""
    global _logger
    
    if _logger:
        return _logger
    
    # Create logger
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    if _logger is None:
        setup_logging()
    if name:
        return _logger.getChild(name)
    return _logger
