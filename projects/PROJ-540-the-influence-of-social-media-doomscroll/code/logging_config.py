import logging
import sys
from pathlib import Path
from config import ensure_directories, load_config

def setup_logging(log_file: str = "outputs/analysis.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configure the project logging infrastructure.

    This function ensures the output directory exists, creates a file handler
    pointing to the specified log file, and attaches it to the root logger.
    It also configures a console handler for immediate feedback during execution.

    Args:
        log_file: Relative path to the log file (default: 'outputs/analysis.log').
        level: Logging level (default: logging.INFO).

    Returns:
        The root logger instance with configured handlers.
    """
    # Load config to ensure base directories exist
    config = load_config()
    ensure_directories(config)

    log_path = Path(log_file)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if root_logger.handlers:
        # Check if file handler already exists to avoid duplicates
        has_file_handler = any(isinstance(h, logging.FileHandler) for h in root_logger.handlers)
        if has_file_handler:
            return root_logger

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # File Handler
    try:
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        # Fallback to stderr if file cannot be created
        sys.stderr.write(f"Warning: Could not create log file {log_path}: {e}\n")

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging infrastructure initialized. Log file: {log_path.resolve()}")
    
    return root_logger
