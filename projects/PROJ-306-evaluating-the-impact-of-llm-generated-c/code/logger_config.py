import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Global logger registry to prevent duplicate handlers
_loggers = {}

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with file and console handlers.
    Ensures handlers are not added multiple times if called repeatedly.
    
    Args:
        name: Logger name (e.g., 'pipeline', 'generation')
        log_file: Optional path to log file. If None, only console output.
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent duplicate logging in parent loggers

    # Clear existing handlers to ensure clean state if re-initialized
    if logger.handlers:
        logger.handlers.clear()

    # Formatter with timestamp and level
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger

def get_pipeline_logger() -> logging.Logger:
    """Get the main pipeline logger."""
    return setup_logger(
        'pipeline',
        log_file='outputs/pipeline.log',
        level=logging.INFO
    )

def log_model_usage(logger: logging.Logger, task_id: str, model_name: str, success: bool, duration_seconds: float = 0.0):
    """
    Log model usage details with robust error handling.
    
    Args:
        logger: Logger instance
        task_id: Task identifier
        model_name: Name of the model used
        success: Whether the generation was successful
        duration_seconds: Time taken for generation
    """
    status = "SUCCESS" if success else "FAILED"
    msg = f"Model Usage | Task: {task_id} | Model: {model_name} | Status: {status}"
    if duration_seconds > 0:
        msg += f" | Duration: {duration_seconds:.2f}s"
    
    if success:
        logger.info(msg)
    else:
        logger.error(msg)

def log_generation_result(logger: logging.Logger, task_id: str, success: bool, error_message: Optional[str] = None, output_path: Optional[str] = None):
    """
    Log generation results with detailed error information.
    
    Args:
        logger: Logger instance
        task_id: Task identifier
        success: Whether generation succeeded
        error_message: Error details if failed
        output_path: Path to generated file if successful
    """
    if success:
        msg = f"Generation | Task: {task_id} | Status: SUCCESS"
        if output_path:
            msg += f" | Output: {output_path}"
        logger.info(msg)
    else:
        msg = f"Generation | Task: {task_id} | Status: FAILED"
        if error_message:
            # Sanitize error message for logging (truncate if too long)
            safe_error = str(error_message)[:500] if error_message else "Unknown error"
            msg += f" | Error: {safe_error}"
        logger.error(msg)

def log_coverage_result(logger: logging.Logger, task_id: str, success: bool, coverage_data: Optional[dict] = None, error_message: Optional[str] = None):
    """
    Log coverage execution results.
    
    Args:
        logger: Logger instance
        task_id: Task identifier
        success: Whether coverage execution succeeded
        coverage_data: Coverage metrics if successful
        error_message: Error details if failed
    """
    if success:
        msg = f"Coverage | Task: {task_id} | Status: SUCCESS"
        if coverage_data:
            line_cov = coverage_data.get('line_coverage', 'N/A')
            branch_cov = coverage_data.get('branch_coverage', 'N/A')
            msg += f" | Line: {line_cov}% | Branch: {branch_cov}%"
        logger.info(msg)
    else:
        msg = f"Coverage | Task: {task_id} | Status: FAILED"
        if error_message:
            safe_error = str(error_message)[:500] if error_message else "Unknown error"
            msg += f" | Error: {safe_error}"
        logger.error(msg)

def log_pipeline_summary(logger: logging.Logger, total_tasks: int, successful: int, failed: int, duration_seconds: float):
    """
    Log a summary of the entire pipeline run.
    
    Args:
        logger: Logger instance
        total_tasks: Total number of tasks processed
        successful: Number of successful tasks
        failed: Number of failed tasks
        duration_seconds: Total execution time
    """
    success_rate = (successful / total_tasks * 100) if total_tasks > 0 else 0.0
    logger.info("=" * 60)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total Tasks: {total_tasks}")
    logger.info(f"Successful:  {successful} ({success_rate:.1f}%)")
    logger.info(f"Failed:      {failed}")
    logger.info(f"Total Time:  {duration_seconds:.2f}s")
    logger.info("=" * 60)
    
    if failed > 0:
        logger.warning(f"⚠️  Pipeline completed with {failed} failures. Check error logs for details.")
    else:
        logger.info("✅ Pipeline completed successfully with no failures.")
