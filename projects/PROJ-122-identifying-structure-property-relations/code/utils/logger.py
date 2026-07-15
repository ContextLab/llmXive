"""
Base logging infrastructure for the llmXive research pipeline.

Provides a centralized logging configuration that ensures:
- Consistent log format across all modules
- Timestamped logs with ISO 8601 format
- Log levels configurable via environment variable or function argument
- File and console handlers
- Integration with the project's seed and checksum utilities
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from datetime import datetime

# Import project utilities to ensure they are available
from .seeds import get_seed_context, is_deterministic_configured
from .checksum import compute_file_checksum


# Default log format
DEFAULT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | "
    "%(filename)s:%(lineno)d | %(message)s"
)

# Default log level
DEFAULT_LEVEL = logging.INFO

# Log file directory (relative to project root)
LOG_DIR = Path("state/logs")


def _ensure_log_dir() -> Path:
    """Ensure the log directory exists."""
    log_path = Path.cwd() / LOG_DIR
    log_path.mkdir(parents=True, exist_ok=True)
    return log_path


def _get_log_filename() -> str:
    """Generate a timestamped log filename."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Include seed context if available for reproducibility tracking
    seed_ctx = get_seed_context()
    if seed_ctx and seed_ctx.get("seed") is not None:
        return f"pipeline_{timestamp}_seed{seed_ctx['seed']}.log"
    return f"pipeline_{timestamp}.log"


def setup_logging(
    level: Optional[Union[int, str]] = None,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
    format_str: Optional[str] = None,
    project_id: Optional[str] = None
) -> logging.Logger:
    """
    Configure the root logger for the pipeline.

    Args:
        level: Log level (e.g., 'DEBUG', 'INFO', logging.INFO).
               Defaults to environment variable LOG_LEVEL or DEFAULT_LEVEL.
        log_file: Path to log file. If None, uses auto-generated filename in state/logs/.
        console: Whether to log to console (default True).
        format_str: Custom log format string. Defaults to DEFAULT_FORMAT.
        project_id: Optional project identifier to include in log metadata.

    Returns:
        The configured root logger.
    """
    # Determine log level
    if level is None:
        level_str = os.environ.get("LOG_LEVEL", "INFO")
        if isinstance(level_str, str):
            level = getattr(logging, level_str.upper(), DEFAULT_LEVEL)
        else:
            level = level_str

    # Get or create logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()

    # Format string
    fmt = format_str or DEFAULT_FORMAT
    formatter = logging.Formatter(fmt)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_file is None:
        log_dir = _ensure_log_dir()
        log_filename = _get_log_filename()
        log_file = log_dir / log_filename
    else:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = logging.FileHandler(str(log_file))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Log startup information
    logger.info("Logging infrastructure initialized.")
    logger.info(f"Log file: {log_file}")
    logger.info(f"Log level: {logging.getLevelName(level)}")
    
    # Log project context if provided
    if project_id:
        logger.info(f"Project ID: {project_id}")
    
    # Log deterministic seed status
    if is_deterministic_configured():
        seed_ctx = get_seed_context()
        logger.info(f"Deterministic mode enabled with seed: {seed_ctx.get('seed')}")
    else:
        logger.warning("Deterministic mode NOT configured. Results may not be reproducible.")

    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance, optionally with a specific name.

    Args:
        name: Logger name. If None, uses the root logger.

    Returns:
        A configured logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)


def log_artifact_checksum(
    logger: logging.Logger,
    file_path: Union[str, Path],
    artifact_name: Optional[str] = None
) -> str:
    """
    Compute and log the SHA-256 checksum of an artifact.

    Args:
        logger: Logger instance to use.
        file_path: Path to the file.
        artifact_name: Optional name for the artifact (defaults to filename).

    Returns:
        The computed checksum string.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"Artifact not found: {path}")
        raise FileNotFoundError(f"Artifact not found: {path}")

    checksum = compute_file_checksum(path)
    name = artifact_name or path.name
    logger.info(f"Artifact checksum ({name}): {checksum}")
    return checksum


class PipelineLogger:
    """
    Context-aware logger wrapper for pipeline stages.
    
    Provides structured logging for specific pipeline stages with
    automatic timing and status tracking.
    """
    
    def __init__(self, stage_name: str, logger: Optional[logging.Logger] = None):
        self.stage_name = stage_name
        self.logger = logger or get_logger(f"pipeline.{stage_name}")
        self._start_time: Optional[datetime] = None
        
    def start(self, **kwargs):
        """Log the start of a stage."""
        self._start_time = datetime.now()
        self.logger.info(f"Starting stage: {self.stage_name}", extra=kwargs)
        
    def complete(self, **kwargs):
        """Log the successful completion of a stage."""
        duration = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        self.logger.info(
            f"Completed stage: {self.stage_name} in {duration:.2f}s",
            extra={"duration": duration, **kwargs}
        )
        self._start_time = None
        
    def fail(self, error: Exception, **kwargs):
        """Log a stage failure."""
        duration = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        self.logger.error(
            f"Failed stage: {self.stage_name} after {duration:.2f}s: {str(error)}",
            exc_info=True,
            extra={"duration": duration, "error": str(error), **kwargs}
        )
        self._start_time = None
