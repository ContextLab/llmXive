import logging
import os
import sys
from pathlib import Path
from typing import Optional

# Ensure the data directory exists for log file output
LOG_DIR = Path("data")
LOG_FILE = LOG_DIR / "run_logs.txt"

# Ensure the directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configure the root logger to avoid duplicate handlers if called multiple times
# We use a flag to track if setup has occurred to prevent handler duplication
_setup_done = False

def setup_logging(log_file: Optional[Path] = None, level: int = logging.INFO) -> None:
    """
    Configure the root logger to output to both console and a file.
    
    Args:
        log_file: Path to the log file. Defaults to data/run_logs.txt.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    """
    global _setup_done
    if _setup_done:
        return

    if log_file is None:
        log_file = LOG_FILE
    
    # Ensure directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter with timestamp, level, and message
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to prevent duplicates on re-runs in same process
    root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    _setup_done = True

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    The logger will inherit the configuration set up by setup_logging().
    
    Args:
        name: Name of the logger (typically __name__ of the module).
        
    Returns:
        Configured Logger instance.
    """
    # Ensure logging is configured
    setup_logging()
    return logging.getLogger(name)

# Initialize logging immediately upon import for convenience, 
# but allow explicit setup_logging() calls to override or initialize if needed.
setup_logging()