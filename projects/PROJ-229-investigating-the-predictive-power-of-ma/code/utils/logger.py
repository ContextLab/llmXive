import logging
import sys
from pathlib import Path
from typing import Optional
import os
from config import get_config

_logger: Optional[logging.Logger] = None
_handler: Optional[logging.Handler] = None

def setup_logger(
    name: str = "llmXive",
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configure and return a singleton logger instance for the pipeline.
    
    Args:
        name: Logger name.
        log_file: Optional path to a log file. If None, logs only to stdout.
        level: Logging level (e.g., logging.DEBUG, logging.INFO).
    
    Returns:
        Configured logging.Logger instance.
    """
    global _logger, _handler
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    # Prevent adding multiple handlers if called repeatedly
    if _logger.handlers:
        return _logger

    # Create formatter
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    
    return _logger

def get_pipeline_logger() -> logging.Logger:
    """
    Retrieve the global pipeline logger.
    Initializes it if it hasn't been initialized yet.
    
    Returns:
        The global pipeline logger instance.
    """
    global _logger
    if _logger is None:
        config = get_config()
        log_level_str = config.get("logging", {}).get("level", "INFO")
        log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        log_file = config.get("logging", {}).get("log_file", "logs/pipeline.log")
        
        _logger = setup_logger(
            name="llmXive",
            log_file=log_file,
            level=log_level
        )
    return _logger
