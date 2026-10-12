"""
Logging configuration utilities for the project.

Provides functions to set up loggers that write to files under the
``data/logs`` directory and also output to the console. The utilities
are used throughout the pipeline scripts (e.g., ``01_data_curation.py``,
``03_analysis.py``, ``03_visualization.py``).

Functions
---------
- ``setup_project_logging(name: str, log_file: str) -> logging.Logger``
  Creates (or retrieves) a logger with the given ``name`` that writes to
  the specified ``log_file`` path. The logger is configured with a
  standard formatter and a console handler.

- ``setup_logging(name: str = "default") -> logging.Logger``
  Convenience wrapper that creates a logger whose log file is placed
  under ``data/logs/<name>.log``. The directory is created if it does not
  exist.

- ``get_logger(name: str) -> logging.Logger``
  Simple accessor that returns a logger instance (creating it if needed
  without adding extra handlers).
"""
import logging
from pathlib import Path

__all__ = [
    "setup_project_logging",
    "setup_logging",
    "get_logger",
]


def _ensure_handler(logger: logging.Logger, handler: logging.Handler) -> None:
    """Add ``handler`` to ``logger`` only if a similar handler is not already present."""
    if not any(isinstance(h, type(handler)) and getattr(h, "baseFilename", None) == getattr(handler, "baseFilename", None)
               for h in logger.handlers):
        logger.addHandler(handler)


def setup_project_logging(name: str, log_file: str) -> logging.Logger:
    """
    Configure a logger for a specific project component.

    Parameters
    ----------
    name: str
        Name of the logger (usually the component name).
    log_file: str
        Full path to the log file that should be written.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # File handler
    file_path = Path(log_file)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    _ensure_handler(logger, file_handler)

    # Console handler (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    _ensure_handler(logger, console_handler)

    return logger


def setup_logging(name: str = "default") -> logging.Logger:
    """
    Convenience wrapper that creates a logger whose log file lives in
    ``data/logs/<name>.log``. The directory hierarchy is created on demand.

    Parameters
    ----------
    name: str, optional
        Identifier for the logger; also used to name the log file.
        Defaults to ``\"default\"``.

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    log_path = Path("data") / "logs" / f"{name}.log"
    return setup_project_logging(name, str(log_path))


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve a logger instance by name. If the logger has not been
    configured yet, it will be created with the default ``setup_logging``
    configuration.

    Parameters
    ----------
    name: str
        Logger name.

    Returns
    -------
    logging.Logger
        Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        # Lazy initialisation with default settings
        setup_logging(name)
    return logger
