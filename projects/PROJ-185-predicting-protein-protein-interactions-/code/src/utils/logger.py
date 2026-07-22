"""
Simple logger utility for the pipeline.

Provides:
- get_logger(): returns a logger that writes to ``pipeline.log`` with ISO‑8601 timestamps.
- log_cli_invocation(args): records the full CLI command line, software version, and seed.
- log_error(message, exc=None): logs an error message (and optional exception traceback).

The logger is used throughout the pipeline; it is deliberately lightweight and has no
external dependencies beyond the Python standard library.
"""
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any, Dict

# Global logger instance (created on first call)
_logger: Optional[logging.Logger] = None

def _ensure_log_file() -> Path:
    """Return the path to the pipeline log file, creating parent directories if needed."""
    log_path = Path("pipeline.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    return log_path

def get_logger() -> logging.Logger:
    """
    Return a logger configured to write to ``pipeline.log`` with ISO‑8601 timestamps.
    The logger is created only once; subsequent calls return the same instance.
    """
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("pipeline")
    logger.setLevel(logging.DEBUG)

    log_file = _ensure_log_file()
    handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Also echo warnings & errors to stderr for immediate visibility
    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setLevel(logging.WARNING)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    _logger = logger
    return logger

def log_cli_invocation(args: Any) -> None:
    """
    Record the exact CLI invocation, software version, and random seed.
    ``args`` is expected to be the ``argparse.Namespace`` returned by the parser.
    """
    logger = get_logger()
    # Re‑create the command line (excluding the python executable)
    cmd = " ".join([sys.argv[0]] + sys.argv[1:])
    version = "pipeline_version: 0.1.0"  # placeholder – could be replaced by a real version tag
    seed = getattr(args, "seed", "None")
    logger.info(f"CLI invocation: {cmd}")
    logger.info(version)
    logger.info(f"Random seed: {seed}")

def log_error(message: str, exc: Optional[BaseException] = None) -> None:
    """
    Log an error message. If an exception is supplied, its traceback is also logged.
    """
    logger = get_logger()
    if exc is not None:
        logger.exception(message)
    else:
        logger.error(message)
