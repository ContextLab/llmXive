"""
Generic error handling wrapper for pipeline execution.

Provides custom exceptions and utility functions to handle pipeline errors gracefully,
log failures, and prevent cascading crashes while maintaining audit trails.
"""
import logging
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Optional, Type, Union

from .utils import PipelineError, SyntaxErrorInRepo, setup_logging


class ExecutionError(PipelineError):
    """
    Raised when a specific execution step fails but the pipeline can potentially continue
    or handle the failure gracefully (e.g., skipping a file).
    """
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}


class FatalPipelineError(PipelineError):
    """
    Raised when a critical failure occurs that prevents further pipeline execution
    (e.g., missing configuration, corrupted data source).
    """
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.context = context or {}


def handle_pipeline_error(
    error: Exception,
    task_name: str,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Centralized error handling logic.

    Logs the error with full traceback and context, then re-raises or handles
    based on error type.

    Args:
        error: The exception instance to handle.
        task_name: Name of the task where the error occurred.
        logger: Logger instance. If None, uses the module's default logger.
    """
    if logger is None:
        logger = setup_logging(__name__)

    error_type = type(error).__name__
    error_msg = str(error)
    stack_trace = traceback.format_exc()

    logger.error(f"Error in task '{task_name}': {error_type}: {error_msg}")
    logger.debug(f"Traceback:\n{stack_trace}")

    # Re-raise to allow caller to decide flow control
    raise error


def safe_execute(
    func: Callable,
    *args: Any,
    task_name: Optional[str] = None,
    on_error: Optional[Callable[[Exception], Any]] = None,
    **kwargs: Any
) -> Any:
    """
    Wrapper to safely execute a function, catching exceptions and either
    logging them or calling a fallback handler.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        task_name: Optional name for logging purposes.
        on_error: Optional callback function(error) -> default_value.
                  If provided, returns the result of this callback instead of raising.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of func() or the result of on_error() if an exception occurs.

    Raises:
        Exception: Re-raised if on_error is not provided.
    """
    logger = setup_logging(__name__)
    name = task_name or func.__name__

    try:
        return func(*args, **kwargs)
    except Exception as e:
        handle_pipeline_error(e, name, logger)
        
        if on_error is not None:
            logger.warning(f"Handling error in {name} via callback, returning fallback.")
            return on_error(e)
        
        # If no callback, re-raise (handled by handle_pipeline_error above, 
        # but explicit for clarity in control flow)
        raise


def wrap_pipeline_task(
    task_name: str,
    critical: bool = False
) -> Callable[[Callable], Callable]:
    """
    Decorator to wrap a pipeline task with standardized error handling and logging.

    Args:
        task_name: The name of the task for logging.
        critical: If True, wraps the task to raise FatalPipelineError on any exception.
                 If False, wraps to raise ExecutionError on non-critical failures.

    Returns:
        A decorator function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = setup_logging(__name__)
            logger.info(f"Starting task: {task_name}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Task {task_name} completed successfully.")
                return result
            except (FatalPipelineError, ExecutionError):
                # These are already handled custom errors, re-raise
                raise
            except SyntaxErrorInRepo:
                # Specific handling for syntax errors in repo processing
                logger.warning(f"Task {task_name} encountered a syntax error in a repo file. Skipping file.")
                raise
            except FileNotFoundErrorInRepo:
                logger.warning(f"Task {task_name} encountered a missing file. Skipping file.")
                raise
            except Exception as e:
                # Wrap unexpected errors
                if critical:
                    raise FatalPipelineError(
                        f"Critical failure in {task_name}: {str(e)}",
                        context={"original_exception": e}
                    )
                else:
                    raise ExecutionError(
                        f"Execution failed in {task_name}: {str(e)}",
                        context={"original_exception": e}
                    )
        return wrapper
    return decorator