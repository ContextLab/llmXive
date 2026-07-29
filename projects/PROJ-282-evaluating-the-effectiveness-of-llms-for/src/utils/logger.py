"""
Structured logging utilities for the llmXive pipeline.

Provides a consistent JSON-formatted logging interface for all pipeline stages,
ensuring machine-readable logs for monitoring and debugging.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class StructuredFormatter(logging.Formatter):
    """
    A logging formatter that outputs JSON-structured logs.
    
    Each log record is serialized into a JSON object containing:
    - timestamp: ISO 8601 formatted timestamp
    - level: Log level (INFO, DEBUG, ERROR, etc.)
    - stage: Pipeline stage identifier (if set in extra)
    - message: The log message
    - context: Additional context data (if provided in extra)
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add stage identifier if present in extra
        if hasattr(record, "stage"):
            log_data["stage"] = record.stage
        
        # Add context data if present in extra
        if hasattr(record, "context") and record.context:
            log_data["context"] = record.context
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get or create a logger with structured JSON formatting.
    
    Args:
        name: Logger name (typically __name__ of the calling module)
        log_file: Optional path to write logs to. If None, logs to stdout only.
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Create formatter
    formatter = StructuredFormatter()
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def create_project_logger(project_root: Path, stage_name: str) -> logging.Logger:
    """
    Create a project-specific logger with stage-based log file.
    
    Args:
        project_root: Root directory of the project
        stage_name: Name of the current pipeline stage (e.g., "ingest", "feature_extraction")
    
    Returns:
        Configured logger instance
    """
    log_dir = project_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"{stage_name}.log"
    logger = get_logger(f"llmXive.{stage_name}", log_file)
    
    # Add stage context to all log records
    class StageFilter(logging.Filter):
        def filter(self, record):
            record.stage = stage_name
            return True
    
    for handler in logger.handlers:
        handler.addFilter(StageFilter())
    
    return logger


def log_stage_start(logger: logging.Logger, stage_name: str, config: Optional[Dict] = None) -> None:
    """
    Log the start of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage
        config: Optional configuration dictionary to log
    """
    extra = {"stage": stage_name, "context": {"event": "stage_start"} | (config or {})}
    logger.info(f"Stage '{stage_name}' starting", extra=extra)


def log_stage_complete(logger: logging.Logger, stage_name: str, metrics: Optional[Dict] = None) -> None:
    """
    Log the successful completion of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage
        metrics: Optional metrics dictionary to log
    """
    extra = {"stage": stage_name, "context": {"event": "stage_complete"} | (metrics or {})}
    logger.info(f"Stage '{stage_name}' completed successfully", extra=extra)


def log_stage_failure(logger: logging.Logger, stage_name: str, error: str, error_type: Optional[str] = None) -> None:
    """
    Log the failure of a pipeline stage.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage
        error: Error message
        error_type: Optional error type/class name
    """
    context = {"event": "stage_failure", "error_message": error}
    if error_type:
        context["error_type"] = error_type
    
    extra = {"stage": stage_name, "context": context}
    logger.error(f"Stage '{stage_name}' failed: {error}", extra=extra)


def log_artifact(
    logger: logging.Logger,
    stage_name: str,
    artifact_path: str,
    artifact_type: str,
    metadata: Optional[Dict] = None
) -> None:
    """
    Log the creation or processing of an artifact.
    
    Args:
        logger: Logger instance
        stage_name: Name of the stage producing the artifact
        artifact_path: Path to the artifact
        artifact_type: Type of artifact (e.g., "csv", "json", "model")
        metadata: Optional metadata dictionary
    """
    context = {
        "event": "artifact",
        "artifact_path": artifact_path,
        "artifact_type": artifact_type,
    }
    if metadata:
        context.update(metadata)
    
    extra = {"stage": stage_name, "context": context}
    logger.info(f"Artifact produced: {artifact_path}", extra=extra)


# Convenience logger for the utils module itself
_utils_logger = get_logger("llmXive.utils")