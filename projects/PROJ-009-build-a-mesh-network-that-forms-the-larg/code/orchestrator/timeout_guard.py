"""
Timeout guard utilities for the orchestrator pipeline.

The original implementation relied on a configuration file to obtain
the CI timeout value, raising a ``ConfigError`` when the file was
missing.  In the CI environment the configuration file may not be
present, causing imports of modules that use the decorator (e.g.
``orchestrator.benchmark``) to fail before any code runs.

This module provides a robust ``enforce_pipeline_timeout`` decorator
that:

* Attempts to read ``ci_timeout_seconds`` from the global configuration
  via ``orchestrator.config.get_config``.
* Falls back to a sensible default (6 hours = 21600 seconds) when the
  configuration cannot be loaded.
* Executes the wrapped function and raises a ``RuntimeError`` if the
  execution exceeds the timeout.
* Is lightweight and has no external side‑effects, making it safe for
  the mock‑node environment used in unit and integration tests.

The decorator is used by ``orchestrator.benchmark`` and any other
pipeline component that needs a hard CI timeout (FR‑007).
"""

from __future__ import annotations

import functools
import signal
from typing import Callable, Any

# The orchestrator configuration module may raise ``ConfigError`` if
# the default ``config.yaml`` file is absent.  We handle that gracefully.
try:
    from orchestrator.config import get_config, ConfigError  # type: ignore
except Exception:  # pragma: no cover
    # If the import itself fails we define a minimal fallback.
    class ConfigError(Exception):
        """Fallback ConfigError used when the real module cannot be imported."""
        pass

    def get_config():
        """Fallback configuration providing a default CI timeout."""
        class _Fallback:
            ci_timeout_seconds = 21600  # 6 hours
        return _Fallback()

def _timeout_handler(signum: int, frame) -> None:  # pragma: no cover
    """Signal handler that raises a ``RuntimeError`` on timeout."""
    raise RuntimeError("Pipeline execution exceeded the allowed timeout")

def enforce_pipeline_timeout() -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Decorator that enforces a hard timeout on the wrapped function.

    The timeout value is taken from ``orchestrator.config.get_config()``
    (``ci_timeout_seconds``).  If the configuration cannot be loaded,
    a default of 21600 seconds (6 hours) is used.

    Example usage:

    >>> @enforce_pipeline_timeout()
    ... def run():
    ...     ...

    The decorated function will raise ``RuntimeError`` if it runs longer
    than the allowed time.
    """
    try:
        timeout_seconds = getattr(get_config(), "ci_timeout_seconds", 21600)
    except ConfigError:
        # Configuration missing – use the default timeout.
        timeout_seconds = 21600

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Register the alarm signal handler.
            original_handler = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_seconds)
            try:
                return func(*args, **kwargs)
            finally:
                # Cancel any pending alarm and restore original handler.
                signal.alarm(0)
                signal.signal(signal.SIGALRM, original_handler)

        return wrapper

    return decorator
