"""
Logger utility for the LLMXive research pipeline.

Provides structured logging, runtime tracking, and memory/CPU monitoring hooks.
Integrates with the project's timeout and memory watchdog systems.
"""
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from code.config.settings import get_paths, ensure_directories


# Global state for runtime tracking
_start_time: Optional[float] = None
_start_datetime: Optional[datetime] = None
_runtime_logger: Optional[logging.Logger] = None
_runtime_stats: Dict[str, Any] = {
    "total_runtime_seconds": 0,
    "pr_processed_count": 0,
    "pr_skipped_count": 0,
    "errors_count": 0,
    "warnings_count": 0,
}


def get_logger(name: str = "llmXive_pipeline") -> logging.Logger:
    """
    Get a logger instance configured for the pipeline.
    
    Args:
        name: Logger name (typically the module name)
        
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create logs directory
    paths = get_paths()
    logs_dir = paths.get("logs", "logs")
    ensure_directories([logs_dir])
    
    # File handler for pipeline logs
    log_file = os.path.join(logs_dir, "pipeline.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    # Console handler for immediate feedback
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter with timestamp and level
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def setup_pipeline_logging() -> logging.Logger:
    """
    Set up the main pipeline logger and ensure log directories exist.
    
    Returns:
        The configured main logger instance
    """
    paths = get_paths()
    logs_dir = paths.get("logs", "logs")
    ensure_directories([logs_dir])
    
    # Configure root logger for the project
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # File handler
    log_file = os.path.join(logs_dir, "pipeline.log")
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    logger = get_logger("llmXive_pipeline")
    logger.info("Pipeline logging initialized")
    
    return logger


def start_runtime_tracking() -> None:
    """
    Start tracking the pipeline runtime.
    
    Records the start time and initializes runtime statistics.
    Must be called before processing any PRs.
    """
    global _start_time, _start_datetime, _runtime_stats
    
    _start_time = time.time()
    _start_datetime = datetime.now()
    _runtime_stats = {
        "start_time": _start_datetime.isoformat(),
        "total_runtime_seconds": 0,
        "pr_processed_count": 0,
        "pr_skipped_count": 0,
        "errors_count": 0,
        "warnings_count": 0,
    }
    
    logger = get_logger("llmXive_pipeline")
    logger.info(f"Runtime tracking started at {_start_datetime.strftime('%Y-%m-%d %H:%M:%S')}")


def stop_runtime_tracking() -> None:
    """
    Stop tracking the pipeline runtime and log final statistics.
    
    Calculates total runtime and updates the runtime stats dictionary.
    """
    global _start_time, _runtime_stats
    
    if _start_time is None:
        logger = get_logger("llmXive_pipeline")
        logger.warning("Runtime tracking was not started")
        return
    
    end_time = time.time()
    total_runtime = end_time - _start_time
    
    _runtime_stats["total_runtime_seconds"] = total_runtime
    _runtime_stats["end_time"] = datetime.now().isoformat()
    
    logger = get_logger("llmXive_pipeline")
    logger.info(f"Runtime tracking stopped. Total runtime: {total_runtime:.2f} seconds")
    
    # Log runtime stats
    log_runtime_stats()


def log_runtime_stats() -> None:
    """
    Log the current runtime statistics to the pipeline log.
    
    Writes stats to both the log and a JSON file in the logs directory.
    """
    global _runtime_stats, _start_datetime
    
    if _start_datetime is None:
        return
    
    logger = get_logger("llmXive_pipeline")
    
    # Format human-readable duration
    total_seconds = _runtime_stats.get("total_runtime_seconds", 0)
    duration = timedelta(seconds=int(total_seconds))
    
    stats_message = (
        f"Runtime Stats: "
        f"Duration={duration}, "
        f"PRs Processed={_runtime_stats['pr_processed_count']}, "
        f"PRs Skipped={_runtime_stats['pr_skipped_count']}, "
        f"Errors={_runtime_stats['errors_count']}, "
        f"Warnings={_runtime_stats['warnings_count']}"
    )
    
    logger.info(stats_message)
    
    # Save stats to JSON file
    paths = get_paths()
    logs_dir = paths.get("logs", "logs")
    ensure_directories([logs_dir])
    
    stats_file = os.path.join(logs_dir, "runtime_stats.json")
    
    import json
    with open(stats_file, "w") as f:
        json.dump(_runtime_stats, f, indent=2)
    
    logger.info(f"Runtime stats saved to {stats_file}")


def increment_pr_processed() -> None:
    """Increment the count of successfully processed PRs."""
    global _runtime_stats
    _runtime_stats["pr_processed_count"] += 1


def increment_pr_skipped() -> None:
    """Increment the count of skipped PRs."""
    global _runtime_stats
    _runtime_stats["pr_skipped_count"] += 1


def increment_errors() -> None:
    """Increment the error count."""
    global _runtime_stats
    _runtime_stats["errors_count"] += 1


def increment_warnings() -> None:
    """Increment the warning count."""
    global _runtime_stats
    _runtime_stats["warnings_count"] += 1


def main() -> None:
    """
    Main entry point for testing the logger module.
    
    Demonstrates setup, runtime tracking, and stat logging.
    """
    print("Testing logger module...")
    
    # Setup logging
    logger = setup_pipeline_logging()
    logger.info("Logger setup complete")
    
    # Start tracking
    start_runtime_tracking()
    logger.info("Runtime tracking started")
    
    # Simulate some work
    time.sleep(0.1)
    
    # Increment counters
    increment_pr_processed()
    increment_pr_processed()
    increment_pr_skipped()
    increment_warnings()
    
    # Stop tracking and log stats
    stop_runtime_tracking()
    
    print("Logger module test complete. Check logs/pipeline.log for details.")


if __name__ == "__main__":
    main()
