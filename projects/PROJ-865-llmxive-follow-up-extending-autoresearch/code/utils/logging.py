import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

# Configure logging
LOG_DIR = Path(__file__).parent.parent.parent / "data" / "artifacts"
LOG_DIR.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Get a logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_path = LOG_DIR / log_file
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)
    
    return logger

def log_stage_start(stage_name: str, message: str) -> None:
    """Log the start of a pipeline stage."""
    logger = get_logger(stage_name)
    logger.info(f"=== STAGE START: {stage_name} ===")
    logger.info(f"Message: {message}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")

def log_stage_end(stage_name: str, message: str, success: bool = True) -> None:
    """Log the end of a pipeline stage."""
    logger = get_logger(stage_name)
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"=== STAGE END: {stage_name} [{status}] ===")
    logger.info(f"Message: {message}")
    logger.info(f"Timestamp: {datetime.now().isoformat()}")

def log_resource_usage(stage_name: str) -> None:
    """Log current resource usage."""
    import psutil
    logger = get_logger(stage_name)
    
    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024 * 1024)
    cpu_percent = process.cpu_percent()
    
    logger.info(f"Resource Usage - Memory: {memory_mb:.2f}MB, CPU: {cpu_percent}%")

def log_metric(stage_name: str, metric_name: str, value: float) -> None:
    """Log a metric value."""
    logger = get_logger(stage_name)
    logger.info(f"METRIC: {metric_name} = {value}")
