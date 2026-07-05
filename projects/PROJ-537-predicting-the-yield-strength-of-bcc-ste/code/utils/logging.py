import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from .checksums import get_logger as _get_checksum_logger

# Ensure the logs directory exists
LOGS_DIR = Path("data/provenance")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Global logger instance
_logger: Optional[logging.Logger] = None

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs for provenance."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        return json.dumps(log_entry)

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get a configured logger instance.
    Returns a singleton logger configured with the StructuredFormatter.
    """
    global _logger
    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        # Remove existing handlers to avoid duplicates
        if _logger.handlers:
            _logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        _logger.addHandler(console_handler)

        # File handler for general logs (optional, can be toggled)
        # log_file = LOGS_DIR / "pipeline.log"
        # file_handler = logging.FileHandler(log_file)
        # file_handler.setFormatter(StructuredFormatter())
        # _logger.addHandler(file_handler)

    return _logger

def log_provenance_event(event_type: str, details: Dict[str, Any]) -> None:
    """
    Log a generic provenance event to the console and optionally to a file.
    """
    logger = get_logger()
    extra = {"event_type": event_type, **details}
    logger.info("Provenance Event", extra={"extra_data": extra})

def log_api_query(service: str, query_params: Dict[str, Any], success: bool, response_time: float, error: Optional[str] = None) -> None:
    """
    Log API query details specifically to `data/provenance/dft_queries.jsonl`.
    This function appends a JSON line for every API interaction.
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "service": service,
        "query_params": query_params,
        "success": success,
        "response_time_seconds": response_time,
        "error": error,
        "type": "api_query"
    }

    # Write to the specific JSONL file for DFT queries
    output_path = Path("data/provenance/dft_queries.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

    # Also log to the main logger for visibility
    logger = get_logger()
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"API Query: {service} -> {status}", extra={"extra_data": {"service": service, "success": success, "response_time": response_time}})

def log_data_artifact(artifact_path: str, operation: str, checksum: Optional[str] = None) -> None:
    """
    Log data artifact creation or modification.
    """
    logger = get_logger()
    extra = {
        "artifact_path": artifact_path,
        "operation": operation,
        "checksum": checksum
    }
    logger.info("Data Artifact Event", extra={"extra_data": extra})
