"""
Logging configuration for the code maintainability impact study.
Provides standardized logging setup to ensure consistency across the pipeline.
"""
import logging
import sys
from pathlib import Path
from llmxive_toolkit import get_logger as toolkit_get_logger

def setup_project_logging(name: str, log_file: str) -> logging.Logger:
    """
    Configure a logger that writes to both a specific file and stdout.
    
    Args:
        name: Name of the logger.
        log_file: Path to the log file.
        
    Returns:
        A configured logging.Logger instance.
    """
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding duplicate handlers if the logger is already configured
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # File handler for persistent logs
        fh = logging.FileHandler(log_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
        # Stream handler for real-time console output
        sh = logging.StreamHandler(sys.stdout)
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
    return logger

def setup_logging():
    """
    General logging setup wrapper used by several pipeline scripts.
    Defaults to a project-level log file.
    """
    return setup_project_logging("project", "data/logs/project.log")

def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger instance. Wraps the toolkit logger to maintain
    compatibility with scripts importing from this module.
    """
    return toolkit_get_logger(name)
