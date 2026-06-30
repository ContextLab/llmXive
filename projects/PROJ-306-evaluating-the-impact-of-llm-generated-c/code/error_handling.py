"""
Centralized error handling and logging utilities for the llmXive pipeline.
Implements robust error handling for API limits, syntax errors, and general exceptions.
"""
import os
import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Callable, TypeVar
from functools import wraps

from config import get_seed
from utils import exponential_backoff_retry

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Set up a logger with console and optional file output.
    
    Args:
        name: Logger name
        log_file: Optional file path for log output
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(console_formatter)
        logger.addHandler(file_handler)
    
    return logger

# Initialize global loggers
pipeline_logger = setup_logger("pipeline", log_file="outputs/pipeline.log")
api_logger = setup_logger("api", log_file="outputs/api.log", level=logging.DEBUG)
error_logger = setup_logger("errors", log_file="outputs/errors.log", level=logging.ERROR)

def log_error(task_id: str, error: Exception, context: Optional[Dict[str, Any]] = None, 
             error_type: str = "general", severity: str = "ERROR"):
    """
    Log an error with structured context and save to error report.
    
    Args:
        task_id: The task identifier
        error: The exception that occurred
        context: Additional context information
        error_type: Type of error (api_limit, syntax_error, general, etc.)
        severity: Severity level (ERROR, WARNING, CRITICAL)
    """
    timestamp = datetime.utcnow().isoformat()
    error_msg = str(error)
    stack_trace = traceback.format_exc()
    
    log_entry = {
        "timestamp": timestamp,
        "task_id": task_id,
        "error_type": error_type,
        "severity": severity,
        "message": error_msg,
        "stack_trace": stack_trace,
        "context": context or {}
    }
    
    # Log to appropriate logger
    if severity == "WARNING":
        error_logger.warning(f"[{task_id}] {error_type}: {error_msg}", extra=log_entry)
    elif severity == "CRITICAL":
        error_logger.critical(f"[{task_id}] {error_type}: {error_msg}", extra=log_entry)
    else:
        error_logger.error(f"[{task_id}] {error_type}: {error_msg}", extra=log_entry)
    
    # Save to error report file
    error_report_path = Path("outputs/error_reports.json")
    error_report_path.parent.mkdir(parents=True, exist_ok=True)
    
    error_reports = []
    if error_report_path.exists():
        try:
            with open(error_report_path, 'r') as f:
                error_reports = json.load(f)
        except (json.JSONDecodeError, IOError):
            error_reports = []
    
    error_reports.append(log_entry)
    
    with open(error_report_path, 'w') as f:
        json.dump(error_reports, f, indent=2, default=str)
    
    pipeline_logger.error(f"Error recorded for task {task_id}: {error_type} - {error_msg}")

def handle_api_rate_limit(task_id: str, error: Exception, max_retries: int = 3, 
                         base_delay: float = 1.0, max_delay: float = 60.0) -> bool:
    """
    Handle API rate limit errors with exponential backoff.
    
    Args:
        task_id: The task identifier
        error: The API exception
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    
    Returns:
        True if retry was successful, False otherwise
    """
    api_logger.warning(f"[{task_id}] API rate limit detected: {error}")
    
    # Check if it's a rate limit error
    error_msg = str(error).lower()
    if "rate limit" in error_msg or "429" in error_msg or "too many requests" in error_msg:
        log_error(task_id, error, error_type="api_rate_limit", severity="WARNING")
        
        # Apply exponential backoff
        for attempt in range(1, max_retries + 1):
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            api_logger.info(f"[{task_id}] Retrying in {delay:.1f}s (attempt {attempt}/{max_retries})")
            time.sleep(delay)
            
            # Try the operation again (caller should handle the actual retry logic)
            # This function logs and prepares for retry, but doesn't execute the operation
            return True
        
        api_logger.error(f"[{task_id}] Max retries ({max_retries}) exceeded for rate limit")
        log_error(task_id, error, error_type="api_rate_limit_exhausted", severity="ERROR")
        return False
    
    return False

def handle_syntax_error(task_id: str, error: SyntaxError, code_snippet: Optional[str] = None):
    """
    Handle syntax errors in generated code with detailed logging.
    
    Args:
        task_id: The task identifier
        error: The syntax error exception
        code_snippet: The code that caused the error (optional)
    """
    error_msg = f"Syntax error at line {error.lineno}, column {error.offset}: {error.msg}"
    
    context = {
        "line": error.lineno,
        "offset": error.offset,
        "message": error.msg
    }
    
    if code_snippet:
        lines = code_snippet.split('\n')
        if error.lineno and 0 < error.lineno <= len(lines):
            context["error_line"] = lines[error.lineno - 1]
            context["error_marker"] = " " * (error.offset - 1) + "^" if error.offset else ""
    
    log_error(task_id, error, context=context, error_type="syntax_error", severity="WARNING")
    pipeline_logger.warning(f"[{task_id}] Generated code has syntax errors: {error_msg}")

def handle_generation_failure(task_id: str, error: Exception, model: str, 
                             prompt_length: int, context: Optional[Dict] = None):
    """
    Handle LLM generation failures with comprehensive logging.
    
    Args:
        task_id: The task identifier
        error: The exception that occurred
        model: The model that was used
        prompt_length: Length of the input prompt
        context: Additional context
    """
    generation_context = {
        "model": model,
        "prompt_length": prompt_length,
        "error_class": error.__class__.__name__
    }
    
    if context:
        generation_context.update(context)
    
    log_error(task_id, error, context=generation_context, error_type="generation_failure", severity="ERROR")

def safe_execute_task(task_id: str, func: Callable, *args, **kwargs) -> Tuple[bool, Optional[Any], Optional[str]]:
    """
    Safely execute a task function with comprehensive error handling.
    
    Args:
        task_id: The task identifier
        func: The function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Tuple of (success, result, error_message)
    """
    try:
        pipeline_logger.info(f"[{task_id}] Starting execution")
        result = func(*args, **kwargs)
        pipeline_logger.info(f"[{task_id}] Execution completed successfully")
        return True, result, None
    except SyntaxError as e:
        handle_syntax_error(task_id, e)
        return False, None, f"Syntax error: {str(e)}"
    except (TimeoutError, ConnectionError) as e:
        if handle_api_rate_limit(task_id, e):
            # Retry logic would be handled by caller
            return False, None, f"API rate limit - retry suggested: {str(e)}"
        log_error(task_id, e, error_type="connection_error")
        return False, None, f"Connection error: {str(e)}"
    except Exception as e:
        handle_generation_failure(task_id, e, kwargs.get('model', 'unknown'), 
                                 kwargs.get('prompt_length', 0))
        return False, None, f"General error: {str(e)}"

# Re-export key functions for easy import
__all__ = [
    'setup_logger',
    'log_error',
    'handle_api_rate_limit',
    'handle_syntax_error',
    'handle_generation_failure',
    'safe_execute_task',
    'pipeline_logger',
    'api_logger',
    'error_logger'
]
