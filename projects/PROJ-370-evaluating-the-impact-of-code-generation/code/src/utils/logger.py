"""
Logging infrastructure for the llmXive pipeline.

Provides:
- Structured logging configuration
- Runtime tracking (start/stop times, duration)
- Memory and timeout integration hooks
"""
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from code.config.settings import get_paths, ensure_directories


# Global state for runtime tracking
_pipeline_start_time: Optional[float] = None
_pipeline_start_datetime: Optional[datetime] = None
_runtime_logger: Optional[logging.Logger] = None


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    # Ensure log directory exists
    paths = get_paths()
    log_dir = Path(paths["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # File handler for pipeline logs
    file_handler = logging.FileHandler(
        log_dir / f"{name}.log",
        mode='a',
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter with timestamp, level, and message
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_pipeline_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure the main pipeline logging infrastructure.
    
    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Main pipeline logger
    """
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    
    level = level_map.get(log_level.upper(), logging.INFO)
    
    # Get paths and ensure directories exist
    paths = get_paths()
    ensure_directories()
    
    log_dir = Path(paths["logs"])
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # File handler for comprehensive pipeline log
    pipeline_log_file = log_dir / "pipeline.log"
    file_handler = logging.FileHandler(
        pipeline_log_file,
        mode='a',
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Detailed formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Also log to a dedicated runtime file
    runtime_logger = get_logger("runtime", level)
    runtime_logger.info("Pipeline logging initialized")
    
    return root_logger


def start_runtime_tracking() -> Dict[str, Any]:
    """
    Start runtime tracking for the pipeline execution.
    
    Returns:
        Dictionary with start time information
    """
    global _pipeline_start_time, _pipeline_start_datetime, _runtime_logger
    
    _pipeline_start_time = time.time()
    _pipeline_start_datetime = datetime.now()
    
    # Get or create runtime logger
    if _runtime_logger is None:
        _runtime_logger = get_logger("runtime")
    
    _runtime_logger.info(
        f"Pipeline started at {_pipeline_start_datetime.isoformat()}"
    )
    
    return {
        "start_time": _pipeline_start_time,
        "start_datetime": _pipeline_start_datetime.isoformat(),
        "status": "started"
    }


def stop_runtime_tracking() -> Dict[str, Any]:
    """
    Stop runtime tracking and calculate duration.
    
    Returns:
        Dictionary with end time and duration information
    """
    global _pipeline_start_time, _pipeline_start_datetime, _runtime_logger
    
    if _pipeline_start_time is None:
        raise RuntimeError("Runtime tracking was not started. Call start_runtime_tracking() first.")
    
    end_time = time.time()
    end_datetime = datetime.now()
    duration_seconds = end_time - _pipeline_start_time
    duration_minutes = duration_seconds / 60.0
    
    if _runtime_logger is None:
        _runtime_logger = get_logger("runtime")
    
    _runtime_logger.info(
        f"Pipeline completed at {end_datetime.isoformat()}"
    )
    _runtime_logger.info(f"Total duration: {duration_seconds:.2f} seconds ({duration_minutes:.2f} minutes)")
    
    # Reset global state
    _pipeline_start_time = None
    _pipeline_start_datetime = None
    
    return {
        "end_time": end_time,
        "end_datetime": end_datetime.isoformat(),
        "duration_seconds": duration_seconds,
        "duration_minutes": duration_minutes,
        "status": "completed"
    }


def log_runtime_stats(stats: Dict[str, Any]) -> None:
    """
    Log runtime statistics to the runtime logger.
    
    Args:
        stats: Dictionary of statistics to log
    """
    global _runtime_logger
    
    if _runtime_logger is None:
        _runtime_logger = get_logger("runtime")
    
    _runtime_logger.info("Runtime statistics:")
    for key, value in stats.items():
        _runtime_logger.info(f"  {key}: {value}")


def main() -> None:
    """
    Main entry point for testing the logger module.
    Demonstrates logging setup and runtime tracking.
    """
    # Setup pipeline logging
    logger = setup_pipeline_logging("INFO")
    
    logger.info("Starting logger module demonstration")
    
    # Start runtime tracking
    start_info = start_runtime_tracking()
    logger.info(f"Tracking started: {start_info['start_datetime']}")
    
    # Simulate some work
    logger.info("Simulating pipeline work...")
    time.sleep(0.5)
    logger.info("Work simulation complete")
    
    # Log some statistics
    stats = {
        "items_processed": 10,
        "errors_encountered": 0,
        "memory_usage_mb": 128
    }
    log_runtime_stats(stats)
    
    # Stop runtime tracking
    end_info = stop_runtime_tracking()
    logger.info(f"Tracking stopped: {end_info['end_datetime']}")
    logger.info(f"Duration: {end_info['duration_seconds']:.2f}s")
    
    logger.info("Logger module demonstration complete")


if __name__ == "__main__":
    main()
