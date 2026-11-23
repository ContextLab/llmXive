"""
Logging utility module.
Provides a consistent logging interface across the project.
"""
import logging
import sys
from typing import Optional, Union

# Singleton root logger instance
_root_logger: Optional[logging.Logger] = None


def _configure_root_logger() -> logging.Logger:
    """
    Configures the singleton root logger used by the project.
    The logger writes to **stdout** and uses a simple formatter.
    This function is idempotent: each call clears any existing handlers
    and attaches a fresh ``StreamHandler`` that points to the *current*
    ``sys.stdout``. This ensures that test frameworks (e.g., pytest's
    ``capsys``) that replace ``sys.stdout`` see the log output.
    """
    global _root_logger
    if _root_logger is None:
        _root_logger = logging.getLogger("llmXive")
        _root_logger.setLevel(logging.INFO)
        # Prevent log propagation to the root logging system
        _root_logger.propagate = False

    # Remove any existing handlers to avoid duplicate output and to
    # capture the *current* stdout (important for testing).
    for handler in _root_logger.handlers[:]:
        _root_logger.removeHandler(handler)
        handler.close()

    # Attach a new handler that writes to the *current* sys.stdout.
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    _root_logger.addHandler(handler)

    return _root_logger


def get_module_logger(name: str) -> logging.Logger:
    """
    Returns a logger for the specified module name.
    Ensures the root logger is configured exactly once (or re‑configured
    to point at the current ``sys.stdout``).
    """
    # Ensure the root logger exists and is configured with the current stdout.
    _configure_root_logger()
    return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """
    Public API required by the task specification.
    Returns a logger for the given module name, writing to stdout.
    This is a thin wrapper around ``get_module_logger`` to keep the
    original internal naming while exposing the expected function.
    """
    return get_module_logger(name)


def set_log_level(level: Union[str, int]) -> None:
    """
    Sets the global log level for the root logger.
    Accepts a string (e.g., "DEBUG") or a numeric logging level.
    """
    root = _configure_root_logger()
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    root.setLevel(level)
    # Ensure all attached handlers respect the new level.
    for handler in root.handlers:
        handler.setLevel(level)


def reset_logger() -> None:
    """
    Resets the global logger configuration.
    Clears handlers and restores the logger to an unconfigured state.
    This is useful for test isolation.
    """
    global _root_logger
    if _root_logger is not None:
        for handler in _root_logger.handlers[:]:
            _root_logger.removeHandler(handler)
            handler.close()
        _root_logger.handlers.clear()
    _root_logger = None
    # Also clear any stray logger with the same name that might have been
    # created elsewhere.
    stray = logging.getLogger("llmXive")
    stray.handlers.clear()
    stray.setLevel(logging.NOTSET)