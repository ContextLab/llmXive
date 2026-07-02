import logging
import sys
from pathlib import Path
from config import ensure_directories, load_config

def setup_logging(log_file: str = "outputs/analysis.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configure the project logging infrastructure.
    
    Sets up a logger that writes to both the console and a file.
    Ensures the output directory exists before creating the log file.
    
    Args:
        log_file: Relative path to the log file from project root.
        level: Logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        The configured root logger.
    """
    # Ensure the output directory exists
    ensure_directories()
    
    # Get the project root (assuming this file is in code/, so root is parent)
    project_root = Path(__file__).resolve().parent.parent
    log_path = project_root / log_file
    
    # Create the log directory if it doesn't exist
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure the root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates on re-runs
    if logger.handlers:
        logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(file_formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger
