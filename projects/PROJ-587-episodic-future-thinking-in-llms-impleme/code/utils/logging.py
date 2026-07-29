"""
Logging utilities for the Episodic Future Thinking project.

Provides specialized loggers for different components (retrieval, fallback, confidence, etc.)
and ensures no circular imports with other modules.
"""
import logging
import json
import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List

# Ensure we use the stdlib logging module
# This file is named logging.py, so 'import logging' would normally cause a circular import
# if not handled carefully. However, since this is the definition of the logging module,
# we must use the built-in logging functionality.
# To avoid recursion, we use the built-in logging module directly.
# The standard approach when a module is named 'logging.py' is to not import it,
# but use the built-in 'logging' module which is already available.
# However, in this context, we are defining the logging module, so we can use
# the built-in logging module.
# The previous error was in stats.py trying to import logging and getting this file.
# This file itself is fine.

_loggers: Dict[str, logging.Logger] = {}
_handlers: Dict[str, List[logging.Handler]] = {}

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if hasattr(record, 'extra_data'):
            log_data["extra"] = record.extra_data
        return json.dumps(log_data)

def _get_logger(name: str, level: int = logging.INFO, use_json: bool = False) -> logging.Logger:
    """Get or create a logger with the specified name."""
    if name not in _loggers:
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Avoid adding handlers multiple times
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            if use_json:
                handler.setFormatter(JSONFormatter())
            else:
                handler.setFormatter(logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                ))
            logger.addHandler(handler)

        _loggers[name] = logger

    return _loggers[name]

def get_default_logger() -> logging.Logger:
    """Get the default logger."""
    return _get_logger("default", use_json=False)

def get_retrieval_logger() -> logging.Logger:
    """Get the retrieval-specific logger."""
    return _get_logger("episodic_retrieval", use_json=True)

def get_fallback_logger() -> logging.Logger:
    """Get the fallback-specific logger."""
    return _get_logger("fallback_handler", use_json=True)

def get_confidence_logger() -> logging.Logger:
    """Get the confidence-specific logger."""
    return _get_logger("confidence_calibration", use_json=True)

def get_conflict_logger() -> logging.Logger:
    """Get the conflict-specific logger."""
    return _get_logger("conflict_resolution", use_json=True)

def get_stats_logger() -> logging.Logger:
    """Get the statistics-specific logger."""
    return _get_logger("statistical_analysis", use_json=True)

def log_retrieval_trigger(
    query_id: str,
    retrieved_count: int,
    similarity_scores: List[float],
    latency_ms: float
) -> None:
    """Log a retrieval event."""
    logger = get_retrieval_logger()
    logger.info(
        f"Retrieved {retrieved_count} episodes for query {query_id}",
        extra={'extra_data': {
            'query_id': query_id,
            'retrieved_count': retrieved_count,
            'similarity_scores': similarity_scores,
            'latency_ms': latency_ms
        }}
    )

def log_fallback_event(
    query_id: str,
    reason: str,
    fallback_method: str
) -> None:
    """Log a fallback event."""
    logger = get_fallback_logger()
    logger.info(
        f"Fallback triggered for query {query_id}: {reason}",
        extra={'extra_data': {
            'query_id': query_id,
            'reason': reason,
            'fallback_method': fallback_method
        }}
    )

def log_confidence_score(
    scenario_id: str,
    confidence_score: float,
    counterfactual_details: Optional[Dict[str, Any]] = None
) -> None:
    """Log confidence score for a scenario."""
    logger = get_confidence_logger()
    log_msg = f"Confidence score {confidence_score:.4f} for scenario {scenario_id}"
    if counterfactual_details:
        log_msg += f" (counterfactuals: {len(counterfactual_details)})"
    
    logger.info(
        log_msg,
        extra={'extra_data': {
            'scenario_id': scenario_id,
            'confidence_score': confidence_score,
            'counterfactual_details': counterfactual_details
        }}
    )

def log_episodic_store(
    episode_id: str,
    state_hash: str,
    action_hash: str,
    outcome_hash: str,
    timestamp: datetime
) -> None:
    """Log an episodic memory storage event."""
    logger = get_retrieval_logger()
    logger.info(
        f"Stored episode {episode_id}",
        extra={'extra_data': {
            'episode_id': episode_id,
            'state_hash': state_hash,
            'action_hash': action_hash,
            'outcome_hash': outcome_hash,
            'timestamp': timestamp.isoformat()
        }}
    )

def log_conflict_detected(
    state_hash: str,
    episode_ids: List[str],
    resolution: str
) -> None:
    """Log a conflict detection and resolution event."""
    logger = get_conflict_logger()
    logger.info(
        f"Conflict detected for state {state_hash}, resolved as {resolution}",
        extra={'extra_data': {
            'state_hash': state_hash,
            'episode_ids': episode_ids,
            'resolution': resolution
        }}
    )

def log_retrieval_stats(
    total_queries: int,
    successful_retrievals: int,
    fallbacks: int,
    avg_latency_ms: float
) -> None:
    """Log overall retrieval statistics."""
    logger = get_stats_logger()
    logger.info(
        f"Retrieval stats: {successful_retrievals}/{total_queries} successful, {fallbacks} fallbacks, avg latency {avg_latency_ms:.2f}ms",
        extra={'extra_data': {
            'total_queries': total_queries,
            'successful_retrievals': successful_retrievals,
            'fallbacks': fallbacks,
            'avg_latency_ms': avg_latency_ms
        }}
    )