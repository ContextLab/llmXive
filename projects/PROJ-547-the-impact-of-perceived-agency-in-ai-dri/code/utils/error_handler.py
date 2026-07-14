"""
Error handling utilities for the llmXive automated science pipeline.

This module provides custom exceptions and helper functions for graceful
error handling, logging, and resource management.
"""

from __future__ import annotations

import sys
from typing import Callable, TypeVar, cast

from logging.pipeline_logger import get_logger

T = TypeVar("T")


class PipelineError(Exception):
    """Custom exception for pipeline-specific errors."""

    def __init__(self, message: str, code: str = "E000") -> None:
        super().__init__(message)
        self.message = message
        self.code = code

    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


def handle_error(
    error: Exception,
    exit_code: int = 1,
    log_level: str = "ERROR",
) -> None:
    """
    Log an error and exit the program with a specified code.

    Args:
        error: The exception instance to log.
        exit_code: The exit code to return to the OS.
        log_level: The logging level to use (e.g., 'ERROR', 'CRITICAL').
    """
    logger = get_logger()
    logger.log(log_level, f"Pipeline error: {str(error)}", error=repr(error))
    sys.exit(exit_code)


def log_and_exit(
    error_message: str,
    error_code: str = "E000",
    exit_code: int = 1,
) -> None:
    """
    Log a custom error message and exit the program.

    This is a convenience function for cases where an exception is not
    yet raised but the pipeline must terminate.

    Args:
        error_message: The message to log.
        error_code: A short code identifying the error type.
        exit_code: The exit code to return to the OS.
    """
    logger = get_logger()
    pipeline_error = PipelineError(error_message, error_code)
    logger.log("ERROR", f"Pipeline error: {pipeline_error}", error=str(pipeline_error))
    sys.exit(exit_code)


def safe_call(
    func: Callable[..., T],
    *args: object,
    exit_on_error: bool = True,
    **kwargs: object,
) -> T | None:
    """
    Execute a function and handle exceptions gracefully.

    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        exit_on_error: If True, exit the program on error; otherwise return None.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the function, or None if an error occurred and exit_on_error is False.
    """
    try:
        return cast(T, func(*args, **kwargs))
    except Exception as e:
        if exit_on_error:
            handle_error(e)
        return None
