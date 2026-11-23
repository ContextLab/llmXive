"""
Generic error handling wrapper for pipeline execution.

This module provides decorators and utility functions to handle errors gracefully
across the bias detection pipeline, ensuring robust execution even when individual
components encounter unexpected issues.
"""

import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from .utils import PipelineError, SyntaxErrorInRepo, setup_logging


class ExecutionError(PipelineError):
    """
    Base exception for execution-time errors in the pipeline.

    This exception is raised when a pipeline task encounters a recoverable error
    that should be logged but not necessarily halt the entire pipeline.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message


class FatalPipelineError(PipelineError):
    """
    Exception for errors that must halt the entire pipeline.

    This exception is raised when a critical error occurs that prevents
    further execution of the pipeline.
    """

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception
        self.message = message


def safe_execute(func: Callable) -> Callable:
    """
    Decorator that safely executes a function and catches exceptions.

    This decorator wraps a function call to catch any exceptions, log them,
    and return a default value or raise a custom ExecutionError.

    Args:
        func: The function to wrap.

    Returns:
        A wrapped function that handles exceptions gracefully.
    """
    logger = setup_logging(func.__module__)

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except SyntaxErrorInRepo as e:
            logger.warning(f"Syntax error in repository processing: {e}")
            return {"status": "skipped", "reason": "syntax_error", "error": str(e)}
        except PipelineError as e:
            logger.error(f"Pipeline error in {func.__name__}: {e}")
            return {"status": "error", "reason": "pipeline_error", "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}\n{traceback.format_exc()}")
            return {"status": "error", "reason": "unexpected", "error": str(e)}

    return wrapper


def handle_pipeline_error(
    func: Callable,
    on_error: Optional[Callable[[Exception], Any]] = None,
    log_level: int = logging.ERROR
) -> Callable:
    """
    Decorator for handling pipeline errors with custom behavior.

    This decorator allows customization of error handling behavior, including
    a custom error handler function and log level.

    Args:
        func: The function to wrap.
        on_error: Optional custom error handler function that receives the exception.
        log_level: The log level to use when logging errors.

    Returns:
        A wrapped function with custom error handling.
    """
    logger = setup_logging(func.__module__)

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.log(log_level, f"Error in {func.__name__}: {e}")
            if on_error:
                return on_error(e)
            raise

    return wrapper


def wrap_pipeline_task(
    task_name: str,
    required: bool = True
) -> Callable:
    """
    Decorator to wrap a pipeline task with standardized error handling.

    This decorator provides consistent error handling across all pipeline tasks,
    logging errors and optionally raising fatal errors for required tasks.

    Args:
        task_name: Name of the task for logging purposes.
        required: Whether this task is required (fatal error if it fails).

    Returns:
        A decorator function that wraps the task.
    """
    logger = setup_logging("error_handler")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                logger.info(f"Starting task: {task_name}")
                result = func(*args, **kwargs)
                logger.info(f"Completed task: {task_name}")
                return result
            except FatalPipelineError as e:
                logger.critical(f"Fatal error in {task_name}: {e}")
                raise
            except ExecutionError as e:
                logger.error(f"Execution error in {task_name}: {e}")
                if required:
                    raise FatalPipelineError(f"Required task {task_name} failed: {e}")
                return {"status": "skipped", "reason": "execution_error", "error": str(e)}
            except Exception as e:
                logger.error(f"Unexpected error in {task_name}: {e}\n{traceback.format_exc()}")
                if required:
                    raise FatalPipelineError(f"Required task {task_name} failed with unexpected error: {e}")
                return {"status": "skipped", "reason": "unexpected_error", "error": str(e)}

        return wrapper

    return decorator