"""
Utility module for audit logging used across the project.

Provides a single function `get_audit_logger` that returns a logger
configured to write JSON‑L (one JSON object per line) audit entries
to ``data/raw/audit_log.json``. The logger is created lazily and cached
so multiple calls return the same instance.
"""

import logging
import json
from pathlib import Path
from typing import Any, Dict

_audit_logger: logging.Logger | None = None

def _ensure_log_file(path: Path) -> None:
    """Make sure the parent directory exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # Create the file if it does not exist
    if not path.exists():
        path.touch()

def get_audit_logger() -> logging.Logger:
    """
    Return a logger that writes JSON audit records to
    ``data/raw/audit_log.json``.

    The logger uses the name ``audit`` and logs at INFO level.
    Each call returns the same logger instance.
    """
    global _audit_logger
    if _audit_logger is not None:
        return _audit_logger

    logger = logging.getLogger("audit")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent double logging

    # Determine the audit log path relative to the project root
    project_root = Path(__file__).resolve().parents[2]  # src/utils -> project root
    audit_path = project_root / "data" / "raw" / "audit_log.json"
    _ensure_log_file(audit_path)

    handler = logging.FileHandler(audit_path, mode="a", encoding="utf-8")
    # Simple formatter that writes the message (already a JSON string)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

    _audit_logger = logger
    return logger

def audit_record(record: Dict[str, Any]) -> None:
    """
    Convenience helper: serialize *record* as JSON and write it via the
    audit logger. This function is used throughout the pipeline to
    guarantee a consistent schema.
    """
    logger = get_audit_logger()
    logger.info(json.dumps(record, ensure_ascii=False))
