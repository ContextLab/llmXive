"""
Audit logging infrastructure for failures, truncations, and pipeline events.

This module provides a centralized logging system for the llmXive pipeline,
ensuring all critical events (failures, truncations, inference steps, scoring)
are recorded with structured JSON payloads for auditability.

Dependencies:
    - code/data/models.py (for type hints and validation context)
    - code/utils/config.py (for configuration defaults)
"""
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Import models to ensure type consistency if needed for future extensions
# from data.models import BenchmarkResult, Response # Currently unused but available

# Global logger instance
_logger: Optional[logging.Logger] = None
_log_dir: Optional[Path] = None

# Default configuration constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_DIR = "logs"
LOG_FILE_PREFIX = "llmXive"

def setup_logging(
    log_dir: str = DEFAULT_LOG_DIR,
    log_level: int = DEFAULT_LOG_LEVEL,
    enable_file_logging: bool = True,
    enable_console_logging: bool = True
) -> logging.Logger:
    """
    Set up the global logger with console and file handlers.
    
    Initializes the logging infrastructure for the llmXive project.
    Creates the log directory if it doesn't exist and configures
    both file and console handlers with appropriate formatters.
    
    Args:
        log_dir: Directory to store log files (default: "logs").
        log_level: Logging level (default: logging.INFO).
        enable_file_logging: Whether to write to file (default: True).
        enable_console_logging: Whether to write to console (default: True).
        
    Returns:
        Configured logger instance.
        
    Raises:
        OSError: If log directory cannot be created.
    """
    global _logger, _log_dir
    if _logger is not None:
        return _logger

    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    # Clear existing handlers to prevent duplicate logs
    logger.handlers.clear()

    # Create log directory if needed
    log_path = Path(log_dir)
    if enable_file_logging:
        try:
            log_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            # Fallback to console-only if directory creation fails
            print(f"Warning: Could not create log directory {log_dir}: {e}")
            enable_file_logging = False

    if enable_file_logging:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_path / f"{LOG_FILE_PREFIX}_{timestamp}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Console handler
    if enable_console_logging:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            "%(levelname)s: %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    _logger = logger
    _log_dir = log_path
    return logger

def get_logger() -> logging.Logger:
    """
    Get the global logger instance.
    
    Initializes with defaults if not set up yet.
    
    Returns:
        Configured logger instance.
    """
    global _logger
    if _logger is None:
        _logger = setup_logging()
    return _logger

def log_failure(event_type: str, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Log a failure event to the audit log.
    
    Used for capturing critical errors such as OOM, validation failures,
    or data processing errors.
    
    Args:
        event_type: Type of failure (e.g., "OOM", "TRUNCATION", "VALIDATION_ERROR", "DOWNLOAD_FAILED").
        message: Human-readable description of the failure.
        details: Optional dictionary of additional context (e.g., stack trace, file paths).
    """
    logger = get_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "FAILURE",
        "event_type": event_type,
        "message": message,
        "details": details or {}
    }
    logger.error(json.dumps(log_entry))

def log_truncation(prompt_id: str, reason: str, tokens_generated: int, max_tokens: int):
    """
    Log a truncation event.
    
    Records when generation stops prematurely due to token limits or timeouts.
    
    Args:
        prompt_id: Identifier of the prompt that was truncated.
        reason: Reason for truncation (e.g., "max_tokens", "timeout", "network_error").
        tokens_generated: Number of tokens generated before truncation.
        max_tokens: The configured maximum token limit.
    """
    logger = get_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "TRUNCATION",
        "prompt_id": prompt_id,
        "reason": reason,
        "tokens_generated": tokens_generated,
        "max_tokens": max_tokens
    }
    logger.warning(json.dumps(log_entry))

def log_inference_start(prompt_id: str, model_name: str):
    """
    Log the start of an inference run.
    
    Args:
        prompt_id: Unique identifier for the prompt.
        model_name: Name or path of the model being used.
    """
    logger = get_logger()
    logger.info(f"Inference start: prompt_id={prompt_id}, model={model_name}")

def log_inference_end(prompt_id: str, status: str, duration_seconds: float):
    """
    Log the end of an inference run.
    
    Args:
        prompt_id: Unique identifier for the prompt.
        status: Outcome status (e.g., "SUCCESS", "FAILED", "TIMEOUT").
        duration_seconds: Time taken for inference in seconds.
    """
    logger = get_logger()
    logger.info(f"Inference end: prompt_id={prompt_id}, status={status}, duration={duration_seconds:.2f}s")

def log_scored_entry(prompt_id: str, scores: Dict[str, float], confidence: float):
    """
    Log a scored entry.
    
    Records the results of the automated scoring process.
    
    Args:
        prompt_id: Unique identifier for the prompt.
        scores: Dictionary of metric scores (e.g., {"novelty": 0.8, "feasibility": 0.6}).
        confidence: Confidence score of the scoring model.
    """
    logger = get_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "SCORE",
        "prompt_id": prompt_id,
        "scores": scores,
        "confidence": confidence
    }
    logger.info(json.dumps(log_entry))

def log_low_confidence(prompt_id: str, reason: str, metrics: Dict[str, float]):
    """
    Log a low-confidence scoring event.
    
    Flags entries where the proxy model's confidence is below the threshold,
    requiring manual review or re-scoring.
    
    Args:
        prompt_id: Unique identifier for the prompt.
        reason: Explanation for low confidence (e.g., "high_variance", "entropy_too_high").
        metrics: Dictionary of metrics contributing to the low confidence.
    """
    logger = get_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "LOW_CONFIDENCE",
        "prompt_id": prompt_id,
        "reason": reason,
        "metrics": metrics
    }
    logger.warning(json.dumps(log_entry))

def log_audit_event(event_type: str, entity_id: str, action: str, details: Optional[Dict[str, Any]] = None):
    """
    Generic audit log entry for any pipeline event.
    
    Provides a flexible way to log custom events that don't fit specific
    helper functions.
    
    Args:
        event_type: Category of the event (e.g., "DATA_INGESTION", "MODEL_LOAD", "VALIDATION").
        entity_id: Identifier of the entity involved (e.g., dataset name, model ID).
        action: Action performed (e.g., "STARTED", "COMPLETED", "SKIPPED").
        details: Optional additional context.
    """
    logger = get_logger()
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "type": "AUDIT",
        "event_type": event_type,
        "entity_id": entity_id,
        "action": action,
        "details": details or {}
    }
    logger.info(json.dumps(log_entry))

def get_log_directory() -> Optional[Path]:
    """
    Get the directory where logs are being written.
    
    Returns:
        Path to the log directory, or None if not yet configured.
    """
    return _log_dir