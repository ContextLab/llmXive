import logging
from pathlib import Path
from typing import Any, Dict

_LOGGER_CACHE: Dict[str, logging.Logger] = {}

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Retrieve a structured logger instance. If the logger does not yet have
    handlers, a simple ``StreamHandler`` with a concise formatter is added.
    """
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    _LOGGER_CACHE[name] = logger
    return logger

def log_analysis_result(logger: logging.Logger, step: str, result: Any) -> None:
    """
    Helper to log the result of a pipeline step in a structured way.
    """
    logger.info(f"Analysis step '{step}' completed. Result: {result}")

def log_power_insufficiency(logger: logging.Logger, observed_min: int, required_min: int) -> None:
    """
    Log a power‑insufficiency event. The message must contain the exact phrase
    ``Power Insufficiency Error`` so that integration tests can verify it.
    """
    logger.error(
        f"Power Insufficiency Error: Group size ({observed_min}) is below the "
        f"minimum threshold ({required_min})."
    )