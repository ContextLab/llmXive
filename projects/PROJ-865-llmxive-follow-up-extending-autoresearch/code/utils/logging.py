import logging
import sys
import os
from pathlib import Path
from typing import Optional

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Create and configure a logger.
    
    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_stage_start(stage_name: str, logger: Optional[logging.Logger] = None) -> None:
    """Log the start of a pipeline stage."""
    if logger:
        logger.info(f"--- Starting Stage: {stage_name} ---")
    else:
        print(f"--- Starting Stage: {stage_name} ---")

def log_stage_end(stage_name: str, logger: Optional[logging.Logger] = None) -> None:
    """Log the end of a pipeline stage."""
    if logger:
        logger.info(f"--- Completed Stage: {stage_name} ---")
    else:
        print(f"--- Completed Stage: {stage_name} ---")

def log_resource_usage(logger: Optional[logging.Logger] = None) -> None:
    """Log current resource usage if psutil is available."""
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=0.1)
        
        msg = f"Resource Usage - Memory: {mem_mb:.2f} MB, CPU: {cpu_percent:.2f}%"
        if logger:
            logger.info(msg)
        else:
            print(msg)
    except ImportError:
        pass
    except Exception:
        pass
