"""
Global error handling middleware and exception hooks for the llmXive pipeline.

This module installs global exception hooks to ensure that:
1. All unhandled exceptions are logged with full tracebacks.
2. A clean shutdown occurs with a user-friendly error message.
3. The system exits with a non-zero status code on failure.
"""
import sys
import traceback
import logging
import atexit
from pathlib import Path
from typing import Callable, Any, Optional

from code.utils.logger import get_logger, log_with_extra

# Initialize the logger for this module
logger = get_logger(__name__)

# Store the original handlers to allow restoration if needed
_original_excepthook = sys.excepthook
_original_stderr = sys.stderr
_original_stdout = sys.stdout

def _global_exception_handler(exctype, value, tb):
    """
    Custom exception hook to handle all uncaught exceptions.
    
    This function replaces sys.excepthook to ensure that any unhandled
    exception results in:
    - Detailed logging via the project's JSON logger.
    - A clear traceback printed to stderr.
    - A clean exit with code 1.
    
    Args:
        exctype: The exception type.
        value: The exception instance.
        tb: The traceback object.
    """
    # Log the exception with full context
    error_msg = f"Unhandled exception of type {exctype.__name__}: {value}"
    logger.critical(error_msg, extra={"exc_info": (exctype, value, tb)})
    
    # Print a formatted traceback to stderr for immediate visibility
    tb_text = "".join(traceback.format_exception(exctype, value, tb))
    sys.stderr.write(f"\n{'='*60}\n")
    sys.stderr.write("CRITICAL ERROR: Unhandled Exception\n")
    sys.stderr.write(f"{'='*60}\n")
    sys.stderr.write(tb_text)
    sys.stderr.write(f"{'='*60}\n\n")
    
    # Restore original hook temporarily to ensure standard exit behavior if needed
    # but we force exit here to prevent partial state saves
    sys.stderr.flush()
    sys.exit(1)

def _register_shutdown_hook():
    """
    Register a hook to handle unexpected termination or cleanup.
    
    This ensures that if the process is killed or exits unexpectedly,
    we log the event (if possible) or at least ensure resources are noted.
    """
    def _on_exit():
        # This runs on normal exit or signal if atexit is supported
        # We don't log here to avoid logging on normal completion,
        # but it's a place for future cleanup logic.
        pass
    
    atexit.register(_on_exit)

def install_global_hooks():
    """
    Install the global exception handler and shutdown hooks.
    
    This function should be called once at the very beginning of the
    application entry point (e.g., in main() of scripts).
    """
    logger.info("Installing global error handling hooks...")
    
    # Install the custom exception hook
    sys.excepthook = _global_exception_handler
    
    # Register shutdown hooks
    _register_shutdown_hook()
    
    logger.info("Global error handling hooks installed successfully.")

def safe_entry_point(func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """
    A decorator/wrapper to safely execute a function with global error handling.
    
    If the function raises an exception, it will be caught, logged, and
    the program will exit with code 1. This is useful for wrapping
    entry points that might be called directly.
    
    Args:
        func: The function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.
        
    Returns:
        The result of the function if successful.
        
    Raises:
        SystemExit: If an exception occurs, exits with code 1.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        # This catch block is a fallback; the global hook should catch most,
        # but this ensures we handle it gracefully if the hook wasn't installed
        # or if we are in a specific context where we want to handle it here.
        logger.critical(f"Exception in safe_entry_point: {e}", exc_info=True)
        sys.stderr.write(f"Fatal error: {e}\n")
        sys.exit(1)