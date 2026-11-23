"""
Logging infrastructure for llmXive SpatialClaw pipeline.

Captures execution logs with seed values, blocked operation details,
and structured metrics for reproducibility and audit.
"""
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
import json
import threading
import re

# Constants for log formatting
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Log file paths
LOG_DIR = "data/logs"
EXECUTION_LOG_FILE = "execution.log"
BLOCKED_OPS_LOG_FILE = "blocked_operations.log"
SEED_LOG_FILE = "seeds.log"

# Thread-local storage for logger instances
_logger_context = threading.local()


class MetricsFormatter(logging.Formatter):
    """Custom formatter that adds structured metadata to log records."""
    
    def format(self, record: logging.LogRecord) -> str:
        # Add structured metadata for JSON parsing if needed
        if not hasattr(record, 'metadata'):
            record.metadata = {}
        
        # Standard formatting
        message = super().format(record)
        
        # Append JSON metadata if present
        if record.metadata:
            meta_json = json.dumps(record.metadata, default=str)
            message += f" | META={meta_json}"
        
        return message


class MetricsLogger(logging.Logger):
    """Custom logger class with methods for structured logging."""
    
    def log_seed(self, seed_value: int, run_id: Optional[int] = None, source: str = "reproducibility") -> None:
        """Log a seed value with context."""
        self.info(
            f"Seed configured: {seed_value}",
            extra={
                'metadata': {
                    'seed': seed_value,
                    'run_id': run_id,
                    'source': source,
                    'event_type': 'seed_configuration'
                }
            }
        )
    
    def log_blocked_operation(self, library: str, operation: str, reason: str, stack_trace: Optional[str] = None) -> None:
        """Log a blocked 3D library operation."""
        self.warning(
            f"BLOCKED: {library}.{operation} - {reason}",
            extra={
                'metadata': {
                    'library': library,
                    'operation': operation,
                    'reason': reason,
                    'stack_trace': stack_trace,
                    'event_type': 'blocked_operation'
                }
            }
        )
    
    def log_execution_step(self, task_id: str, step_name: str, duration_ms: float, status: str) -> None:
        """Log an execution step with timing."""
        self.info(
            f"Step {step_name} for task {task_id}: {status} ({duration_ms:.2f}ms)",
            extra={
                'metadata': {
                    'task_id': task_id,
                    'step_name': step_name,
                    'duration_ms': duration_ms,
                    'status': status,
                    'event_type': 'execution_step'
                }
            }
        )


# Register custom logger class
logging.setLoggerClass(MetricsLogger)


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = LOG_DIR,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True,
    seed: Optional[int] = None,
    run_id: Optional[int] = None
) -> None:
    """
    Configure the logging infrastructure for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        enable_file_logging: Whether to write logs to files
        enable_console_logging: Whether to output logs to console
        seed: Current random seed (will be logged)
        run_id: Current run ID (will be logged)
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    file_formatter = MetricsFormatter(LOG_FORMAT, DATE_FORMAT)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    if enable_console_logging:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(console_handler)
    
    # File handlers
    if enable_file_logging:
        # Execution log
        exec_log_path = os.path.join(log_dir, EXECUTION_LOG_FILE)
        exec_handler = logging.FileHandler(exec_log_path)
        exec_handler.setFormatter(file_formatter)
        exec_handler.setLevel(getattr(logging, log_level.upper()))
        root_logger.addHandler(exec_handler)
        
        # Blocked operations log
        blocked_log_path = os.path.join(log_dir, BLOCKED_OPS_LOG_FILE)
        blocked_handler = logging.FileHandler(blocked_log_path)
        blocked_handler.setFormatter(file_formatter)
        blocked_handler.setLevel(logging.WARNING)
        root_logger.addHandler(blocked_handler)
        
        # Seeds log
        seed_log_path = os.path.join(log_dir, SEED_LOG_FILE)
        seed_handler = logging.FileHandler(seed_log_path)
        seed_handler.setFormatter(file_formatter)
        seed_handler.setLevel(logging.INFO)
        root_logger.addHandler(seed_handler)
    
    # Log initialization
    logger = get_logger(__name__)
    logger.info("Logging infrastructure initialized", extra={
        'metadata': {
            'log_level': log_level,
            'log_dir': log_dir,
            'console_logging': enable_console_logging,
            'file_logging': enable_file_logging
        }
    })
    
    # Log seed if provided
    if seed is not None:
        log_seed_usage(seed, run_id)


def get_logger(name: str) -> MetricsLogger:
    """
    Get a logger instance for the specified module name.
    
    Args:
        name: Module name (e.g., __name__)
        
    Returns:
        Configured MetricsLogger instance
    """
    logger = logging.getLogger(name)
    if not isinstance(logger, MetricsLogger):
        # Fallback if logger class wasn't registered properly
        logger = MetricsLogger(name)
        logger.setLevel(logging.INFO)
    return logger


def log_seed_usage(seed: int, run_id: Optional[int] = None, source: str = "reproducibility") -> None:
    """
    Log seed configuration for reproducibility tracking.
    
    Args:
        seed: The random seed value
        run_id: Optional run identifier
        source: Source of the seed configuration
    """
    logger = get_logger(__name__)
    logger.log_seed(seed, run_id, source)


def log_blocked_operation(library: str, operation: str, reason: str, stack_trace: Optional[str] = None) -> None:
    """
    Log a blocked 3D library operation attempt.
    
    Args:
        library: Name of the blocked library (e.g., 'trimesh')
        operation: The operation that was blocked
        reason: Reason for blocking
        stack_trace: Optional stack trace for debugging
    """
    logger = get_logger(__name__)
    logger.log_blocked_operation(library, operation, reason, stack_trace)


def log_execution_step(task_id: str, step_name: str, duration_ms: float, status: str) -> None:
    """
    Log an execution step with timing information.
    
    Args:
        task_id: Identifier for the task
        step_name: Name of the step being executed
        duration_ms: Duration in milliseconds
        status: Status of the step (SUCCESS, FAILED, BLOCKED, etc.)
    """
    logger = get_logger(__name__)
    logger.log_execution_step(task_id, step_name, duration_ms, status)


def extract_blocked_operations(log_file: str = None) -> Dict[str, Any]:
    """
    Extract and summarize blocked operations from log files.
    
    Args:
        log_file: Path to blocked operations log (defaults to data/logs/blocked_operations.log)
        
    Returns:
        Dictionary with blocked operation statistics
    """
    if log_file is None:
        log_file = os.path.join(LOG_DIR, BLOCKED_OPS_LOG_FILE)
    
    if not os.path.exists(log_file):
        return {'total_blocked': 0, 'by_library': {}, 'by_operation': {}}
    
    by_library = {}
    by_operation = {}
    total_blocked = 0
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'BLOCKED:' in line:
                total_blocked += 1
                
                # Extract library and operation
                match = re.search(r'BLOCKED:\s*(\w+)\.(\w+)', line)
                if match:
                    lib = match.group(1)
                    op = match.group(2)
                    
                    by_library[lib] = by_library.get(lib, 0) + 1
                    by_operation[op] = by_operation.get(op, 0) + 1
    
    return {
        'total_blocked': total_blocked,
        'by_library': by_library,
        'by_operation': by_operation
    }


def extract_seed_usage(log_file: str = None) -> List[Dict[str, Any]]:
    """
    Extract seed usage from log files.
    
    Args:
        log_file: Path to seeds log (defaults to data/logs/seeds.log)
        
    Returns:
        List of seed usage records
    """
    if log_file is None:
        log_file = os.path.join(LOG_DIR, SEED_LOG_FILE)
    
    if not os.path.exists(log_file):
        return []
    
    records = []
    
    with open(log_file, 'r') as f:
        for line in f:
            if 'Seed configured:' in line:
                # Parse JSON metadata if present
                meta_match = re.search(r'META=(\{.*\})', line)
                if meta_match:
                    try:
                        meta = json.loads(meta_match.group(1))
                        records.append(meta)
                    except json.JSONDecodeError:
                        pass
    
    return records


def main():
    """
    Demonstrate logging infrastructure setup and usage.
    """
    # Setup logging
    setup_logging(
        log_level="DEBUG",
        seed=42,
        run_id=1
    )
    
    logger = get_logger(__name__)
    
    # Log some test events
    logger.info("Test info message")
    logger.warning("Test warning message")
    
    # Log seed usage
    log_seed_usage(42, run_id=1, source="main.py")
    log_seed_usage(43, run_id=2, source="main.py")
    
    # Log blocked operations
    log_blocked_operation("trimesh", "load", "3D library not allowed in 2D restriction", 
                        "Traceback (most recent call): ...")
    log_blocked_operation("pytorch3d", "PointClouds", "3D library not allowed in 2D restriction")
    
    # Log execution steps
    log_execution_step("task_001", "projection", 125.5, "SUCCESS")
    log_execution_step("task_002", "action", 89.2, "SUCCESS")
    
    # Extract and print statistics
    print("\n--- Blocked Operations Summary ---")
    blocked_stats = extract_blocked_operations()
    print(json.dumps(blocked_stats, indent=2))
    
    print("\n--- Seed Usage Summary ---")
    seed_records = extract_seed_usage()
    for record in seed_records:
        print(json.dumps(record, indent=2))
    
    print("\nLogging infrastructure test complete.")
    print(f"Logs written to: {LOG_DIR}/")


if __name__ == "__main__":
    main()