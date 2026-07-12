import logging
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_dir: str = "data/logs") -> None:
    """
    Configure the logging infrastructure for the project.
    
    Creates a logs directory and sets up:
    - Console logging (stdout) with color/clean formatting
    - File logging (rotating file handler) for persistent records
    
    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Relative path to the logs directory from project root
    """
    # Get the project root (assuming code/ is at root level)
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    
    # Ensure logs directory exists
    logs_dir = project_root / log_dir
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamped log filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"pipeline_{timestamp}.log"
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    
    # Setup file handler (rotating to avoid huge files)
    file_handler = logging.RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    logging.info(f"Logging infrastructure initialized. Log file: {log_file}")

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Name for the logger. If None, uses the module name.
        
    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)