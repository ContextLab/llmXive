import logging
import signal
import sys
import threading
import time
from functools import wraps
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Callable, Optional

from utils.io import ensure_directory


# Project-wide logger configuration
_logger: Optional[logging.Logger] = None
_log_lock = threading.Lock()


def get_logger(name: str = "md_pipeline") -> logging.Logger:
    """
    Retrieves or creates a project-wide logger with consistent configuration.
    Logs to both console and a rotating file in `data/logs/pipeline.log`.
    """
    global _logger
    with _log_lock:
        if _logger is None:
            _logger = logging.getLogger(name)
            if _logger.handlers:
                return _logger

            _logger.setLevel(logging.DEBUG)
            _logger.propagate = False

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler.setFormatter(console_formatter)
            _logger.addHandler(console_handler)

            # File Handler (Rotating)
            log_dir = Path("data/logs")
            ensure_directory(log_dir)
            log_file = log_dir / "pipeline.log"

            file_handler = RotatingFileHandler(
                log_file, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            _logger.addHandler(file_handler)

            # Custom Exception Handler for uncaught errors
            def handle_exception(exc_type, exc_value, exc_traceback):
                if issubclass(exc_type, KeyboardInterrupt):
                    sys.__excepthook__(exc_type, exc_value, exc_traceback)
                    return
                _logger.critical(
                    "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
                )

            sys.excepthook = handle_exception

        return _logger


class TimeoutError(Exception):
    """Custom exception raised when a task exceeds the configured timeout."""

    pass


def enforce_timeout(seconds: int):
    """
    Decorator that enforces a hard timeout for a function execution.
    Uses threading.Timer to raise TimeoutError if the function takes too long.
    Note: This is a cooperative timeout; it works best for I/O or long-running
    loops that check for interruption, but for pure CPU-bound Python loops,
    a signal-based approach (Unix only) is stricter. Here we use a threading
    approach compatible with Windows and Linux for the 300s MD run constraint.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result_container = [None]
            exception_container = [None]
            timer_finished = threading.Event()

            def target():
                try:
                    result_container[0] = func(*args, **kwargs)
                except Exception as e:
                    exception_container[0] = e
                finally:
                    timer_finished.set()

            thread = threading.Thread(target=target, daemon=True)
            thread.start()

            if not timer_finished.wait(timeout=seconds):
                # Timeout occurred
                raise TimeoutError(
                    f"Function '{func.__name__}' exceeded timeout of {seconds} seconds."
                )

            thread.join()

            if exception_container[0]:
                raise exception_container[0]

            return result_container[0]

        return wrapper

    return decorator


def timeout_handler(signum: int, frame: Any) -> None:
    """Signal handler for hard timeout enforcement on Unix-like systems."""
    raise TimeoutError("Process exceeded time limit enforced by signal.")


def setup_signal_timeout(seconds: int) -> None:
    """
    Sets up a signal-based timeout for the current process.
    Only works on Unix systems (SIGALRM).
    """
    if hasattr(signal, "SIGALRM"):
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
    else:
        # Fallback for Windows: Log a warning that signal timeout is unavailable
        logger = get_logger()
        logger.warning(
            "SIGALRM not available on this platform. Using threading-based timeout decorator instead."
        )


def clear_signal_timeout() -> None:
    """Clears the signal alarm if it was set."""
    if hasattr(signal, "SIGALRM"):
        signal.alarm(0)


class MDRunLogger:
    """
    Context manager for logging specific MD simulation runs.
    Ensures consistent logging format for simulation steps and errors.
    """

    def __init__(self, complex_id: str, params: dict):
        self.complex_id = complex_id
        self.params = params
        self.logger = get_logger(f"run_{complex_id}")

    def __enter__(self):
        self.logger.info(
            f"Starting simulation for {self.complex_id} with params: {self.params}"
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.info(
                f"Simulation completed successfully for {self.complex_id}"
            )
        elif exc_type is TimeoutError:
            self.logger.error(
                f"Simulation timed out for {self.complex_id} after {self.params.get('duration', 'unknown')}ns"
            )
        else:
            self.logger.error(
                f"Simulation failed for {self.complex_id}: {exc_val}",
                exc_info=exc_tb,
            )
        return False  # Do not suppress exceptions

# Export main symbols
__all__ = [
    "get_logger",
    "TimeoutError",
    "enforce_timeout",
    "setup_signal_timeout",
    "clear_signal_timeout",
    "MDRunLogger",
]