import logging
import sys
from pathlib import Path
from code.config import ensure_dirs

def setup_logging(log_level: str = "INFO", log_file: str = "pipeline.log") -> None:
    """
    Configure the root logger for the project.
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: The filename for the log output relative to the project root.
    """
    # Ensure the log directory exists
    ensure_dirs()
    
    # Determine the absolute path for the log file
    log_path = Path(log_file)
    if not log_path.is_absolute():
        # Assume relative to project root (where code/ is a sibling)
        # We try to find the project root by looking for 'code' directory
        current = Path.cwd()
        while current != current.parent:
            if (current / "code").exists() and (current / "data").exists():
                log_path = current / log_file
                break
            current = current.parent
        else:
            # Fallback to current working directory if project structure not found
            log_path = Path.cwd() / log_file

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Clear existing handlers to avoid duplicates in re-runs
    logger.handlers.clear()
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File Handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger instance.
    
    Args:
        name: The name of the logger (usually __name__).
    
    Returns:
        A configured Logger instance.
    """
    return logging.getLogger(name)
