"""
Failure Mode Classification for Evaluation Tasks.

This module implements the classification of evaluation failures into specific
categories: 'Syntax Error', 'Semantic Mismatch', and 'Timeout'.

It provides utilities to catch exceptions during inference and classify them,
as well as logging mechanisms for audit trails.
"""
import logging
import signal
import time
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from pathlib import Path

from utils.logging import get_logger


class FailureMode(Enum):
    """Enumeration of possible failure modes during evaluation."""
    SYNTAX_ERROR = "Syntax Error"
    SEMANTIC_MISMATCH = "Semantic Mismatch"
    TIMEOUT = "Timeout"
    SUCCESS = "Success"
    UNKNOWN = "Unknown"


class TimeoutError(Exception):
    """Custom exception raised when a task exceeds the time limit."""
    pass


class TimeoutHandler:
    """Context manager to enforce a timeout on a block of code."""
    
    def __init__(self, seconds: int):
        self.seconds = seconds
        self.original_handler = None

    def _handle_timeout(self, signum, frame):
        raise TimeoutError(f"Task timed out after {self.seconds} seconds")

    def __enter__(self):
        # Only works on Unix systems where SIGALRM is available
        if hasattr(signal, 'SIGALRM'):
            self.original_handler = signal.signal(signal.SIGALRM, self._handle_timeout)
            signal.alarm(self.seconds)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if hasattr(signal, 'SIGALRM'):
            signal.alarm(0)  # Cancel the alarm
            if self.original_handler:
                signal.signal(signal.SIGALRM, self.original_handler)
        # Do not suppress exceptions
        return False


def classify_exception(exception: Exception) -> FailureMode:
    """
    Classifies a given exception into a FailureMode.
    
    Args:
        exception: The exception instance raised during execution.
        
    Returns:
        FailureMode enum corresponding to the exception type.
    """
    if isinstance(exception, SyntaxError):
        return FailureMode.SYNTAX_ERROR
    elif isinstance(exception, TimeoutError):
        return FailureMode.TIMEOUT
    elif isinstance(exception, (ValueError, TypeError, AssertionError, KeyError)):
        # These often indicate the output didn't match expectations (semantic mismatch)
        return FailureMode.SEMANTIC_MISMATCH
    else:
        # Catch-all for unexpected errors, treated as semantic mismatches or unknown
        # depending on strictness. Here we default to Unknown for safety.
        return FailureMode.UNKNOWN


def log_failure(task_id: str, mode: FailureMode, details: Optional[str] = None, logger: Optional[logging.Logger] = None):
    """
    Logs a failure event to the project logger and optionally to a file.
    
    Args:
        task_id: The ID of the task that failed.
        mode: The FailureMode classification.
        details: Optional string describing the specific error message or context.
        logger: Optional logger instance. If None, uses the default project logger.
    """
    if logger is None:
        logger = get_logger(__name__)
    
    log_message = f"Task {task_id} failed with mode: {mode.value}"
    if details:
        log_message += f" - Details: {details}"
    
    if mode == FailureMode.SYNTAX_ERROR:
        logger.warning(log_message)
    elif mode == FailureMode.TIMEOUT:
        logger.warning(log_message)
    else:
        logger.info(log_message)


def run_task_with_classification(task_func, task_id: str, timeout_seconds: int = 30, *args, **kwargs) -> Tuple[bool, FailureMode, Optional[str]]:
    """
    Executes a task function with timeout and exception classification.
    
    Args:
        task_func: The callable to execute.
        task_id: Identifier for the task (used in logging).
        timeout_seconds: Maximum time allowed for the task.
        *args, **kwargs: Arguments to pass to task_func.
        
    Returns:
        A tuple of (success: bool, mode: FailureMode, details: str or None).
        - If success is True, mode is FailureMode.SUCCESS.
        - If success is False, mode is the classified failure type, details contains the error message.
    """
    logger = get_logger(__name__)
    
    try:
        with TimeoutHandler(timeout_seconds):
            task_func(*args, **kwargs)
        
        return True, FailureMode.SUCCESS, None
        
    except TimeoutError as e:
        details = str(e)
        log_failure(task_id, FailureMode.TIMEOUT, details, logger)
        return False, FailureMode.TIMEOUT, details
        
    except SyntaxError as e:
        details = str(e)
        log_failure(task_id, FailureMode.SYNTAX_ERROR, details, logger)
        return False, FailureMode.SYNTAX_ERROR, details
        
    except Exception as e:
        # Classify other exceptions
        mode = classify_exception(e)
        details = str(e)
        log_failure(task_id, mode, details, logger)
        return False, mode, details


def verify_mock_syntax_error():
    """
    Verification function to demonstrate the classification of a SyntaxError.
    This function intentionally raises a SyntaxError to test the logging mechanism.
    """
    logger = get_logger(__name__)
    logger.info("Running verification for mock SyntaxError classification...")
    
    # Simulate a task that produces a SyntaxError
    def mock_task():
        # This code is syntactically invalid
        eval("def broken(")
    
    success, mode, details = run_task_with_classification(
        mock_task, 
        task_id="MOCK-SYNTAX-TEST", 
        timeout_seconds=5
    )
    
    assert not success, "Expected the mock task to fail."
    assert mode == FailureMode.SYNTAX_ERROR, f"Expected SyntaxError mode, got {mode}"
    assert details is not None, "Expected details to be present."
    
    logger.info(f"Verification successful: Detected {mode.value} as expected.")
    return True


if __name__ == "__main__":
    # Run verification if executed directly
    verify_mock_syntax_error()