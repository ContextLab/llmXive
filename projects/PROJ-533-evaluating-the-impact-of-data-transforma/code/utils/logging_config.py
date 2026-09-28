import logging
import os
import json
import fcntl
import tempfile
import platform
import sys
from typing import Optional, Dict, Any
from pathlib import Path

# Import cross-platform locking modules
try:
    import portalocker
    HAS_PORTALOCKER = True
except ImportError:
    HAS_PORTALOCKER = False

try:
    import msvcrt
    HAS_MSVCRT = True
except ImportError:
    HAS_MSVCRT = False


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "data": {}
        }

        # Add extra fields if present
        if hasattr(record, 'extra_data') and isinstance(record.extra_data, dict):
            log_data["data"].update(record.extra_data)

        # Add exception info if present
        if record.exc_info:
            log_data["data"]["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class AtomicFileHandler(logging.FileHandler):
    """
    A logging handler that writes logs atomically using a temp file and rename.
    Supports cross-platform file locking (fcntl on Linux, msvcrt on Windows, or portalocker).
    """

    def __init__(self, filename: str, mode: str = 'a', encoding: Optional[str] = None, delay: bool = False):
        super().__init__(filename, mode, encoding, delay)
        self.filename = filename
        self.lock_file = None

    def emit(self, record: logging.LogRecord):
        """
        Emit a record.
        Performs atomic write: write to temp file, then rename to target.
        Handles file locking for concurrency.
        """
        try:
            msg = self.format(record)
            stream = self.stream

            # Ensure directory exists
            log_dir = os.path.dirname(self.filename)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            # Determine lock mechanism
            if HAS_PORTALOCKER:
                # Use portalocker for cross-platform locking
                with open(self.filename, 'a') as f:
                    portalocker.lock(f, portalocker.LOCK_EX)
                    try:
                        # Write to temp file in same directory to ensure same filesystem for rename
                        dir_name = os.path.dirname(self.filename) or '.'
                        fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='.tmp_log_')
                        try:
                            with os.fdopen(fd, 'w', encoding=self.encoding) as temp_file:
                                temp_file.write(msg + self.terminator)
                            os.replace(temp_path, self.filename)
                        except Exception:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                            raise
                    finally:
                        portalocker.unlock(f)
            elif platform.system() == 'Windows' and HAS_MSVCRT:
                # Windows specific locking
                with open(self.filename, 'a') as f:
                    msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1024)
                    try:
                        dir_name = os.path.dirname(self.filename) or '.'
                        fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='.tmp_log_')
                        try:
                            with os.fdopen(fd, 'w', encoding=self.encoding) as temp_file:
                                temp_file.write(msg + self.terminator)
                            os.replace(temp_path, self.filename)
                        except Exception:
                            if os.path.exists(temp_path):
                                os.unlink(temp_path)
                            raise
                    finally:
                        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1024)
            else:
                # Unix/Linux default (fcntl)
                with open(self.filename, 'a') as f:
                    try:
                        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                        try:
                            dir_name = os.path.dirname(self.filename) or '.'
                            fd, temp_path = tempfile.mkstemp(dir=dir_name, prefix='.tmp_log_')
                            try:
                                with os.fdopen(fd, 'w', encoding=self.encoding) as temp_file:
                                    temp_file.write(msg + self.terminator)
                                os.replace(temp_path, self.filename)
                            except Exception:
                                if os.path.exists(temp_path):
                                    os.unlink(temp_path)
                                raise
                        finally:
                            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                    except Exception as e:
                        # Fallback if flock fails (e.g., NFS issues), write directly
                        # This is a safety net, but atomicity might be compromised
                        stream.write(msg + self.terminator)
                        stream.flush()

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)


def setup_pipeline_logger(
    name: str = "pipeline",
    log_file: str = "results/pipeline.log",
    level: int = logging.INFO
) -> logging.Logger:
    """
    Configures and returns a logger that writes JSON-formatted logs to a file.
    Uses AtomicFileHandler for safe concurrent writes.

    Args:
        name: Logger name.
        log_file: Path to the log file (relative to project root).
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create handler
    handler = AtomicFileHandler(str(log_path))
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)
    return logger


def log_exclusion(logger: logging.Logger, dataset_id: str, reason: str, details: str) -> None:
    """Log a dataset exclusion event."""
    logger.info(
        "Dataset Excluded",
        extra={
            "extra_data": {
                "dataset_id": dataset_id,
                "reason": reason,
                "details": details
            }
        }
    )


def log_imputation_rate(logger: logging.Logger, dataset_id: str, variable: str, rate: float) -> None:
    """Log an imputation event."""
    logger.info(
        "Imputation Performed",
        extra={
            "extra_data": {
                "dataset_id": dataset_id,
                "variable": variable,
                "imputation_rate": rate
            }
        }
    )


def log_transformation_intervention(logger: logging.Logger, dataset_id: str, transformation: str, reason: str) -> None:
    """Log a transformation intervention."""
    logger.info(
        "Transformation Intervention",
        extra={
            "extra_data": {
                "dataset_id": dataset_id,
                "transformation": transformation,
                "reason": reason
            }
        }
    )
