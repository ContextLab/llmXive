"""
Utility logging module for the project.

Provides a configurable logger and simple provenance/event logging functions.
The implementation is intentionally lightweight and does not depend on any
external packages beyond the Python standard library.
"""

import logging
import json
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

# Base logger configuration – each module can obtain a child logger via get_logger(__name__)
_logger = None

def _ensure_logger():
    global _logger
    if _logger is None:
        _logger = logging.getLogger("llmXive")
        _logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        _logger.addHandler(handler)

def get_logger(name: str = __name__) -> logging.Logger:
    """
    Return a logger instance for the given module name.

    The root logger is configured once; subsequent calls return child loggers.
    """
    _ensure_logger()
    return logging.getLogger(name)

# ----------------------------------------------------------------------
# Simple provenance / event logging utilities
# ----------------------------------------------------------------------
_PROVENANCE_DIR = Path(__file__).resolve().parents[2] / "data" / "provenance"
_PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)

def _write_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Append a JSON line to the provenance log.

    Args:
        event_type: Short identifier for the kind of event.
        details: Arbitrary dictionary of event‑specific data.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    entry = {"timestamp": timestamp, "event_type": event_type, "details": details}
    log_path = _PROVENANCE_DIR / "provenance.log"
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")

def log_provenance_event(event_type: str, **details: Any) -> None:
    """
    Public helper used throughout the pipeline to record high‑level events.

    Example:
        log_provenance_event("data_download", source=url, rows=123)
    """
    _write_event(event_type, details)

def log_api_query(service: str, query_params: Dict[str, Any], success: bool,
                  response_time: float, error: str = "") -> None:
    """
    Record an API request – used by the Materials Project fetcher.

    Args:
        service: Name of the external service (e.g., "Materials Project Elasticity").
        query_params: Dictionary of parameters sent to the service.
        success: Whether the request succeeded (HTTP 200).
        response_time: Elapsed time in seconds.
        error: Optional error message if the request failed.
    """
    _write_event(
        "api_query",
        {
            "service": service,
            "query_params": query_params,
            "success": success,
            "response_time_s": response_time,
            "error": error,
        },
    )

def log_data_artifact(artifact_path: Path, action: str = "created") -> None:
    """
    Record creation/modification of a data artifact.

    Args:
        artifact_path: Path to the file that was written.
        action: Description of the action (e.g., "created", "updated").
    """
    _write_event(
        "data_artifact",
        {
            "path": str(artifact_path),
            "action": action,
            "size_bytes": artifact_path.stat().st_size if artifact_path.exists() else None,
        },
    )
