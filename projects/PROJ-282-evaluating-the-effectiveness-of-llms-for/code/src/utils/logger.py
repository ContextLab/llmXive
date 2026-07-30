"""
Structured logging utility for the llmXive research pipeline.

Provides a consistent JSON-formatted logging interface for all pipeline stages,
ensuring reproducibility and ease of parsing for downstream analysis.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

from src.utils.config import get_project_root


class StructuredFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs JSON-structured logs.
    
    Ensures that every log entry contains:
    - timestamp (ISO 8601)
    - level
    - stage (if available in context)
    - message
    - extra metadata (if provided)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'stage'):
            log_entry["stage"] = record.stage
        
        if hasattr(record, 'artifact'):
            log_entry["artifact"] = record.artifact
        
        if hasattr(record, 'duration_ms'):
            log_entry["duration_ms"] = record.duration_ms
        
        if hasattr(record, 'error_code'):
            log_entry["error_code"] = record.error_code
        
        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)


def get_logger(name: str) -> logging.Logger:
    """
    Retrieve or create a logger with the structured formatter.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    return logger


def create_project_logger(stage_name: str) -> logging.Logger:
    """
    Create a logger specific to a pipeline stage.
    
    Args:
        stage_name: Name of the pipeline stage (e.g., "download", "preprocess")
        
    Returns:
        Logger instance configured for the stage
    """
    logger = get_logger(f"llmXive.{stage_name}")
    logger.stage = stage_name
    return logger


def log_stage_start(logger: logging.Logger, stage_name: str) -> None:
    """
    Log the beginning of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage
    """
    logger.info(f"Stage '{stage_name}' started", extra={"stage": stage_name})


def log_stage_complete(
    logger: logging.Logger, 
    stage_name: str, 
    duration_ms: Optional[float] = None
) -> None:
    """
    Log the successful completion of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage
        duration_ms: Optional duration in milliseconds
    """
    extra = {"stage": stage_name}
    if duration_ms is not None:
        extra["duration_ms"] = duration_ms
    logger.info(f"Stage '{stage_name}' completed", extra=extra)


def log_stage_failure(
    logger: logging.Logger, 
    stage_name: str, 
    error_message: str, 
    error_code: Optional[str] = None
) -> None:
    """
    Log a pipeline stage failure.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage
        error_message: Description of the failure
        error_code: Optional error code for categorization
    """
    extra = {"stage": stage_name, "error_code": error_code}
    logger.error(
        f"Stage '{stage_name}' failed: {error_message}",
        extra=extra,
        exc_info=True
    )


def log_artifact(
    logger: logging.Logger, 
    artifact_path: str, 
    artifact_type: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log the creation or processing of an artifact.
    
    Args:
        logger: Logger instance
        artifact_path: Path to the artifact (relative to project root)
        artifact_type: Type of artifact (e.g., "dataset", "prediction", "feature")
        metadata: Optional metadata dictionary to include
    """
    extra = {"artifact": artifact_path, "artifact_type": artifact_type}
    if metadata:
        extra["metadata"] = metadata
    
    logger.info(
        f"Artifact logged: {artifact_type} at {artifact_path}",
        extra=extra
    )


def log_config(logger: logging.Logger, config_dict: Dict[str, Any]) -> None:
    """
    Log the current configuration for reproducibility.
    
    Args:
        logger: Logger instance
        config_dict: Configuration dictionary to log
    """
    logger.info(
        "Configuration snapshot",
        extra={"config": json.dumps(config_dict, default=str)}
    )


def log_memory_snapshot(logger: logging.Logger, ram_used_gb: float, batch_size: int) -> None:
    """
    Log a memory usage snapshot.
    
    Args:
        logger: Logger instance
        ram_used_gb: Current RAM usage in GB
        batch_size: Current batch size being used
    """
    logger.info(
        f"Memory snapshot: {ram_used_gb:.2f} GB used, batch size: {batch_size}",
        extra={"ram_used_gb": ram_used_gb, "batch_size": batch_size}
    )
