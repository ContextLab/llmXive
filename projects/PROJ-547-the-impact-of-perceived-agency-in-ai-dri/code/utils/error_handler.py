"""
Error handling utilities for the pipeline.

Provides custom exception classes and helper functions for logging errors,
handling exceptions gracefully, and exiting the pipeline with appropriate
error codes.
"""

from __future__ import annotations

import sys
from typing import Callable, TypeVar, cast

from logging.pipeline_logger import get_logger

T = TypeVar("T")

class PipelineError(Exception):
    """
    Custom exception for pipeline-specific errors.

    This exception is used to signal errors that occur during pipeline execution
    and should be logged and handled according to the pipeline's error handling
    policy.

    Attributes:
        message (str): The error message.
        code (int): Optional error code for programmatic handling.
    """

    def __init__(self, message: str, code: int | None = None) -> None:
        """
        Initialize a PipelineError.

        Args:
            message: The error message.
            code: Optional error code for programmatic handling.
        """
        super().__init__(message)
        self.message = message
        self.code = code

def handle_error(
    func: Callable[..., T]
) -> Callable[..., T]:
    """
    Decorator to handle errors in pipeline functions.

    This decorator wraps a function to catch exceptions, log them, and re-raise
    them as PipelineError if they are not already PipelineError instances.

    Args:
        func: The function to wrap.

    Returns:
        The wrapped function.
    """
    logger = get_logger()

    def wrapper(*args: object, **kwargs: object) -> T:
        try:
            return func(*args, **kwargs)
        except PipelineError:
            raise
        except Exception as e:
            error_msg = f"Unexpected error in {func.__name__}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PipelineError(error_msg) from e

    return wrapper

def log_and_exit(
    error: Exception,
    exit_code: int = 1,
    logger_name: str | None = None,
) -> None:
    """
    Log an error and exit the pipeline.

    This function logs the provided error and exits the program with the
    specified exit code. It is typically used when a fatal error occurs
    that prevents the pipeline from continuing.

    Args:
        error: The exception to log.
        exit_code: The exit code to use when exiting. Default is 1.
        logger_name: Optional name of the logger to use. If None, the default
            logger is used.
    """
    logger = get_logger(logger_name)
    error_msg = f"Fatal error: {str(error)}"
    logger.error(error_msg, exc_info=True)
    sys.exit(exit_code)
