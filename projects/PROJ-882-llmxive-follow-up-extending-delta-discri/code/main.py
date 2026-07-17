import os
import sys
import time
import json
import logging
import traceback
import resource
from typing import Optional, Callable, Dict, Any, List
from pathlib import Path

# Local imports
from config import get_config_summary

# --- Configuration Constants ---
# SC-003: Global wall-clock budget constraint (6 hours)
WALL_CLOCK_BUDGET_SECONDS = 6 * 60 * 60
MEMORY_LIMIT_MB = 7000  # 7 GB limit as per project constraints

# --- Logging Setup ---
def setup_logging() -> logging.Logger:
    """
    Configure logging infrastructure to track execution time and memory usage.
    Returns a logger instance configured for the pipeline.
    """
    logger = logging.getLogger("llmXive_pipeline")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        # File handler for error tracking
        fh = logging.FileHandler("error.log")
        fh.setLevel(logging.ERROR)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

# --- Resource Monitoring ---
def get_memory_usage_mb() -> float:
    """
    Get current memory usage of the process in MB.
    Uses resource module for Unix-like systems.
    """
    usage = resource.getrusage(resource.RUSAGE_SELF)
    # maxrss is in KB on Linux/macOS
    return usage.ru_maxrss / 1024.0

def check_time_limit(start_time: float, logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if the elapsed wall-clock time exceeds the 6-hour limit (SC-003).
    
    Args:
        start_time: The timestamp (float) when execution began.
        logger: Optional logger to record the violation.
        
    Returns:
        True if within limit, False if exceeded.
        
    Raises:
        RuntimeError: If the time limit is exceeded, with a clear message.
    """
    elapsed = time.time() - start_time
    if elapsed > WALL_CLOCK_BUDGET_SECONDS:
        msg = (
            f"CRITICAL: Wall-clock time limit exceeded. "
            f"Elapsed: {elapsed:.2f}s ({elapsed/3600:.2f} hours), "
            f"Limit: {WALL_CLOCK_BUDGET_SECONDS}s ({WALL_CLOCK_BUDGET_SECONDS/3600:.2f} hours). "
            f"Execution halted per SC-003."
        )
        if logger:
            logger.error(msg)
        raise RuntimeError(msg)
    return True

def check_memory_limit(logger: Optional[logging.Logger] = None) -> bool:
    """
    Check if current memory usage exceeds the 7 GB limit.
    
    Returns:
        True if within limit, False if exceeded.
        
    Raises:
        RuntimeError: If memory limit is exceeded.
    """
    current_mb = get_memory_usage_mb()
    if current_mb > MEMORY_LIMIT_MB:
        msg = (
            f"CRITICAL: Memory limit exceeded. "
            f"Current: {current_mb:.2f} MB, "
            f"Limit: {MEMORY_LIMIT_MB} MB. "
            f"Execution halted."
        )
        if logger:
            logger.error(msg)
        raise RuntimeError(msg)
    return True

class ExecutionMonitor:
    """
    Context manager to track execution time and memory for a specific task or
    the entire pipeline.
    """
    def __init__(self, task_name: str, logger: logging.Logger):
        self.task_name = task_name
        self.logger = logger
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.memory_start: float = 0.0
        self.memory_end: float = 0.0

    def __enter__(self):
        self.start_time = time.time()
        self.memory_start = get_memory_usage_mb()
        self.logger.info(f"Starting task: {self.task_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.memory_end = get_memory_usage_mb()
        
        elapsed = self.end_time - self.start_time
        mem_delta = self.memory_end - self.memory_start
        
        self.logger.info(
            f"Completed task: {self.task_name}. "
            f"Duration: {elapsed:.2f}s, "
            f"Peak Memory Delta: {mem_delta:.2f} MB"
        )
        
        # Check global constraints on exit
        # Note: We check against the *start* of the monitor if it's the root monitor,
        # but for nested monitors we rely on the root check_time_limit call.
        # For simplicity in this implementation, we assume the root monitor 
        # calls check_time_limit at the very end of main().
        
        if exc_type is not None:
            self.logger.error(f"Task {self.task_name} failed with exception: {exc_val}")
            return False
        return True

# --- Task Wrappers ---
# These are stubs or placeholders for the actual task logic that will be implemented
# in subsequent tasks. They exist here to satisfy the import surface required by T009.

def task_download_gsm8k(logger: logging.Logger) -> bool:
    """Placeholder for T012: Download GSM8K."""
    logger.info("Task T012 (Download GSM8K) not yet implemented.")
    return True

def task_generate_oracle(logger: logging.Logger) -> bool:
    """Placeholder for T013: Generate Oracle coefficients."""
    logger.info("Task T013 (Generate Oracle) not yet implemented.")
    return True

def task_extract_features(logger: logging.Logger) -> bool:
    """Placeholder for T018: Extract static features."""
    logger.info("Task T018 (Extract Features) not yet implemented.")
    return True

def task_train_model(logger: logging.Logger) -> bool:
    """Placeholder for T022: Train MLP."""
    logger.info("Task T022 (Train Model) not yet implemented.")
    return True

def task_evaluate(logger: logging.Logger) -> bool:
    """Placeholder for T026/T027: Evaluate metrics."""
    logger.info("Task T026 (Evaluate) not yet implemented.")
    return True

def run_task(task_func: Callable[[logging.Logger], bool], logger: logging.Logger) -> bool:
    """
    Execute a task function with monitoring and error handling.
    Catches RuntimeError/ValueError for numerical instability, logs to error.log,
    and skips to next example (returns False for this task but allows pipeline to continue).
    """
    try:
        with ExecutionMonitor(task_func.__name__, logger):
            # Periodic time check
            check_time_limit(getattr(run_task, '_start_time', time.time()), logger)
            check_memory_limit(logger)
            return task_func(logger)
    except (RuntimeError, ValueError) as e:
        logger.error(f"Numerical instability or runtime error in {task_func.__name__}: {e}")
        logger.error(traceback.format_exc())
        # Log to error.log is handled by the file handler in setup_logging
        return False
    except Exception as e:
        logger.critical(f"Unexpected error in {task_func.__name__}: {e}")
        logger.error(traceback.format_exc())
        raise

# --- Main Orchestrator ---
def main():
    """
    Main pipeline orchestrator.
    1. Setup logging.
    2. Record start time.
    3. Execute tasks in order.
    4. Check time limit at the end.
    5. Report final execution time.
    """
    logger = setup_logging()
    logger.info("=== llmXive Pipeline Started ===")
    
    start_time = time.time()
    run_task._start_time = start_time  # Attach to function for periodic checks if needed

    tasks = [
        ("T012: Download GSM8K", task_download_gsm8k),
        ("T013: Generate Oracle", task_generate_oracle),
        ("T018: Extract Features", task_extract_features),
        ("T022: Train Model", task_train_model),
        ("T026: Evaluate", task_evaluate),
    ]

    success_count = 0
    failed_count = 0

    for name, func in tasks:
        logger.info(f"--- Executing {name} ---")
        # Check time limit before starting each task
        check_time_limit(start_time, logger)
        
        if run_task(func, logger):
            success_count += 1
        else:
            failed_count += 1
            # Note: In a strict pipeline we might stop on failure, 
            # but the spec says "skip to next example" for numerical instability.
            # For task-level failures, we continue to attempt others if possible.
            logger.warning(f"Task {name} failed. Continuing to next task.")

    total_time = time.time() - start_time
    
    # SC-003: Final explicit check
    try:
        check_time_limit(start_time, logger)
    except RuntimeError:
        # If we hit the limit here, we report and exit
        logger.critical("Pipeline terminated due to wall-clock time limit.")
        # Re-raise to ensure the process exits with an error code
        raise

    # Final Report
    logger.info("=== Pipeline Execution Report ===")
    logger.info(f"Total Wall-Clock Time: {total_time:.2f} seconds ({total_time/3600:.2f} hours)")
    logger.info(f"Tasks Succeeded: {success_count}")
    logger.info(f"Tasks Failed: {failed_count}")
    logger.info(f"Peak Memory Usage: {get_memory_usage_mb():.2f} MB")
    
    # Write summary to a file for external consumption
    summary_path = Path("data/processed/pipeline_summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "total_time_seconds": total_time,
        "time_limit_seconds": WALL_CLOCK_BUDGET_SECONDS,
        "time_limit_exceeded": total_time > WALL_CLOCK_BUDGET_SECONDS,
        "peak_memory_mb": get_memory_usage_mb(),
        "tasks_succeeded": success_count,
        "tasks_failed": failed_count,
        "config_summary": get_config_summary()
    }
    
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Summary saved to {summary_path}")
    logger.info("=== Pipeline Finished ===")

    if failed_count > 0:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()