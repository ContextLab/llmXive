import logging
import sys
from pathlib import Path
from typing import Optional

def setup_logging(log_file: Optional[str] = None) -> None:
    """
    Configure the root logger with a standard format and destination.
    
    Args:
        log_file: Optional path to a log file. If None, logs go to stdout.
    """
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    handlers = []
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    handlers.append(console_handler)
    
    # File handler (optional)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        handlers.append(file_handler)
    
    logging.basicConfig(
        level=logging.INFO,
        handlers=handlers,
        force=True
    )

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieve a logger instance.
    
    Args:
        name: Logger name. If None, returns the root logger.
    
    Returns:
        Configured logging.Logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)
