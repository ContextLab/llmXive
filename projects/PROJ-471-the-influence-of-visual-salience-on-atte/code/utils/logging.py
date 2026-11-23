"""
Structured logging utilities for the llmXive pipeline.

Provides a centralized logging configuration that adheres to the project's
requirements for structured, reproducible, and auditable logs.
"""
import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Import project paths from config to ensure logs go to the correct location
from config import get_paths, load_config


class JsonFormatter(logging.Formatter):
    """
    A custom formatter that outputs log records as JSON lines.
    This ensures logs are machine-parseable for downstream analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


class ContextFilter(logging.Filter):
    """
    Adds context-specific information (like run_id or project stage) to all log records.
    """

    def __init__(self, context: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.context = context or {}

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    json_format: bool = True,
    context: Optional[Dict[str, Any]] = None,
) -> logging.Logger:
    """
    Configures the root logger for the project with structured output.

    Args:
        log_level: The logging level (e.g., 'DEBUG', 'INFO', 'WARNING').
        log_file: Optional path to a log file. If None, logs only to stdout.
        json_format: If True, uses JSON formatting; otherwise uses standard text formatting.
        context: Optional dictionary of key-value pairs to inject into every log record.

    Returns:
        The configured root logger instance.
    """
    # Determine log level
    level = getattr(logging, log_level.upper(), logging.INFO)

    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers to avoid duplicates in repeated calls
    root_logger.handlers.clear()

    # Create formatters
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Create file handler if path provided
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Add context filter if provided
    if context:
        context_filter = ContextFilter(context)
        root_logger.addFilter(context_filter)

    return root_logger


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieves a logger with the specified name.
    Ensures the logger inherits the root configuration.

    Args:
        name: The name of the logger (typically __name__ of the module).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)


def log_experiment_start(run_id: str, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Logs the start of an experiment run with a unique ID and optional configuration snapshot.

    Args:
        run_id: Unique identifier for the current run.
        config: Optional dictionary containing the experiment configuration.
    """
    logger = get_logger("experiment")
    logger.info(
        "Experiment started",
        extra={"extra_data": {"run_id": run_id, "config_snapshot": config}}
    )


def log_artifact_generation(artifact_path: str, artifact_type: str, status: str = "success") -> None:
    """
    Logs the generation of a data artifact.

    Args:
        artifact_path: Relative or absolute path to the generated artifact.
        artifact_type: Type of artifact (e.g., 'salience_map', 'fixation_metrics').
        status: Status of the generation ('success', 'failed', 'partial').
    """
    logger = get_logger("artifacts")
    logger.info(
        f"Artifact {status}: {artifact_type}",
        extra={"extra_data": {"path": artifact_path, "type": artifact_type, "status": status}}
    )


def log_error_context(error_msg: str, context_data: Dict[str, Any]) -> None:
    """
    Logs an error with additional context data for debugging.

    Args:
        error_msg: The error message.
        context_data: Dictionary of contextual information (e.g., input parameters, state).
    """
    logger = get_logger("errors")
    logger.error(
        error_msg,
        extra={"extra_data": context_data}
    )
