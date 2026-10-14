"""
Deterministic logging configuration for the llmXive EVA-Bench latency study.

Provides ``setup()`` which configures the ROOT logger with:
  * a rotating file handler writing to ``logs/run.log`` (INFO level),
  * a console handler at WARNING level,
  * a fixed, deterministic format.

The configuration is idempotent: calling ``setup()`` repeatedly will not
duplicate handlers.

Verification command (from the project root):
    python -c "import logging, code.logging_config as lc; lc.setup(); logging.info('test')"
creates ``logs/run.log`` containing the formatted message.
"""
import logging
import sys
import warnings
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional, Union

# Project root = parent of the code/ directory containing this file.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Deterministic defaults (no environment-dependent behavior).
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"
DEFAULT_LOG_FILE = "run.log"
DEFAULT_FILE_LEVEL = logging.INFO
DEFAULT_CONSOLE_LEVEL = logging.WARNING
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file before rotation
LOG_BACKUP_COUNT = 5             # keep run.log.1 ... run.log.5

LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)
LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"

# Module-level marker so setup() is idempotent across repeated calls.
_CONFIGURED = False


def _build_formatter() -> logging.Formatter:
    """Return the single deterministic formatter used by all handlers."""
    return logging.Formatter(fmt=LOG_FORMAT, datefmt=LOG_DATEFMT)


def _clear_handlers(logger: logging.Logger) -> None:
    """Remove and close every handler attached to ``logger``."""
    for handler in list(logger.handlers):
        try:
            handler.flush()
            handler.close()
        except Exception:
            pass
        logger.removeHandler(handler)


def _resolve_log_path(log_file: Optional[Union[str, Path]]) -> Path:
    """Resolve the log file path, defaulting to ``<project>/logs/run.log``."""
    if log_file is None:
        return DEFAULT_LOG_DIR / DEFAULT_LOG_FILE
    # Guard against callers passing a module or other non-path object
    # (a previous regression passed a module here and crashed Path()).
    if isinstance(log_file, Path):
        return log_file
    if isinstance(log_file, str):
        return Path(log_file)
    raise TypeError(
        f"log_file must be a str or Path, got {type(log_file).__name__}"
    )


def setup(
    log_file: Optional[Union[str, Path]] = None,
    file_level: int = DEFAULT_FILE_LEVEL,
    console_level: int = DEFAULT_CONSOLE_LEVEL,
    console_output: bool = True,
    force: bool = False,
) -> logging.Logger:
    """
    Configure the root logger deterministically.

    Args:
        log_file: Path to the log file. Defaults to ``<project>/logs/run.log``.
        file_level: Level for the file handler (default INFO).
        console_level: Level for the console handler (default WARNING).
        console_output: Whether to attach a console handler at all.
        force: Re-configure even if setup() was already called.

    Returns:
        The configured root logger.
    """
    global _CONFIGURED

    root_logger = logging.getLogger()

    if _CONFIGURED and not force:
        return root_logger

    # Resolve output path (always a real filesystem path).
    log_path = _resolve_log_path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Start from a clean slate so handler levels are exactly as configured.
    _clear_handlers(root_logger)
    root_logger.setLevel(min(file_level, console_level))

    formatter = _build_formatter()

    # --- Rotating file handler ---
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # --- Console handler at WARNING level ---
    if console_output:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(console_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Route warnings module output through logging (deterministic capture).
    logging.captureWarnings(True)
    warnings.filterwarnings("ignore", category=ResourceWarning)

    _CONFIGURED = True
    root_logger.debug(
        "Logging initialized: file=%s (level=%s), console level=%s",
        log_path,
        logging.getLevelName(file_level),
        logging.getLevelName(console_level),
    )
    return root_logger


def setup_logging(log_file: Optional[Union[str, Path]] = None, **kwargs) -> logging.Logger:
    """Backwards/forwards-compatible alias for :func:`setup`."""
    return setup(log_file=log_file, **kwargs)


def get_log_path() -> Path:
    """Return the default log file path (``<project>/logs/run.log``)."""
    return DEFAULT_LOG_DIR / DEFAULT_LOG_FILE


__all__ = ["setup", "setup_logging", "get_log_path", "PROJECT_ROOT"]
