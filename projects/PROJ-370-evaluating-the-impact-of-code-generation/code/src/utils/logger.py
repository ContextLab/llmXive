import logging
import os
import sys
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from threading import Lock

# Import project paths from settings
try:
    from code.config.settings import get_paths, ensure_directories
except ImportError:
    # Fallback for direct execution or different project root
    from config.settings import get_paths, ensure_directories

# Global state for runtime tracking
_runtime_start: Optional[float] = None
_runtime_stats: Dict[str, Any] = {
    "start_time": None,
    "end_time": None,
    "total_runtime_seconds": 0.0,
    "pr_processed": 0,
    "pr_skipped": 0,
    "errors": 0,
    "warnings": 0,
}
_stats_lock = Lock()

# Log file paths (initialized on setup)
_log_dir: Optional[Path] = None
_runtime_log_path: Optional[Path] = None
_stats_log_path: Optional[Path] = None

def _ensure_log_dirs():
    """Ensure log directories exist."""
    global _log_dir
    if _log_dir is None:
        paths = get_paths()
        _log_dir = paths.get("logs", Path("logs"))
        ensure_directories([_log_dir])

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger instance
    """
    _ensure_log_dirs()
    
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler for general logs
    log_file = _log_dir / f"{name.split('.')[-1]}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)
    file_handler.setFormatter(console_format)
    logger.addHandler(file_handler)
    
    return logger

def setup_pipeline_logging():
    """
    Set up logging infrastructure for the entire pipeline.
    
    Creates:
    - Main pipeline logger
    - Runtime tracking log file
    - Stats summary log file
    """
    _ensure_log_dirs()
    
    # Set up root logger for the project
    root_logger = logging.getLogger("llmXive")
    root_logger.setLevel(logging.INFO)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)
    
    # File handler for pipeline logs
    pipeline_log = _log_dir / "pipeline.log"
    file_handler = logging.FileHandler(pipeline_log)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    root_logger.addHandler(file_handler)
    
    # Initialize runtime log file path
    global _runtime_log_path, _stats_log_path
    _runtime_log_path = _log_dir / "runtime.log"
    _stats_log_path = _log_dir / "runtime_stats.json"
    
    logger = get_logger("llmXive.pipeline")
    logger.info("Pipeline logging infrastructure initialized")
    logger.info(f"Log directory: {_log_dir}")
    
    return root_logger

def start_runtime_tracking():
    """
    Start tracking pipeline runtime.
    
    Records start time and initializes tracking state.
    """
    global _runtime_start, _runtime_stats
    
    with _stats_lock:
        _runtime_start = time.time()
        _runtime_stats["start_time"] = datetime.now().isoformat()
        _runtime_stats["pr_processed"] = 0
        _runtime_stats["pr_skipped"] = 0
        _runtime_stats["errors"] = 0
        _runtime_stats["warnings"] = 0
        _runtime_stats["total_runtime_seconds"] = 0.0
        
        logger = get_logger("llmXive.runtime")
        logger.info(f"Runtime tracking started at {_runtime_stats['start_time']}")

def stop_runtime_tracking():
    """
    Stop tracking pipeline runtime and finalize stats.
    
    Calculates total runtime and writes stats to log file.
    """
    global _runtime_start, _runtime_stats
    
    if _runtime_start is None:
        logger = get_logger("llmXive.runtime")
        logger.warning("Runtime tracking was not started")
        return
    
    with _stats_lock:
        end_time = time.time()
        total_runtime = end_time - _runtime_start
        
        _runtime_stats["end_time"] = datetime.now().isoformat()
        _runtime_stats["total_runtime_seconds"] = total_runtime
        
        # Log runtime stats
        logger = get_logger("llmXive.runtime")
        logger.info(f"Runtime tracking stopped at {_runtime_stats['end_time']}")
        logger.info(f"Total runtime: {total_runtime:.2f} seconds ({total_runtime/60:.2f} minutes)")
        
        # Write stats to JSON file
        if _stats_log_path:
            with open(_stats_log_path, 'w') as f:
                json.dump(_runtime_stats, f, indent=2)
            logger.info(f"Runtime stats written to {_stats_log_path}")
        
        _runtime_start = None

def log_runtime_stats():
    """
    Log current runtime statistics without stopping tracking.
    
    Useful for periodic updates during long-running pipelines.
    """
    if _runtime_start is None:
        return
    
    with _stats_lock:
        current_runtime = time.time() - _runtime_start
        stats_snapshot = _runtime_stats.copy()
        stats_snapshot["current_runtime_seconds"] = current_runtime
        
        logger = get_logger("llmXive.runtime")
        logger.info(f"Runtime checkpoint: {current_runtime:.2f}s, "
                   f"PRs processed: {stats_snapshot['pr_processed']}, "
                   f"PRs skipped: {stats_snapshot['pr_skipped']}, "
                   f"errors: {stats_snapshot['errors']}")

def increment_pr_processed():
    """Increment the count of processed PRs."""
    with _stats_lock:
        _runtime_stats["pr_processed"] += 1
        log_runtime_stats()

def increment_pr_skipped():
    """Increment the count of skipped PRs."""
    with _stats_lock:
        _runtime_stats["pr_skipped"] += 1
        log_runtime_stats()

def increment_errors():
    """Increment the error count."""
    with _stats_lock:
        _runtime_stats["errors"] += 1
        log_runtime_stats()

def increment_warnings():
    """Increment the warning count."""
    with _stats_lock:
        _runtime_stats["warnings"] += 1
        log_runtime_stats()

def get_runtime_remaining_seconds() -> Optional[float]:
    """
    Get remaining time until 6-hour limit (if tracking started).
    
    Returns:
        Remaining seconds or None if tracking not started
    """
    if _runtime_start is None:
        return None
    
    elapsed = time.time() - _runtime_start
    max_runtime = 6 * 60 * 60  # 6 hours in seconds
    remaining = max_runtime - elapsed
    
    return max(0.0, remaining)

def main():
    """
    Main function for standalone execution of logger setup.
    
    Demonstrates logger initialization and runtime tracking.
    """
    # Setup logging
    setup_pipeline_logging()
    logger = get_logger("llmXive.logger_main")
    
    logger.info("Logger module test started")
    
    # Start runtime tracking
    start_runtime_tracking()
    
    # Simulate some work
    logger.info("Simulating pipeline work...")
    time.sleep(0.1)
    
    increment_pr_processed()
    increment_warnings()
    
    # Log runtime stats
    log_runtime_stats()
    
    # Stop tracking
    stop_runtime_tracking()
    
    logger.info("Logger module test completed")

if __name__ == "__main__":
    main()
