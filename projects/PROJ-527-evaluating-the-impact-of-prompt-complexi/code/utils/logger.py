"""
Logging and Error Handling Infrastructure.
"""
import logging
import sys
import traceback
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json

from config import LOG_LEVEL, LOG_FILE

class PipelineError(Exception):
    """Base exception for pipeline errors."""
    pass

class DataFetchError(PipelineError):
    """Error during data fetching."""
    pass

class LLMClientError(PipelineError):
    """Error during LLM interaction."""
    pass

class ExecutionError(PipelineError):
    """Error during code execution."""
    pass

class AnalysisError(PipelineError):
    """Error during analysis."""
    pass

class ValidationError(PipelineError):
    """Error during validation."""
    pass

def setup_logging() -> logging.Logger:
    """Configure and return the root logger for the pipeline."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Clear existing handlers
    if logger.handlers:
        logger.handlers.clear()

    # File Handler
    try:
        fh = logging.FileHandler(LOG_FILE)
        fh.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    logger.addHandler(ch)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    parent_logger = logging.getLogger("llmXive")
    return parent_logger.getChild(name)

def handle_error(error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error with context and traceback."""
    logger = get_logger(__name__)
    logger.error(f"Error occurred: {type(error).__name__}: {str(error)}")
    if context:
        logger.error(f"Context: {json.dumps(context, default=str)}")
    logger.error("Traceback:\n" + traceback.format_exc())

def log_execution_time(func):
    """Decorator to log execution time of a function."""
    import functools

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logger = get_logger(func.__module__)
            logger.info(f"{func.__name__} executed in {duration:.2f} seconds")
    return wrapper

def log_pipeline_stage(stage_name: str, status: str, details: Optional[str] = None) -> None:
    """Log a pipeline stage status."""
    logger = get_logger("pipeline")
    message = f"Stage: {stage_name} | Status: {status}"
    if details:
        message += f" | Details: {details}"
    if status == "SUCCESS":
        logger.info(message)
    elif status == "FAILED":
        logger.error(message)
    else:
        logger.warning(message)

# Initialize logging on module import
setup_logging()

def main():
    """Test logging setup."""
    logger = get_logger(__name__)
    logger.info("Logger initialized successfully.")
    logger.debug("This is a debug message.")
    logger.warning("This is a warning.")
    try:
        raise ValueError("Test error")
    except Exception as e:
        handle_error(e)

if __name__ == "__main__":
    main()
