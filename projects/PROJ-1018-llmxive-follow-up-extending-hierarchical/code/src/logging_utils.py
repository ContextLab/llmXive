import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import hashlib


class JSONFormatter(logging.Formatter):
    """
    A custom logging formatter that outputs log records as JSON lines.
    Each log entry includes timestamp, level, message, and version_hash.
    """

    def __init__(self, version_hash: Optional[str] = None):
        super().__init__()
        self.version_hash = version_hash or self._generate_default_version_hash()

    def _generate_default_version_hash(self) -> str:
        """
        Generates a default version hash based on a fixed seed or project name
        if no specific hash is provided. In a real deployment, this might come
        from a git commit or build artifact.
        """
        source = "llmXive-PROJ-1018"
        return hashlib.sha256(source.encode('utf-8')).hexdigest()[:16]

    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "version_hash": self.version_hash
        }

        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)


def get_logger(name: str = "llmxive", version_hash: Optional[str] = None) -> logging.Logger:
    """
    Creates and configures a logger that outputs JSON lines to stdout.

    Args:
        name: The name of the logger.
        version_hash: Optional version hash to include in logs.

    Returns:
        A configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Avoid adding handlers multiple times if called repeatedly
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        formatter = JSONFormatter(version_hash=version_hash)
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def log_version_info(logger: logging.Logger, version: str, commit: Optional[str] = None) -> None:
    """
    Logs version information using the provided logger.

    Args:
        logger: The logger instance to use.
        version: The version string (e.g., '1.0.0').
        commit: Optional git commit hash.
    """
    extra_data = {}
    if commit:
        extra_data['git_commit'] = commit
    
    # Create a temporary record with extra data
    logger.info(f"System initialized. Version: {version}", extra=extra_data)