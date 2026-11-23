"""
Structured logging and provenance tracking for the plant traits SDM pipeline.

This module provides:
- JsonFormatter: JSON-formatted log output for machine parsing.
- ProvenanceAdapter: Tracks data lineage, source URLs, and processing steps.
- setup_logging: Configures root logger with JSON output and file handlers.
- get_logger: Factory for retrieving named loggers.
- log_provenance: Helper to log data lineage events.
- log_error: Helper to log errors with context.
"""

import logging
import json
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

# Constants
LOG_DIR = Path("data") / "logs"
LOG_FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FILE = "pipeline_provenance.jsonl"
TEXT_LOG_FILE = "pipeline.log"

class JsonFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra fields.
    """

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

        # Include extra fields if present
        if hasattr(record, "provenance"):
            log_data["provenance"] = record.provenance
        if hasattr(record, "source"):
            log_data["source"] = record.source
        if hasattr(record, "step"):
            log_data["step"] = record.step
        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "exc_info") and record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


class ProvenanceAdapter:
    """
    Tracks data lineage and processing steps for provenance logging.
    Stores a list of events describing data transformations.
    """

    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log_fetch(self, source: str, dataset_id: str, species: str, record_count: int):
        """Log data fetching event."""
        event = {
            "type": "fetch",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": source,
            "dataset_id": dataset_id,
            "species": species,
            "record_count": record_count,
        }
        self.events.append(event)

    def log_preprocess(self, step_name: str, input_records: int, output_records: int, params: Dict[str, Any]):
        """Log preprocessing event."""
        event = {
            "type": "preprocess",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "step": step_name,
            "input_records": input_records,
            "output_records": output_records,
            "parameters": params,
        }
        self.events.append(event)

    def log_model_train(self, model_type: str, species: str, cv_folds: int, metrics: Dict[str, float]):
        """Log model training event."""
        event = {
            "type": "model_train",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "model_type": model_type,
            "species": species,
            "cv_folds": cv_folds,
            "metrics": metrics,
        }
        self.events.append(event)

    def log_analysis(self, analysis_type: str, species_count: int, result_summary: Dict[str, Any]):
        """Log analysis event."""
        event = {
            "type": "analysis",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "analysis_type": analysis_type,
            "species_count": species_count,
            "result_summary": result_summary,
        }
        self.events.append(event)

    def save_to_file(self, filepath: Path):
        """Save all provenance events to a JSONL file."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w") as f:
            for event in self.events:
                f.write(json.dumps(event) + "\n")

    def get_events(self) -> List[Dict[str, Any]]:
        """Return all recorded events."""
        return self.events


# Global provenance tracker
_provenance_tracker: Optional[ProvenanceAdapter] = None


def get_provenance_tracker() -> ProvenanceAdapter:
    """Get or create the global provenance tracker."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceAdapter()
    return _provenance_tracker


def setup_logging(
    log_level: int = logging.INFO,
    enable_json: bool = True,
    enable_file: bool = True,
    console_output: bool = True,
):
    """
    Configure the root logger with JSON formatting and optional file handlers.

    Args:
        log_level: Logging level (e.g., logging.DEBUG, logging.INFO).
        enable_json: If True, add a JSON file handler.
        enable_file: If True, add a text file handler.
        console_output: If True, add a console handler.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = []  # Clear existing handlers

    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(LOG_FORMATTER)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # JSON file handler for provenance
    if enable_json:
        json_handler = logging.FileHandler(LOG_DIR / JSON_LOG_FILE)
        json_handler.setLevel(log_level)
        json_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(json_handler)

    # Text file handler for human-readable logs
    if enable_file:
        text_handler = logging.FileHandler(LOG_DIR / TEXT_LOG_FILE)
        text_handler.setLevel(log_level)
        text_handler.setFormatter(logging.Formatter(LOG_FORMATTER))
        root_logger.addHandler(text_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Args:
        name: Logger name (e.g., 'src.data.fetch_gbif').

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


def log_provenance(
    logger_name: str,
    event_type: str,
    **kwargs,
):
    """
    Log a provenance event to both the logger and the global tracker.

    Args:
        logger_name: Name of the logger to use.
        event_type: Type of event (e.g., 'fetch', 'preprocess').
        **kwargs: Event-specific data to log.
    """
    logger = get_logger(logger_name)
    tracker = get_provenance_tracker()

    # Create a log record with provenance data
    message = f"{event_type.capitalize()} event recorded"
    extra = {"provenance": kwargs}

    # Route to appropriate handler based on event type
    if event_type == "fetch":
        tracker.log_fetch(
            source=kwargs.get("source", "unknown"),
            dataset_id=kwargs.get("dataset_id", "unknown"),
            species=kwargs.get("species", "unknown"),
            record_count=kwargs.get("record_count", 0),
        )
    elif event_type == "preprocess":
        tracker.log_preprocess(
            step_name=kwargs.get("step_name", "unknown"),
            input_records=kwargs.get("input_records", 0),
            output_records=kwargs.get("output_records", 0),
            params=kwargs.get("params", {}),
        )
    elif event_type == "model_train":
        tracker.log_model_train(
            model_type=kwargs.get("model_type", "unknown"),
            species=kwargs.get("species", "unknown"),
            cv_folds=kwargs.get("cv_folds", 0),
            metrics=kwargs.get("metrics", {}),
        )
    elif event_type == "analysis":
        tracker.log_analysis(
            analysis_type=kwargs.get("analysis_type", "unknown"),
            species_count=kwargs.get("species_count", 0),
            result_summary=kwargs.get("result_summary", {}),
        )

    logger.info(message, extra=extra)


def log_error(
    logger_name: str,
    error_message: str,
    error_type: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
):
    """
    Log an error with optional context and error type.

    Args:
        logger_name: Name of the logger to use.
        error_message: Error message to log.
        error_type: Type of error (e.g., 'ValueError', 'DataFetchError').
        context: Additional context data.
    """
    logger = get_logger(logger_name)
    extra = {}
    if error_type:
        extra["error_type"] = error_type
    if context:
        extra["context"] = context

    logger.error(error_message, extra=extra, exc_info=True)


def save_provenance_report(output_path: Optional[str] = None):
    """
    Save the global provenance tracker to a file.

    Args:
        output_path: Path to save the report. Defaults to data/logs/pipeline_provenance.jsonl.
    """
    tracker = get_provenance_tracker()
    if output_path is None:
        output_path = str(LOG_DIR / JSON_LOG_FILE)

    tracker.save_to_file(Path(output_path))
    get_logger("src.utils.logging").info(f"Provenance report saved to {output_path}")