"""
Logging infrastructure setup for the CMB analysis pipeline.
Provides consistent logging configuration across all modules.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level: str = "INFO", log_dir: Path = None) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files. Defaults to data/logs/
        
    Returns:
        Configured logger instance
    """
    # Set up log directory
    if log_dir is None:
        base_path = Path(__file__).resolve().parent.parent
        log_dir = base_path / "data" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"cmb_analysis_{timestamp}.log"
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers = []
    
    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Create project logger
    project_logger = logging.getLogger("cmb_analysis")
    project_logger.info(f"Logging initialized. Log file: {log_file}")
    
    return project_logger

def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name. If None, returns the project logger.
        
    Returns:
        Logger instance
    """
    if name is None:
        return logging.getLogger("cmb_analysis")
    return logging.getLogger(f"cmb_analysis.{name}")

def main():
    """
    Test the logging setup by creating a logger and logging some messages.
    """
    logger = setup_logging()
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print(f"\nLogging setup complete. Check data/logs/ for log files.")

if __name__ == "__main__":
    main()
