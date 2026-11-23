import os
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_file: str = "pipeline.log", level: int = logging.INFO) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_file: Name of the log file (relative to project root).
        level: Logging level.
        
    Returns:
        Root logger.
    """
    project_root = Path(__file__).parent.parent
    log_path = project_root / log_file
    
    # Ensure logs directory exists if needed
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create logger
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # File handler
    fh = logging.FileHandler(log_path)
    fh.setLevel(level)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

def get_module_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module."""
    return logging.getLogger(name)

def log_operation_start(logger: logging.Logger, operation: str, message: str = ""):
    """Log the start of an operation."""
    logger.info(f"[START] {operation}: {message}")

def log_operation_complete(logger: logging.Logger, operation: str, message: str = ""):
    """Log the completion of an operation."""
    logger.info(f"[COMPLETE] {operation}: {message}")

def log_data_filter_step(logger: logging.Logger, step_name: str, reason: str, rows_affected: int):
    """Log a data filtering step."""
    logger.warning(f"[FILTER] {step_name}: {reason}. Rows affected: {rows_affected}")

def log_skipped_row(logger: logging.Logger, row_index: int, missing_cols: list):
    """Log a skipped row due to missing data."""
    cols_str = ", ".join(missing_cols)
    logger.warning(f"[SKIP ROW] Index {row_index}: Missing {cols_str}")

def log_zero_variance_field(logger: logging.Logger, field_name: str):
    """Log a field with zero variance."""
    logger.warning(f"[ZERO VARIANCE] Field '{field_name}' has zero variance.")

def log_model_convergence(logger: logging.Logger, converged: bool):
    """Log model convergence status."""
    if converged:
        logger.info("[CONVERGENCE] Model converged successfully.")
    else:
        logger.warning("[CONVERGENCE] Model failed to converge.")

def log_error_fallback(logger: logging.Logger, operation: str, error_msg: str):
    """Log an error that triggered a fallback or failure."""
    logger.error(f"[ERROR] {operation}: {error_msg}")

def log_validation_result(logger: logging.Logger, result: str, details: str = ""):
    """Log a validation result."""
    logger.info(f"[VALIDATION] {result}: {details}")

def log_metric_extraction(logger: logging.Logger, metric_name: str, value: float):
    """Log an extracted metric."""
    logger.info(f"[METRIC] {metric_name}: {value}")

def log_file_write(logger: logging.Logger, file_path: str, rows: int = 0):
    """Log a file write operation."""
    logger.info(f"[WRITE] Saved to {file_path}. Rows: {rows}")

def log_pipeline_phase(logger: logging.Logger, phase_name: str):
    """Log the start of a pipeline phase."""
    logger.info(f"[PHASE START] {phase_name}")

def log_pipeline_phase_end(logger: logging.Logger, phase_name: str, duration: float):
    """Log the end of a pipeline phase."""
    logger.info(f"[PHASE END] {phase_name}. Duration: {duration:.2f}s")
