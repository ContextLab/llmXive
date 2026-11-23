import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_DIR = os.path.join(PROJECT_ROOT, "state")

# Ensure state directory exists
os.makedirs(STATE_DIR, exist_ok=True)

def get_logger(name: str = "research_pipeline") -> logging.Logger:
    """
    Gets or creates a logger with standard formatting.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File Handler
    log_file = os.path.join(STATE_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    fh = logging.FileHandler(log_file)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    return logger

def log_state_event(event_name: str, data: dict) -> None:
    """Logs a state event to a dedicated state log."""
    logger = get_logger()
    timestamp = datetime.now().isoformat()
    msg = f"STATE_EVENT: {event_name} | {data}"
    logger.info(msg)
    
    # Append to a specific state log file
    state_log_path = os.path.join(STATE_DIR, "state_events.log")
    with open(state_log_path, "a") as f:
        f.write(f"{timestamp} | {msg}\n")

def log_pipeline_start() -> None:
    logger = get_logger()
    logger.info("Pipeline started.")
    log_state_event("pipeline_start", {})

def log_pipeline_complete() -> None:
    logger = get_logger()
    logger.info("Pipeline completed successfully.")
    log_state_event("pipeline_complete", {})

def log_pipeline_error(error_msg: str) -> None:
    logger = get_logger()
    logger.error(f"Pipeline error: {error_msg}")
    log_state_event("pipeline_error", {"error": error_msg})

def get_state_log_path() -> str:
    return os.path.join(STATE_DIR, "state_events.log")

def get_log_file_path() -> str:
    return os.path.join(STATE_DIR, f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
