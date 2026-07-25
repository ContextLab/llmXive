import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from config.settings import get_paths

# Global runtime tracking state
_runtime_start: Optional[float] = None
_runtime_end: Optional[float] = None
_logger: Optional[logging.Logger] = None

# Standard log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a logger with the specified name.
    Ensures the logger is configured with appropriate handlers and levels.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A configured logging.Logger instance.
    """
    global _logger
    
    if _logger is None:
        _logger = setup_pipeline_logging(name)
    else:
        # If logger exists but wasn't configured for this name, add handler if needed
        if not any(h.name == name or h.name == "llmXive" for h in _logger.handlers):
            _logger = setup_pipeline_logging(name)
    
    return logging.getLogger(name) if name != "llmXive" else _logger

def setup_pipeline_logging(name: str = "llmXive", level: int = logging.INFO) -> logging.Logger:
    """
    Configure the pipeline logging infrastructure.
    Creates log directory, file handler, and console handler.
    
    Args:
        name: The name for the logger.
        level: The logging level (default: INFO).
        
    Returns:
        A configured logging.Logger instance.
    """
    paths = get_paths()
    log_dir = paths["log_dir"]
    
    # Ensure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # File handler
    log_file = Path(log_dir) / "pipeline.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def start_runtime_tracking() -> None:
    """
    Start tracking the runtime of the pipeline.
    Records the start time in a global variable.
    """
    global _runtime_start
    _runtime_start = time.time()
    _runtime_end = None
    
    logger = get_logger()
    logger.info(f"Pipeline runtime tracking started at {datetime.now().isoformat()}")

def stop_runtime_tracking() -> Optional[float]:
    """
    Stop tracking the runtime and calculate the duration.
    
    Returns:
        The duration in seconds, or None if tracking was not started.
    """
    global _runtime_start, _runtime_end
    
    if _runtime_start is None:
        logger = get_logger()
        logger.warning("Runtime tracking was not started before stopping.")
        return None
    
    _runtime_end = time.time()
    duration = _runtime_end - _runtime_start
    
    logger = get_logger()
    logger.info(f"Pipeline runtime tracking stopped. Duration: {duration:.2f} seconds")
    
    return duration

def log_runtime_stats(stats: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Log runtime statistics and return a summary dictionary.
    
    Args:
        stats: Optional dictionary of additional statistics to include.
        
    Returns:
        A dictionary containing runtime statistics.
    """
    global _runtime_start, _runtime_end
    
    logger = get_logger()
    
    result = {
        "tracking_active": _runtime_start is not None,
        "start_time": datetime.fromtimestamp(_runtime_start).isoformat() if _runtime_start else None,
        "end_time": datetime.fromtimestamp(_runtime_end).isoformat() if _runtime_end else None,
        "duration_seconds": (_runtime_end - _runtime_start) if (_runtime_start and _runtime_end) else None
    }
    
    if stats:
        result.update(stats)
    
    logger.info(f"Runtime stats logged: {result}")
    
    return result

def main() -> None:
    """
    Main function to demonstrate logging infrastructure and runtime tracking.
    This function is intended for testing purposes.
    """
    logger = setup_pipeline_logging()
    logger.info("Logger infrastructure initialized.")
    
    start_runtime_tracking()
    
    # Simulate some work
    time.sleep(0.5)
    
    stop_runtime_tracking()
    
    runtime_stats = log_runtime_stats({"simulated_work": True})
    print(f"Runtime stats: {runtime_stats}")

if __name__ == "__main__":
    main()
