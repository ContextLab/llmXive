"""
metrics_logging.py
------------------

Utility module for logging metric‑computation progress and exclusions
to ``data/metrics_log.txt``.  It provides a lightweight, file‑based logger
that can be imported by the metric pipeline (``code/metrics.py``) and by
unit‑tests.

The logger writes ISO‑8601 timestamps, the log level and the supplied
message, mirroring the behaviour of the project's generic logger in
``utils.setup_logger`` but targeting the dedicated ``metrics_log.txt`` file.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

# Path to the log file – relative to the project root.
_METRICS_LOG_PATH = Path("data/metrics_log.txt")

# Internal singleton logger instance.
_logger: Optional[logging.Logger] = None


def _ensure_log_file_exists() -> None:
    """
    Make sure the ``data/metrics_log.txt`` file exists.
    If the ``data`` directory hierarchy is missing, raise an informative
    error so that the failure is loud and not silently ignored.
    """
    if not _METRICS_LOG_PATH.parent.is_dir():
        raise FileNotFoundError(
            f"Parent directory for metrics log does not exist: "
            f"{_METRICS_LOG_PATH.parent}"
        )
    # Touch the file – this creates it if it does not exist and does
    # nothing if it already exists.
    _METRICS_LOG_PATH.touch(exist_ok=True)


def get_metrics_logger() -> logging.Logger:
    """
    Return a configured ``logging.Logger`` instance that writes to
    ``data/metrics_log.txt``.  The logger is created only once (singleton)
    and re‑used on subsequent calls.

    The logger uses a simple formatter that includes an ISO‑8601 timestamp,
    the log level and the message.
    """
    global _logger
    if _logger is not None:
        return _logger

    _ensure_log_file_exists()

    logger = logging.getLogger("metrics_logger")
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers if this function is called repeatedly.
    if not logger.handlers:
        file_handler = logging.FileHandler(_METRICS_LOG_PATH, mode="a")
        formatter = logging.Formatter(
            fmt="%(asctime)s %(levelname)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def log_metric_progress(message: str) -> None:
    """
    Log a generic progress message for the metric pipeline.

    Parameters
    ----------
    message : str
        Human‑readable description of the current step (e.g. ``"Starting
        sliding‑window computation for subject 01‑ABC"``).
    """
    logger = get_metrics_logger()
    logger.info(message)


def log_metric_exclusion(subject_id: str, reason: str) -> None:
    """
    Record that a subject was excluded from metric computation.

    Parameters
    ----------
    subject_id : str
        Identifier of the excluded subject.
    reason : str
        Short description of why the subject was excluded (e.g.
        ``"FD > 0.5 mm"``, ``"missing fMRI data"``, etc.).
    """
    logger = get_metrics_logger()
    logger.warning(f"Excluding subject {subject_id}: {reason}")
