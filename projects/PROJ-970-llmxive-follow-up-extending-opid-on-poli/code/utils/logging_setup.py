import logging
import os
import sys
from datetime import datetime
from typing import Optional

def setup_logging(
    log_level: int = logging.INFO,
    log_dir: str = "data/logs",
    log_file_prefix: str = "opid_experiment"
) -> None:
    """
    Configures the root logger for the project.
    
    Sets up:
    - Console output (stdout) with color codes if available (simplified here to standard format)
    - File output rotating log file in data/logs/
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO)
        log_dir: Directory where log files will be stored
        log_file_prefix: Prefix for the log filename
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{log_file_prefix}_{timestamp}.log"
    log_filepath = os.path.join(log_dir, log_filename)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    file_handler = logging.FileHandler(log_filepath, mode='a', encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    if root_logger.handlers:
        root_logger.handlers.clear()
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Log the setup completion
    logging.info(f"Logging initialized. Log file: {log_filepath}")

def get_experiment_logger(
    name: Optional[str] = None,
    log_level: int = logging.INFO
) -> logging.Logger:
    """
    Retrieves or creates a named logger for specific experiment components.
    
    Args:
        name: Optional name for the logger (e.g., 'GraphGenerator', 'OPIDRouter')
             If None, returns the root logger.
        log_level: Optional log level override for this specific logger.
    
    Returns:
        A configured logging.Logger instance.
    """
    if name is None:
        logger = logging.getLogger()
    else:
        logger = logging.getLogger(name)
    
    logger.setLevel(log_level)
    return logger
