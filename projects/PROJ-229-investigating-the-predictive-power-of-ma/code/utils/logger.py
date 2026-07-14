import logging
import sys
from pathlib import Path
from typing import Optional
from config import get_config

_logger_instance: Optional[logging.Logger] = None
_logger_initialized: bool = False

def setup_logger(
    name: str = "llmXive_pipeline",
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure and return a logger instance with file and/or console handlers.
    
    Args:
        name: Logger name
        log_file: Optional path to log file. If None, only console output.
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        console_output: Whether to log to stdout/stderr
        
    Returns:
        Configured logging.Logger instance
    """
    global _logger_instance, _logger_initialized
    
    if _logger_initialized and _logger_instance and _logger_instance.name == name:
        return _logger_instance
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates on re-initialization
    logger.handlers.clear()
    
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(name)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _logger_instance = logger
    _logger_initialized = True
    
    return logger

def get_pipeline_logger() -> logging.Logger:
    """
    Get the global pipeline logger, initializing it if necessary.
    Uses configuration from config.yaml for log level and file path.
    
    Returns:
        Configured logging.Logger instance
    """
    global _logger_instance, _logger_initialized
    
    if _logger_initialized and _logger_instance:
        return _logger_instance
    
    try:
        config = get_config()
    except Exception:
        # Fallback if config is not yet available
        config = {}
    
    log_level_str = config.get('logging', {}).get('level', 'INFO')
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    
    log_file = config.get('logging', {}).get('log_file', 'data/results/pipeline.log')
    
    return setup_logger(
        name="llmXive_pipeline",
        log_file=log_file,
        level=log_level,
        console_output=True
    )
