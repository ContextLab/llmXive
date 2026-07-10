"""
Logging and error handling infrastructure for the molecular complexity pipeline.

This module configures a centralized logging system that writes to both console
and file, with structured error reporting for pipeline failures.
"""
import logging
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
import traceback
import json

# Ensure data directories exist
DATA_DIR = Path("data")
LOGS_DIR = DATA_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None
_initialized: bool = False

# Custom exception for pipeline errors
class PipelineError(Exception):
    """Base exception for pipeline failures."""
    def __init__(self, message: str, stage: str = "unknown", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.stage = stage
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()

class DataIngestionError(PipelineError):
    """Error during data ingestion."""
    pass

class DescriptorCalculationError(PipelineError):
    """Error during descriptor calculation."""
    pass

class AnalysisError(PipelineError):
    """Error during analysis."""
    pass

class VisualizationError(PipelineError):
    """Error during visualization."""
    pass

class ConfigurationError(PipelineError):
    """Error during configuration."""
    pass


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure and return the main logger for the pipeline.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional custom log file path (defaults to data/logs/pipeline.log)
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    global _logger, _initialized
    
    if _initialized:
        return _logger
    
    # Set up log file path
    if log_file is None:
        log_file = str(LOGS_DIR / "pipeline.log")
    
    # Create logger
    _logger = logging.getLogger("molecular_pipeline")
    _logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    _logger.handlers.clear()
    
    # Create formatter with detailed info
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    try:
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # File gets all logs
        file_handler.setFormatter(formatter)
        _logger.addHandler(file_handler)
    except Exception as e:
        # Fallback if file cannot be created
        print(f"Warning: Could not create log file {log_file}: {e}", file=sys.stderr)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        _logger.addHandler(console_handler)
    
    _initialized = True
    return _logger


def get_logger() -> logging.Logger:
    """
    Get the configured logger instance.
    
    Returns:
        Logger instance, initializing if necessary
    """
    global _logger, _initialized
    if not _initialized:
        return setup_logging()
    return _logger


def log_error(
    logger: logging.Logger,
    error: Exception,
    stage: str = "unknown",
    details: Optional[Dict[str, Any]] = None,
    include_traceback: bool = True
) -> Dict[str, Any]:
    """
    Log an error with structured information.
    
    Args:
        logger: Logger instance to use
        error: The exception that occurred
        stage: The pipeline stage where error occurred
        details: Additional context about the error
        include_traceback: Whether to include full traceback
        
    Returns:
        Dictionary with error information
    """
    error_info = {
        "timestamp": datetime.utcnow().isoformat(),
        "stage": stage,
        "error_type": type(error).__name__,
        "message": str(error),
        "details": details or {}
    }
    
    if include_traceback:
        error_info["traceback"] = traceback.format_exc()
    
    # Log at ERROR level
    error_msg = f"ERROR in {stage}: {type(error).__name__} - {str(error)}"
    if details:
        error_msg += f" | Details: {json.dumps(details)}"
    
    logger.error(error_msg)
    
    if include_traceback:
        logger.debug(traceback.format_exc())
    
    return error_info


def handle_pipeline_exception(
    logger: Optional[logging.Logger] = None,
    stage: str = "unknown",
    exit_on_error: bool = True
):
    """
    Context manager or decorator-like function to handle pipeline exceptions.
    
    Usage:
        try:
            with handle_pipeline_exception(stage="ingestion"):
                # code that might fail
                pass
        except PipelineError:
            # handle
            pass
        
    Or as a decorator:
        @handle_pipeline_exception(stage="analysis")
        def my_function():
            pass
    """
    class ExceptionHandler:
        def __init__(self, stage: str, exit_on_error: bool):
            self.stage = stage
            self.exit_on_error = exit_on_error
            self.logger = logger or get_logger()
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                error_info = log_error(
                    self.logger,
                    exc_val,
                    stage=self.stage,
                    include_traceback=True
                )
                
                # Write error summary to error log file
                error_log_path = LOGS_DIR / "errors.log"
                try:
                    with open(error_log_path, 'a', encoding='utf-8') as f:
                        f.write(f"\n{'='*80}\n")
                        f.write(f"ERROR: {self.stage}\n")
                        f.write(f"Time: {error_info['timestamp']}\n")
                        f.write(f"Type: {error_info['error_type']}\n")
                        f.write(f"Message: {error_info['message']}\n")
                        if error_info.get('traceback'):
                            f.write(f"Traceback:\n{error_info['traceback']}\n")
                        f.write(f"{'='*80}\n")
                except Exception as e:
                    print(f"Warning: Could not write to error log: {e}", file=sys.stderr)
                
                if self.exit_on_error:
                    sys.exit(1)
                
                return True  # Suppress exception if not exiting
            return False
        
        def __call__(self, func):
            """Decorator usage"""
            import functools
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return wrapper

    return ExceptionHandler(stage, exit_on_error)


def log_pipeline_start(stage: str, details: Optional[Dict[str, Any]] = None):
    """Log the start of a pipeline stage."""
    logger = get_logger()
    msg = f"STARTING stage: {stage}"
    if details:
        msg += f" | {json.dumps(details)}"
    logger.info(msg)


def log_pipeline_complete(stage: str, duration_seconds: Optional[float] = None):
    """Log the completion of a pipeline stage."""
    logger = get_logger()
    msg = f"COMPLETED stage: {stage}"
    if duration_seconds is not None:
        msg += f" | Duration: {duration_seconds:.2f}s"
    logger.info(msg)


def log_pipeline_failure(stage: str, error: Exception, details: Optional[Dict[str, Any]] = None):
    """Log a pipeline failure."""
    logger = get_logger()
    log_error(logger, error, stage=stage, details=details)


# Initialize logger on module import
setup_logging()
