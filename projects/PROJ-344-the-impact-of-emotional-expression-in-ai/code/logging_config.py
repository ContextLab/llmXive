"""
Logging configuration for the llmXive research pipeline.

Provides deterministic logging and state tracking as per T006.
Ensures consistent log formats, file rotation, and state logging
to support reproducibility and debugging.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Ensure state directory exists (per T001)
STATE_DIR = Path("state")
STATE_DIR.mkdir(parents=True, exist_ok=True)

# Log file paths
LOG_FILE = STATE_DIR / "pipeline.log"
STATE_LOG_FILE = STATE_DIR / "state_log.csv"

# Deterministic log format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Global logger instance
_logger = None


def setup_logging(
    level: int = logging.INFO,
    log_file: Path = LOG_FILE,
    console: bool = True
) -> logging.Logger:
    """
    Configure and return the global logger instance.
    
    Args:
        level: Logging level (default: INFO)
        log_file: Path to log file
        console: Whether to log to console as well
    
    Returns:
        Configured logger instance
    """
    global _logger
    
    if _logger is not None:
        return _logger
    
    _logger = logging.getLogger("llmXive")
    _logger.setLevel(level)
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # File handler with rotation
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    _logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        _logger.addHandler(console_handler)
    
    _logger.info("Logging system initialized")
    return _logger


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a logger instance, creating it if necessary.
    
    Args:
        name: Logger name (default: "llmXive")
    
    Returns:
        Logger instance
    """
    if _logger is None:
        setup_logging()
    return logging.getLogger(name)


def log_state_event(
    event_type: str,
    task_id: str,
    status: str,
    details: dict = None,
    timestamp: datetime = None
) -> None:
    """
    Log a state event to the state log CSV file.
    
    Args:
        event_type: Type of event (e.g., "START", "COMPLETE", "ERROR")
        task_id: Task identifier
        status: Status of the task/event
        details: Additional details as a dictionary
        timestamp: Event timestamp (default: current time)
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Prepare CSV header if file doesn't exist
    if not STATE_LOG_FILE.exists():
        with open(STATE_LOG_FILE, 'w', newline='') as f:
            f.write("timestamp,event_type,task_id,status,details\n")
    
    # Format details as JSON string
    details_str = str(details) if details else ""
    
    # Append to state log
    with open(STATE_LOG_FILE, 'a', newline='') as f:
        f.write(f"{timestamp.isoformat()},{event_type},{task_id},{status},{details_str}\n")
    
    # Also log to main logger
    logger = get_logger()
    logger.info(f"STATE_EVENT: {event_type} | Task: {task_id} | Status: {status} | Details: {details_str}")


def log_pipeline_start(task_id: str, config: dict = None) -> None:
    """Log the start of a pipeline task."""
    log_state_event("START", task_id, "initiated", config)

def log_pipeline_complete(task_id: str, duration: float = None, metrics: dict = None) -> None:
    """Log the completion of a pipeline task."""
    details = {"duration_seconds": duration} if duration else {}
    if metrics:
        details.update(metrics)
    log_state_event("COMPLETE", task_id, "success", details)

def log_pipeline_error(task_id: str, error: str, traceback: str = None) -> None:
    """Log an error in a pipeline task."""
    details = {"error": error}
    if traceback:
        details["traceback"] = traceback
    log_state_event("ERROR", task_id, "failed", details)

def get_state_log_path() -> Path:
    """Return the path to the state log file."""
    return STATE_LOG_FILE

def get_log_file_path() -> Path:
    """Return the path to the main log file."""
    return LOG_FILE


# Initialize logger on module import if needed
if __name__ == "__main__":
    # Test logging functionality
    logger = setup_logging()
    logger.info("Testing logging system")
    log_state_event("TEST", "T006", "success", {"test": True})
    print(f"Log file: {get_log_file_path()}")
    print(f"State log: {get_state_log_path()}")
