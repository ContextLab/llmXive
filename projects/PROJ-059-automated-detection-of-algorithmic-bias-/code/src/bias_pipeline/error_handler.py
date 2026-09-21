"""
Error handling utilities for the pipeline.
"""
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from .utils import PipelineError, SyntaxErrorInRepo, setup_logging

logger = setup_logging(__name__)

class ExecutionError(PipelineError):
    """Custom error for execution failures."""
    pass

class FatalPipelineError(PipelineError):
    """Custom error for fatal pipeline failures."""
    pass

def safe_execute(
    expected_exception: Optional[Type[Exception]] = None,
    error_msg: str = "An error occurred",
    fallback_return: Any = None
):
    """
    Decorator to safely execute a function and handle exceptions.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except expected_exception as e:
                logger.warning(f"{error_msg}: {e}")
                return fallback_return
            except Exception as e:
                logger.error(f"Unexpected error in {func.__name__}: {e}")
                traceback.print_exc()
                return fallback_return
        return wrapper
    return decorator

def handle_pipeline_error(task_name: str):
    """
    Decorator to wrap a function with error handling for a specific task.
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Task '{task_name}' failed: {e}")
                # Re-raise as a custom error or return a structured error dict
                # For this task, we return a dict with error info to allow pipeline to continue
                return {'error': str(e), 'task': task_name}
        return wrapper
    return decorator

def wrap_pipeline_task(func: Callable) -> Callable:
    """
    Generic wrapper for pipeline tasks.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}")
            raise ExecutionError(f"Failed in {func.__name__}: {e}")
    return wrapper