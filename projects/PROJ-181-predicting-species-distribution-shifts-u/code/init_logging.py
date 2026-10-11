"""
Initialise logging configuration for the project.

This script creates the ``logs/`` directory (if it does not exist) and
configures the root logger to write messages both to a file
``logs/pipeline.log`` and to the console. The log format follows the
specification required by task T003:

    %(asctime)s - %(name)s - %(levelname)s - %(message)s

The function ``initialize_logging`` can be imported by any other module
in the pipeline that needs logging. Running the module as a script will
simply initialise the logging system and emit a single informational
entry.
"""

import logging
from pathlib import Path
from typing import Optional


def _ensure_log_directory(log_dir: Path) -> Path:
    """
    Ensure that the log directory exists.

    Parameters
    ----------
    log_dir: Path
        Desired directory for log files.

    Returns
    -------
    Path
        The (now existing) log directory.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def initialize_logging(log_file: Optional[Path] = None) -> None:
    """
    Initialise the project‑wide logging configuration.

    If *log_file* is ``None`` a default file ``logs/pipeline.log`` is
    created inside the project root. The function configures the root
    logger with the required format and adds both a file handler and a
    stream handler (stdout).

    The call is idempotent – subsequent calls will not add duplicate
    handlers.
    """
    # Resolve the default log directory relative to the project root.
    project_root = Path(__file__).resolve().parents[1]
    default_log_dir = project_root / "logs"
    log_dir = _ensure_log_directory(default_log_dir)

    if log_file is None:
        log_file = log_dir / "pipeline.log"
    else:
        log_file = Path(log_file)

    # Avoid adding handlers multiple times if initialise_logging is called
    # more than once (e.g., from several modules).
    root_logger = logging.getLogger()
    if any(isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_file for h in root_logger.handlers):
        # Logging already configured for the desired file.
        return

    # Define the formatter according to the specification.
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler.
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Console (stream) handler.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    # Configure the root logger.
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(stream_handler)

    root_logger.info("Logging initialised – output directed to %s", log_file)


if __name__ == "__main__":
    # When executed directly, simply initialise logging.
    initialize_logging()
