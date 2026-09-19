"""
Logging infrastructure for the project.
Configures a unified logger that writes to both console and file.
"""
import logging
import sys
from pathlib import Path

# Project root directory (parent of 'code/')
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

def setup_logger(
    name: str = "llmXive",
    level: int = logging.INFO,
    log_file: Path = None
) -> Path:
    """
    Configures the root logger for the project.
    
    Args:
        name: Logger name (default: 'llmXive')
        level: Logging level (default: INFO)
        log_file: Optional custom log file path.
    
    Returns:
        Path to the log file being written to.
    """
    if log_file is None:
        log_file = LOG_FILE
    
    # Get root logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return log_file

    # Create formatters
    detailed_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    simple_format = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_format)

    # File Handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(detailed_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return log_file
