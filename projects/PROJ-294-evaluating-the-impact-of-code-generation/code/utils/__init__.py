"""
Utility package providing core functions used across the project.
This module supplies logging helpers, task‑ID handling, and SHA‑256
checksum utilities required by the data acquisition pipeline.
"""
import hashlib
import logging
from typing import Optional

# Global task identifier used by the logging filter
_TASK_ID: Optional[str] = None


def set_task_id(task_id: str) -> None:
    """Set the current task identifier for logging."""
    global _TASK_ID
    _TASK_ID = task_id


def get_task_id() -> Optional[str]:
    """Return the current task identifier (or ``None`` if not set)."""
    return _TASK_ID


def setup_logging(task_id: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Initialise the root logger with a formatter that includes the task ID.

    If ``task_id`` is supplied it becomes the current global task ID.
    Subsequent calls will reuse the existing handlers.
    """
    global _TASK_ID
    if task_id:
        _TASK_ID = task_id

    if not logging.root.handlers:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] [%(task_id)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    logger = logging.getLogger(__name__)

    # Ensure the logger has a filter that injects the task ID into each record
    if not any(isinstance(f, logging.Filter) for f in logger.filters):
        class _TaskFilter(logging.Filter):
            def filter(self, record):
                record.task_id = _TASK_ID or "UNKNOWN"
                return True

        logger.addFilter(_TaskFilter())

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Retrieve a logger that respects the global task‑ID filter.
    """
    logger = logging.getLogger(name)
    if not any(isinstance(f, logging.Filter) for f in logger.filters):
        class _TaskFilter(logging.Filter):
            def filter(self, record):
                record.task_id = _TASK_ID or "UNKNOWN"
                return True

        logger.addFilter(_TaskFilter())
    return logger


def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA‑256 checksum of ``file_path``.

    Raises ``FileNotFoundError`` if the path does not exist.
    """
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def verify_checksum(file_path: str, expected_hash: str) -> bool:
    """
    Verify that the SHA‑256 checksum of ``file_path`` matches ``expected_hash``.
    Returns ``True`` on a match, ``False`` otherwise.
    """
    try:
        actual = compute_sha256(file_path)
    except FileNotFoundError:
        return False
    return actual == expected_hash
