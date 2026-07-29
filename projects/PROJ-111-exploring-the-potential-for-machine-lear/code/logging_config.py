import logging
import sys
import os
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_file: str = None, log_dir: str = "logs") -> logging.Logger:
    """
    Configures the project's logging infrastructure.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional relative path for the log file.
        log_dir: Directory to store log files.
    
    Returns:
        A configured logger instance.
    """
    # Ensure log directory exists
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Determine log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File Handler (if log_file is specified)
    if log_file:
        # Handle absolute vs relative paths
        if os.path.isabs(log_file):
            full_log_path = Path(log_file)
        else:
            full_log_path = log_path / log_file
        
        # Ensure parent directory for log file exists
        full_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(full_log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Create a specific logger for this project
    project_logger = logging.getLogger("llmXive")
    project_logger.setLevel(level)
    
    # Log startup message
    project_logger.info("Logging infrastructure initialized successfully.")
    project_logger.info(f"Log level set to: {log_level}")
    if log_file:
        project_logger.info(f"Logs will be written to: {full_log_path}")
    
    return project_logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves a logger by name, ensuring it inherits the root configuration.
    """
    return logging.getLogger(name)
