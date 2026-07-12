"""
Logging utilities for the Episodic Future Thinking pipeline.

Provides a JSON formatter for structured logs, file output configuration,
and a dedicated 'fallback_event' logger for tracking fallback triggers
(e.g., when episodic retrieval fails and a baseline model is used).

This module ensures consistent logging across the project to satisfy
Constitution Principle V (artifact tracking) and debugging requirements.
"""
import logging
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


# Project root relative to this file (utils/logging.py -> ../../projects/...)
# We assume the script is run from the project root or code directory.
# The log directory will be created under code/logs/
LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "pipeline.log"
FALLBACK_LOG_FILE = LOG_DIR / "fallback_events.log"


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra data.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data

        # Include exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def _ensure_log_dir() -> None:
    """Create the log directory if it doesn't exist."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def get_json_logger(
    name: str,
    log_file: Optional[Path] = None,
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Configure and return a logger with JSON formatting.

    Args:
        name: Name of the logger (usually __name__).
        log_file: Path to the log file. Defaults to LOG_FILE.
        level: Logging level (INFO, WARNING, ERROR).
        console_output: Whether to also output to stdout.

    Returns:
        Configured logger instance.
    """
    _ensure_log_dir()
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers.clear()  # Clear existing handlers to avoid duplicates

    # File handler
    file_path = log_file or LOG_FILE
    file_handler = logging.FileHandler(file_path)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)

    # Console handler (optional)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JSONFormatter())
        logger.addHandler(console_handler)

    return logger


# --- Specialized Loggers ---

# Global logger for general pipeline events
pipeline_logger = get_json_logger("pipeline", log_file=LOG_FILE)


# Specialized logger for fallback events (Constitution Principle V tracking)
fallback_event_logger = get_json_logger(
    "fallback_event",
    log_file=FALLBACK_LOG_FILE,
    level=logging.WARNING
)


def log_fallback_event(
    reason: str,
    context: Dict[str, Any],
    confidence_score: Optional[float] = None
) -> None:
    """
    Log a specific fallback event where the system defaulted to a baseline model.

    Args:
        reason: The reason for the fallback (e.g., "low_retrieval_count").
        context: Additional context data (e.g., current state, retrieved items).
        confidence_score: The confidence score that triggered the fallback, if applicable.
    """
    extra_data = {
        "reason": reason,
        "context": context,
        "confidence_score": confidence_score,
    }
    # Use a custom attribute to pass extra data to the JSON formatter
    fallback_event_logger.warning(
        f"Fallback triggered: {reason}",
        extra={"extra_data": extra_data}
    )


def log_retrieval_stats(
    query_id: str,
    retrieved_count: int,
    top_score: float,
    latency_ms: float
) -> None:
    """Log retrieval performance metrics."""
    extra_data = {
        "query_id": query_id,
        "retrieved_count": retrieved_count,
        "top_score": top_score,
        "latency_ms": latency_ms,
    }
    pipeline_logger.info(
        f"Retrieval complete: {retrieved_count} items, top score {top_score:.4f}",
        extra={"extra_data": extra_data}
    )


def log_episodic_store(
    episode_id: str,
    state_hash: str,
    outcome_hash: str
) -> None:
    """Log successful storage of an episodic memory."""
    extra_data = {
        "episode_id": episode_id,
        "state_hash": state_hash,
        "outcome_hash": outcome_hash,
    }
    pipeline_logger.info(
        f"Episodic memory stored: {episode_id}",
        extra={"extra_data": extra_data}
    )


def log_conflict_detected(
    state_hash: str,
    existing_outcome: str,
    new_outcome: str,
    resolution: str
) -> None:
    """Log a conflict resolution event during memory update."""
    extra_data = {
        "state_hash": state_hash,
        "existing_outcome": existing_outcome,
        "new_outcome": new_outcome,
        "resolution": resolution,
    }
    pipeline_logger.warning(
        f"Conflict detected and resolved for state {state_hash}",
        extra={"extra_data": extra_data}
    )


if __name__ == "__main__":
    # Self-test: verify loggers work and files are created
    print("Testing logging configuration...")
    
    # Test general logging
    pipeline_logger.info("Pipeline initialization started")
    pipeline_logger.warning("Pipeline initialization completed with warnings")
    pipeline_logger.error("Simulated critical error for testing")

    # Test fallback logging
    log_fallback_event(
        reason="retrieval_count_low",
        context={"query": "test_query", "count": 1},
        confidence_score=0.45
    )

    # Test retrieval stats
    log_retrieval_stats(
        query_id="q-12345",
        retrieved_count=5,
        top_score=0.89,
        latency_ms=120.5
    )

    # Test episodic store
    log_episodic_store(
        episode_id="ep-98765",
        state_hash="sha256:abc123",
        outcome_hash="sha256:def456"
    )

    # Test conflict
    log_conflict_detected(
        state_hash="sha256:conflict_state",
        existing_outcome="out_A",
        new_outcome="out_B",
        resolution="timestamp_override"
    )

    print(f"Logs written to: {LOG_FILE}")
    print(f"Fallback logs written to: {FALLBACK_LOG_FILE}")
    print("Log test completed.")