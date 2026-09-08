"""
Logging setup module.

Provides a consistent logging configuration across the project.
"""
import logging
import sys
import os
from datetime import datetime
from typing import Optional

def setup_logging(module_name: str, log_file: Optional[str] = None) -> Optional[logging.Logger]:
    """
    Setup logging for a specific module.
    
    Args:
        module_name: Name of the module (e.g., 'download_data')
        log_file: Optional path to log file. If None, logs to console only.
    
    Returns:
        Logger instance or None if setup fails.
    """
    try:
        logger = logging.getLogger(module_name)
        logger.setLevel(logging.INFO)
        
        # Avoid adding handlers multiple times
        if logger.handlers:
            return logger
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            # Ensure directory exists
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        return logger
        
    except Exception as e:
        # Fallback to basic logging if custom setup fails
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        return logging.getLogger(module_name)
