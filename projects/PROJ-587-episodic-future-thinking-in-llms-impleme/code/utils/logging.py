"""
Logging utilities for the Episodic Future Thinking project.

Provides specialized loggers for retrieval events, confidence scores,
fallback triggers, and conflict resolution. Uses JSON formatting for
structured log analysis.
"""

import logging
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Global registry to prevent circular import issues and ensure single instance per logger name
_loggers: Dict[str, logging.Logger] = {}

# Constants for logger names
LOGGER_DEFAULT = "episodic_default"
LOGGER_RETRIEVAL = "episodic_retrieval"
LOGGER_FALLBACK = "episodic_fallback"
LOGGER_CONFIDENCE = "episodic_confidence"
LOGGER_CONFLICT = "episodic_conflict"
LOGGER_STATS = "episodic_stats"

# Log file paths (relative to project root)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "logs")
LOG_FILE_RETRIEVAL = os.path.join(LOG_DIR, "retrieval_events.jsonl")
LOG_FILE_FALLBACK = os.path.join(LOG_DIR, "fallback_events.jsonl")
LOG_FILE_CONFIDENCE = os.path.join(LOG_DIR, "confidence_scores.jsonl")
LOG_FILE_CONFLICT = os.path.join(LOG_DIR, "conflict_events.jsonl")
LOG_FILE_STATS = os.path.join(LOG_DIR, "stats_events.jsonl")
LOG_FILE_DEFAULT = os.path.join(LOG_DIR, "general.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON lines."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
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
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def _get_logger(
    name: str, 
    log_file: str, 
    level: int = logging.INFO, 
    use_json: bool = True
) -> logging.Logger:
    """
    Internal helper to create or retrieve a logger.
    
    Args:
        name: Logger name
        log_file: Path to log file
        level: Logging level
        use_json: Whether to use JSON formatter
        
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # Prevent double logging
    
    # Clear existing handlers to avoid duplicates on re-import
    logger.handlers.clear()
    
    # File handler
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(level)
    
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Optional: Console handler for debugging
    if os.environ.get("LOG_TO_CONSOLE", "false").lower() == "true":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    _loggers[name] = logger
    return logger

def get_default_logger() -> logging.Logger:
    """Get the default general-purpose logger."""
    return _get_logger(LOGGER_DEFAULT, LOG_FILE_DEFAULT, logging.INFO, use_json=False)

def get_retrieval_logger() -> logging.Logger:
    """Get the logger for episodic retrieval events."""
    return _get_logger(LOGGER_RETRIEVAL, LOG_FILE_RETRIEVAL, logging.INFO, use_json=True)

def get_fallback_logger() -> logging.Logger:
    """Get the logger for fallback triggers (when episodic memory fails)."""
    return _get_logger(LOGGER_FALLBACK, LOG_FILE_FALLBACK, logging.WARNING, use_json=True)

def get_confidence_logger() -> logging.Logger:
    """Get the logger for confidence score reporting."""
    return _get_logger(LOGGER_CONFIDENCE, LOG_FILE_CONFIDENCE, logging.INFO, use_json=True)

def get_conflict_logger() -> logging.Logger:
    """Get the logger for conflict resolution events."""
    return _get_logger(LOGGER_CONFLICT, LOG_FILE_CONFLICT, logging.WARNING, use_json=True)

def get_stats_logger() -> logging.Logger:
    """Get the logger for statistical analysis events."""
    return _get_logger(LOGGER_STATS, LOG_FILE_STATS, logging.INFO, use_json=True)

def log_retrieval_trigger(
    query_state: str,
    retrieved_episodes: List[Dict[str, Any]],
    similarity_scores: List[float],
    threshold: float,
    latency_ms: float
) -> None:
    """
    Log a retrieval event with query details and results.
    
    Args:
        query_state: The state text used for retrieval
        retrieved_episodes: List of retrieved episode dictionaries
        similarity_scores: Cosine similarity scores for retrieved episodes
        threshold: The similarity threshold used
        latency_ms: Time taken for retrieval in milliseconds
    """
    logger = get_retrieval_logger()
    extra_data = {
        "event_type": "retrieval_trigger",
        "query_state_preview": query_state[:100] + "..." if len(query_state) > 100 else query_state,
        "retrieved_count": len(retrieved_episodes),
        "top_similarity": max(similarity_scores) if similarity_scores else 0.0,
        "threshold": threshold,
        "latency_ms": round(latency_ms, 2),
        "episodes": retrieved_episodes
    }
    logger.info(f"Retrieved {len(retrieved_episodes)} episodes with threshold {threshold}", extra={"extra_data": extra_data})

def log_fallback_event(
    reason: str,
    current_state: str,
    fallback_method: str = "baseline_transformer"
) -> None:
    """
    Log a fallback event when episodic memory cannot provide sufficient retrieval.
    
    Args:
        reason: Why the fallback was triggered (e.g., "low_retrieval_count", "low_similarity")
        current_state: The current state that triggered the fallback
        fallback_method: The method used as fallback
    """
    logger = get_fallback_logger()
    extra_data = {
        "event_type": "fallback_triggered",
        "reason": reason,
        "current_state_preview": current_state[:100] + "..." if len(current_state) > 100 else current_state,
        "fallback_method": fallback_method
    }
    logger.warning(f"Fallback triggered: {reason}", extra={"extra_data": extra_data})

def log_confidence_score(
    scenario_id: str,
    confidence_scores: Dict[str, float],
    counterfactual_details: Optional[List[Dict[str, Any]]] = None,
    wysiat_flag: bool = False
) -> None:
    """
    Log confidence scores for a generated scenario.
    
    Args:
        scenario_id: Unique identifier for the scenario
        confidence_scores: Dictionary mapping detail types to confidence scores
        counterfactual_details: Optional list of counterfactual details
        wysiat_flag: True if WYSIATI bias was detected
    """
    logger = get_confidence_logger()
    extra_data = {
        "event_type": "confidence_report",
        "scenario_id": scenario_id,
        "confidence_scores": confidence_scores,
        "wysiat_flag": wysiat_flag
    }
    if counterfactual_details:
        extra_data["counterfactual_count"] = len(counterfactual_details)
    
    logger.info(f"Confidence scores logged for scenario {scenario_id}", extra={"extra_data": extra_data})

def log_conflict_detected(
    state_hash: str,
    episode_ids: List[str],
    outcomes: List[str],
    resolution: str,
    timestamp: datetime
) -> None:
    """
    Log a conflict resolution event.
    
    Args:
        state_hash: Hash of the conflicting state
        episode_ids: IDs of the conflicting episodes
        outcomes: Different outcomes associated with the state
        resolution: How the conflict was resolved (e.g., "most_recent")
        timestamp: Timestamp of the conflict detection
    """
    logger = get_conflict_logger()
    extra_data = {
        "event_type": "conflict_detected",
        "state_hash": state_hash,
        "conflicting_episodes": episode_ids,
        "outcomes": outcomes,
        "resolution_method": resolution,
        "detection_time": timestamp.isoformat()
    }
    logger.warning(f"Conflict detected for state {state_hash}, resolved via {resolution}", extra={"extra_data": extra_data})

def log_episodic_store(
    episode_id: str,
    state_hash: str,
    action_hash: str,
    outcome_hash: str,
    embedding_dim: int,
    store_time_ms: float
) -> None:
    """
    Log an episode storage event.
    
    Args:
        episode_id: Unique identifier for the stored episode
        state_hash: Hash of the state
        action_hash: Hash of the action
        outcome_hash: Hash of the outcome
        embedding_dim: Dimensionality of the embedding
        store_time_ms: Time taken to store in milliseconds
    """
    logger = get_retrieval_logger()
    extra_data = {
        "event_type": "episode_stored",
        "episode_id": episode_id,
        "state_hash": state_hash,
        "action_hash": action_hash,
        "outcome_hash": outcome_hash,
        "embedding_dim": embedding_dim,
        "store_time_ms": round(store_time_ms, 2)
    }
    logger.info(f"Episode {episode_id} stored successfully", extra={"extra_data": extra_data})

def log_retrieval_stats(
    total_queries: int,
    successful_retrievals: int,
    fallbacks: int,
    avg_latency_ms: float,
    avg_similarity: float,
    threshold: float
) -> None:
    """
    Log aggregate retrieval statistics.
    
    Args:
        total_queries: Total number of retrieval queries
        successful_retrievals: Number of queries with sufficient retrieval
        fallbacks: Number of fallback events
        avg_latency_ms: Average retrieval latency in milliseconds
        avg_similarity: Average similarity score of retrieved episodes
        threshold: The similarity threshold used
    """
    logger = get_stats_logger()
    extra_data = {
        "event_type": "retrieval_stats",
        "total_queries": total_queries,
        "successful_retrievals": successful_retrievals,
        "fallback_count": fallbacks,
        "fallback_rate": round(fallbacks / total_queries, 4) if total_queries > 0 else 0.0,
        "avg_latency_ms": round(avg_latency_ms, 2),
        "avg_similarity": round(avg_similarity, 4),
        "threshold": threshold
    }
    logger.info(f"Retrieval statistics logged: {successful_retrievals}/{total_queries} successful", extra={"extra_data": extra_data})