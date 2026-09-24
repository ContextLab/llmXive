import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import hashlib
import os

# Attempt to get version info from environment or git
def _get_version_hash() -> str:
    """
    Attempts to retrieve a version hash from the environment.
    If not found, returns a deterministic hash of the project root path
    to ensure a unique identifier per environment run.
    """
    env_hash = os.environ.get("LLMXIVE_VERSION_HASH")
    if env_hash:
        return env_hash

    try:
        # Fallback: try to get git commit hash if available
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
            timeout=2
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # Final fallback: hash the absolute path of the project root
    # to ensure uniqueness even in non-git environments.
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return hashlib.sha256(project_root.encode('utf-8')).hexdigest()[:12]


class JSONFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs JSON lines.
    Fields: timestamp, level, message, version_hash
    """

    def __init__(self, version_hash: Optional[str] = None):
        super().__init__()
        self.version_hash = version_hash or _get_version_hash()

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "version_hash": self.version_hash
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)


def get_logger(name: str = "llmxive", level: int = logging.INFO) -> logging.Logger:
    """
    Creates and configures a logger that outputs JSON lines to stdout.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        logger.setLevel(level)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)

        # Set formatter
        formatter = JSONFormatter()
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

    return logger


def log_version_info(logger: Optional[logging.Logger] = None) -> None:
    """
    Logs the current version hash to the logger.
    If no logger is provided, uses the default 'llmxive' logger.
    """
    if logger is None:
        logger = get_logger()

    version = _get_version_hash()
    logger.info(f"Initialized with version hash: {version}")