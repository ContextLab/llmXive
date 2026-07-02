import logging
import os
import platform
import sys
import socket
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Dict, Any

# Global logger registry
_loggers: Dict[str, logging.Logger] = {}

def setup_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    console: bool = True
) -> logging.Logger:
    """
    Setup a logger with optional file and console handlers.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        level: Logging level
        console: Whether to log to console
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    if console:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    _loggers[name] = logger
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger by name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)

def log_environment():
    """Log current environment details for reproducibility."""
    logger = get_logger(__name__)
    logger.info("=== Environment Details ===")
    logger.info(f"Python Version: {sys.version}")
    logger.info(f"OS: {platform.system()} {platform.release()}")
    logger.info(f"Hostname: {socket.gethostname()}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Environment Variables (selected):")
    for key in ['PATH', 'PYTHONPATH', 'HOME']:
        if key in os.environ:
            logger.info(f"  {key}: {os.environ[key][:50]}...")

def log_random_seed(seed: int):
    """Log the random seed used for reproducibility."""
    logger = get_logger(__name__)
    logger.info(f"Random seed set to: {seed}")

def log_model_versions(models: Dict[str, str]):
    """Log model versions used in the experiment."""
    logger = get_logger(__name__)
    logger.info("=== Model Versions ===")
    for name, version in models.items():
        logger.info(f"{name}: {version}")

def log_configuration(config: Dict[str, Any]):
    """Log the experiment configuration."""
    logger = get_logger(__name__)
    logger.info("=== Configuration ===")
    for key, value in config.items():
        logger.info(f"{key}: {value}")

def main():
    """Test logging functions."""
    setup_logger("test", console=True)
    log_environment()
    log_random_seed(42)
    log_model_versions({"test_model": "v1.0"})

if __name__ == "__main__":
    main()