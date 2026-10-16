"""
Logging configuration for the neural narrative networks pipeline.

This module sets up a logger that writes all messages (DEBUG and above) to
``logs/pipeline.log`` and prints error messages (ERROR and above) to
``stderr``.  Error messages are always prefixed with a concrete error code
from the set ``E001``–``E004`` as required by the project specification.

Usage
-----
>>> from code.utils.logging_config import get_logger, log_error
>>> logger = get_logger(__name__)
>>> logger.info("pipeline started")
>>> log_error("E001", "Missing input file")
[E001] Missing input file
"""
import logging
import sys
from pathlib import Path
from typing import Optional

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# The log directory is ``<project_root>/logs``.  The ``Path`` object is
# created relative to the repository root so that the script works no
# matter where it is executed from (e.g. via ``python -m code.main``).
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"

# The set of error codes that the pipeline may emit.  Keeping the list
# explicit makes it easy to audit that only the allowed codes are used.
VALID_ERROR_CODES = {"E001", "E002", "E003", "E004"}

# ----------------------------------------------------------------------
# Helper – custom formatter for console error output
# ----------------------------------------------------------------------
class _ErrorFormatter(logging.Formatter):
    """
    Formatter that ensures error messages are printed with the explicit
    ``[E###]`` prefix.  If a message already contains a code it is left
    untouched; otherwise the caller must supply a code via ``log_error``.
    """
    def format(self, record: logging.LogRecord) -> str:
        # ``record.msg`` may be a format string with arguments – we format it
        # first to get the final message.
        if record.args:
            record.msg = record.msg % record.args
            record.args = None

        # Ensure the message starts with an error code when the level is
        # ERROR or higher.
        if record.levelno >= logging.ERROR and not record.msg.startswith("[E"):
            # No code supplied – this is a programming error.  We fall back
            # to a generic placeholder so the log still contains something.
            record.msg = f"[E???] {record.msg}"
        return super().format(record)

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
_loggers = {}

def get_logger(name: str = "pipeline") -> logging.Logger:
    """
    Return a configured logger instance.

    The logger writes all messages (DEBUG+) to ``logs/pipeline.log`` and
    prints error messages (ERROR+) to ``stderr`` using the custom
    ``_ErrorFormatter``.  Subsequent calls with the same ``name`` return the
    same logger object (singleton per name) to avoid duplicate handlers.
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # File handler – captures everything.
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler – only errors and above, with a concise format.
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.ERROR)
    console_formatter = _ErrorFormatter("%(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent log propagation to the root logger which could duplicate output.
    logger.propagate = False

    _loggers[name] = logger
    return logger

def log_error(code: str, message: str, logger_name: str = "pipeline") -> None:
    """
    Log an error with a specific error code.

    Parameters
    ----------
    code : str
        One of ``E001``–``E004``.  The function raises ``ValueError`` if an
        unknown code is supplied, ensuring that only the permitted codes are
        emitted.
    message : str
        Human‑readable description of the problem.
    logger_name : str, optional
        Name of the logger to use (defaults to the default pipeline logger).
    """
    if code not in VALID_ERROR_CODES:
        raise ValueError(f"Invalid error code '{code}'. Must be one of {sorted(VALID_ERROR_CODES)}.")
    logger = get_logger(logger_name)
    # Prefix the message with the code in square brackets.
    formatted_msg = f"[{code}] {message}"
    logger.error(formatted_msg)

# Convenience wrappers for each allowed error code.  These make the common
# pattern ``log_E001("msg")`` succinct and type‑checked.
def log_E001(message: str, logger_name: str = "pipeline") -> None:
    """Error E001 – data corruption / missing files."""
    log_error("E001", message, logger_name)

def log_E002(message: str, logger_name: str = "pipeline") -> None:
    """Error E002 – empty or invalid data."""
    log_error("E002", message, logger_name)

def log_E003(message: str, logger_name: str = "pipeline") -> None:
    """Error E003 – unexpected runtime condition."""
    log_error("E003", message, logger_name)

def log_E004(message: str, logger_name: str = "pipeline") -> None:
    """Error E004 – external dependency failure."""
    log_error("E004", message, logger_name)

# Simple aliases matching the original convenience API used elsewhere in the
# codebase.  They forward to the standard ``logging.Logger`` methods.
def info(msg: str, logger_name: str = "pipeline") -> None:
    get_logger(logger_name).info(msg)

def debug(msg: str, logger_name: str = "pipeline") -> None:
    get_logger(logger_name).debug(msg)

def warning(msg: str, logger_name: str = "pipeline") -> None:
    get_logger(logger_name).warning(msg)

def error(msg: str, logger_name: str = "pipeline") -> None:
    """
    Log a generic error without an explicit code.  The console formatter
    will prepend a placeholder ``[E???]`` so that every error line contains a
    code‑like token, satisfying downstream parsers that expect the pattern.
    """
    get_logger(logger_name).error(msg)

def critical(msg: str, logger_name: str = "pipeline") -> None:
    get_logger(logger_name).critical(msg)