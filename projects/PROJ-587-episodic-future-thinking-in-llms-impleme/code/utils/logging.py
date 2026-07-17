import logging
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Constants for log formatting
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Module-level logger instance
_logger = None
_fallback_logger = None

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_data["extra"] = record.extra_data

        return json.dumps(log_data)

def get_json_logger(
    name: str,
    log_file: Optional[str] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """
    Create and configure a logger with JSON formatting.

    Args:
        name: Logger name (usually __name__)
        log_file: Optional path to log file. If None, logs to stdout.
        level: Logging level (e.g., logging.INFO, logging.DEBUG)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    # Create formatter
    formatter = JSONFormatter()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Add file handler if specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

def log_fallback_event(
    logger: logging.Logger,
    event_type: str,
    details: Dict[str, Any],
    confidence_score: Optional[float] = None
) -> None:
    """
    Log a fallback event when the system reverts to baseline behavior.

    Args:
        logger: Logger instance
        event_type: Type of fallback (e.g., "low_retrieval_count", "similarity_threshold")
        details: Additional context about the fallback
        confidence_score: Optional confidence score that triggered fallback
    """
    extra_data = {
        "event_type": event_type,
        "details": details,
        "confidence_score": confidence_score,
    }

    logger.warning(
        f"Fallback event triggered: {event_type}",
        extra={"extra_data": extra_data}
    )

def log_retrieval_stats(
    logger: logging.Logger,
    query_id: str,
    retrieved_count: int,
    avg_similarity: float,
    latency_ms: float,
    top_k: int
) -> None:
    """
    Log retrieval statistics for analysis.

    Args:
        logger: Logger instance
        query_id: Unique identifier for the query
        retrieved_count: Number of items retrieved
        avg_similarity: Average similarity score
        latency_ms: Retrieval latency in milliseconds
        top_k: Requested top-k value
    """
    extra_data = {
        "query_id": query_id,
        "retrieved_count": retrieved_count,
        "avg_similarity": avg_similarity,
        "latency_ms": latency_ms,
        "top_k": top_k,
    }

    logger.info(
        f"Retrieval stats for {query_id}: {retrieved_count} items, "
        f"avg_sim={avg_similarity:.4f}, latency={latency_ms:.2f}ms",
        extra={"extra_data": extra_data}
    )

def log_episodic_store(
    logger: logging.Logger,
    episode_id: str,
    state_hash: str,
    action_hash: str,
    outcome_hash: str,
    timestamp: datetime
) -> None:
    """
    Log successful storage of an episodic memory.

    Args:
        logger: Logger instance
        episode_id: Unique identifier for the episode
        state_hash: Hash of the state representation
        action_hash: Hash of the action taken
        outcome_hash: Hash of the outcome observed
        timestamp: When the episode was stored
    """
    extra_data = {
        "episode_id": episode_id,
        "state_hash": state_hash,
        "action_hash": action_hash,
        "outcome_hash": outcome_hash,
        "timestamp": timestamp.isoformat(),
    }

    logger.debug(
        f"Episodic memory stored: {episode_id}",
        extra={"extra_data": extra_data}
    )

def log_conflict_detected(
    logger: logging.Logger,
    state_hash: str,
    outcome_hashes: list,
    resolution_strategy: str
) -> None:
    """
    Log a detected conflict in episodic memory (same state, different outcomes).

    Args:
        logger: Logger instance
        state_hash: Hash of the conflicting state
        outcome_hashes: List of conflicting outcome hashes
        resolution_strategy: Strategy used to resolve the conflict
    """
    extra_data = {
        "state_hash": state_hash,
        "outcome_hashes": outcome_hashes,
        "resolution_strategy": resolution_strategy,
    }

    logger.warning(
        f"Conflict detected for state {state_hash}",
        extra={"extra_data": extra_data}
    )

# Initialize default loggers at module load
if _logger is None:
    _logger = get_json_logger("episodic_future_thinking")

if _fallback_logger is None:
    _fallback_logger = get_json_logger("fallback_events", level=logging.WARNING)

def get_default_logger() -> logging.Logger:
    """Get the default project logger."""
    return _logger

def get_fallback_logger() -> logging.Logger:
    """Get the fallback event logger."""
    return _fallback_logger