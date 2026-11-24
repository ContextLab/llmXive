"""
Simple project‑wide logger used by pipeline modules.

The logger writes INFO and higher‑level messages to ``logs/pipeline.log``.
It is deliberately lightweight to avoid import‑time side effects that could
break the ``--stage noop`` execution path.
"""

import logging
from pathlib import Path
from utils.config import LOG_PATH

_logger: logging.Logger | None = None

def _ensure_log_file() -> Path:
    """Return the path to the pipeline log file, creating parent directories."""
    log_file = LOG_PATH / "pipeline.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Return a configured logger instance.

    The first call creates a ``logging.Logger`` with a ``FileHandler`` that
    writes to ``logs/pipeline.log`` and a ``StreamHandler`` for console output.
    Subsequent calls return the same logger to avoid duplicate handlers.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler (writes to logs/pipeline.log)
    file_handler = logging.FileHandler(_ensure_log_file(), mode="a")
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler (stderr)
    console_handler = logging.StreamHandler()
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.propagate = False
    _logger = logger
    return logger

# Convenience wrapper used by older modules that imported ``log_warning`` directly.
def log_warning(message: str) -> None:
    """Log a warning message using the project logger."""
    get_logger().warning(message)