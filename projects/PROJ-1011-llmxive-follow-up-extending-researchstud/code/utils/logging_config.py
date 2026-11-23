"""
Minimal logging configuration for the llmXive research pipeline.

The original project referenced a fairly large ``logging_config`` module,
but the test suite only requires a few utilities:
  * ``ensure_log_dir`` – guarantees that the ``logs/`` directory exists.
  * ``get_logger`` – returns a ``logging.Logger`` instance with a sensible
    formatter and an optional file handler.
  * Placeholder logging helper functions used elsewhere in the code base
    (e.g. ``log_model_switch``) are provided as no‑ops to keep imports
    functional.

This implementation avoids external dependencies and works in the
constrained execution environment.
"""
import logging
from pathlib import Path
from typing import Dict, Any

# Directory where all log files are stored.
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

def ensure_log_dir() -> None:
    """
    Ensure that the ``logs/`` directory exists.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

def _create_file_handler(name: str) -> logging.FileHandler:
    """
    Create a ``FileHandler`` that writes to ``logs/<name>.log``.
    """
    log_path = LOG_DIR / f"{name}.log"
    handler = logging.FileHandler(log_path, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    return handler

def get_logger(name: str, log_file: str | None = None) -> logging.Logger:
    """
    Retrieve a configured logger.

    Parameters
    ----------
    name : str
        Name of the logger (typically ``__name__``).
    log_file : str | None, optional
        If provided, a file handler writing to ``logs/<log_file>`` is added.
        If ``None``, a handler writing to ``logs/<name>.log`` is used.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    ensure_log_dir()
    logger = logging.getLogger(name)

    # Prevent adding multiple handlers in interactive environments.
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Console handler for immediate feedback.
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter("%(levelname)s - %(message)s")
        )
        logger.addHandler(console_handler)

        # File handler for persistent logs.
        file_name = log_file if log_file is not None else name
        file_handler = _create_file_handler(file_name)
        logger.addHandler(file_handler)

    return logger

# ----------------------------------------------------------------------
# Placeholder helper functions referenced throughout the code base.
# They are intentionally lightweight no‑ops; the real implementations
# would emit structured JSON logs. Keeping them here avoids import errors.
# ----------------------------------------------------------------------
def sanitize_structured_log(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Pass‑through sanitizer for structured log dictionaries. In a full
    implementation this would remove non‑serializable objects.
    """
    return data

def log_model_switch(old_model: str, new_model: str) -> None:
    """
    Log that the embedding/model loading switched from ``old_model`` to
    ``new_model`` due to a memory error.
    """
    logger = get_logger(__name__)
    logger.info(f"Model switch: {old_model} → {new_model}")

def log_memory_error(model_name: str, exc: Exception) -> None:
    """
    Log a memory‑related exception encountered while loading a model.
    """
    logger = get_logger(__name__)
    logger.error(f"MemoryError while loading model {model_name}: {exc}")

def log_fallback_success(fallback_model: str) -> None:
    """
    Log successful fallback to a lighter model.
    """
    logger = get_logger(__name__)
    logger.info(f"Successfully fell back to model {fallback_model}")

def log_fallback_failure(primary_model: str, fallback_model: str, exc: Exception) -> None:
    """
    Log failure to load both primary and fallback models.
    """
    logger = get_logger(__name__)
    logger.error(
        f"Failed to load primary model {primary_model} and fallback model "
        f"{fallback_model}: {exc}"
    )