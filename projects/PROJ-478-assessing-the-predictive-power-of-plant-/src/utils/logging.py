"""
Structured logging and provenance tracking for the plant traits SDM pipeline.

This module provides:
- JSON-formatted logging for machine-readable logs
- Provenance tracking for data lineage and reproducibility
- Centralized logger configuration
- Error context capture with stack traces
"""
import logging
import json
import os
import sys
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import uuid
import hashlib

# Constants for provenance tracking
PROVENANCE_LOG_DIR = "data/metadata/provenance"
PROVENANCE_FILENAME = "provenance_log.jsonl"
RUN_ID_ENV_VAR = "LLMXIVE_RUN_ID"

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging output."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "run_id": os.environ.get(RUN_ID_ENV_VAR, "unknown"),
            "hostname": os.uname().nodename if hasattr(os, "uname") else "unknown"
        }
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_entry)

class ProvenanceAdapter:
    """Tracks data provenance and lineage for reproducibility."""
    
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or os.environ.get(RUN_ID_ENV_VAR) or str(uuid.uuid4())
        self.provenance_records: List[Dict[str, Any]] = []
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """Create provenance log directory if it doesn't exist."""
        log_path = Path(PROVENANCE_LOG_DIR)
        log_path.mkdir(parents=True, exist_ok=True)
    
    def _get_log_file_path(self) -> Path:
        """Get the path to the provenance log file."""
        return Path(PROVENANCE_LOG_DIR) / self.run_id / PROVENANCE_FILENAME
    
    def log_data_source(self, 
                      source_type: str,
                      source_path: str,
                      checksum: Optional[str] = None,
                      parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Log a data source with its metadata."""
        record = {
            "type": "data_source",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "source_type": source_type,
            "source_path": source_path,
            "checksum": checksum,
            "parameters": parameters or {},
            "id": str(uuid.uuid4())
        }
        self.provenance_records.append(record)
        self._write_record(record)
        return record
    
    def log_data_transformation(self,
                              operation: str,
                              input_ids: List[str],
                              output_id: str,
                              parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Log a data transformation step."""
        record = {
            "type": "transformation",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "operation": operation,
            "input_ids": input_ids,
            "output_id": output_id,
            "parameters": parameters or {},
            "id": str(uuid.uuid4())
        }
        self.provenance_records.append(record)
        self._write_record(record)
        return record
    
    def log_model_training(self,
                         model_type: str,
                         parameters: Dict[str, Any],
                         input_data_id: str,
                         metrics: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Log a model training event."""
        record = {
            "type": "model_training",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "model_type": model_type,
            "parameters": parameters,
            "input_data_id": input_data_id,
            "metrics": metrics or {},
            "id": str(uuid.uuid4())
        }
        self.provenance_records.append(record)
        self._write_record(record)
        return record
    
    def log_error(self,
                error_type: str,
                error_message: str,
                context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Log an error with context."""
        record = {
            "type": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "run_id": self.run_id,
            "error_type": error_type,
            "error_message": error_message,
            "context": context or {},
            "traceback": traceback.format_exc() if context else None,
            "id": str(uuid.uuid4())
        }
        self.provenance_records.append(record)
        self._write_record(record)
        return record
    
    def _write_record(self, record: Dict[str, Any]):
        """Write a single record to the log file."""
        log_file = self._get_log_file_path()
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, "a") as f:
            f.write(json.dumps(record) + "\n")
    
    def get_provenance_chain(self, record_id: str) -> List[Dict[str, Any]]:
        """Get the full provenance chain for a given record."""
        chain = []
        current_id = record_id
        visited = set()
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            for record in self.provenance_records:
                if record["id"] == current_id:
                    chain.append(record)
                    # Find inputs
                    if "input_ids" in record:
                        current_id = record["input_ids"][0] if record["input_ids"] else None
                    elif "input_data_id" in record:
                        current_id = record["input_data_id"]
                    else:
                        current_id = None
                    break
            else:
                break
        
        return list(reversed(chain))

# Global provenance tracker instance
_provenance_tracker: Optional[ProvenanceAdapter] = None

def get_provenance_tracker(run_id: Optional[str] = None) -> ProvenanceAdapter:
    """Get or create the global provenance tracker."""
    global _provenance_tracker
    if _provenance_tracker is None:
        _provenance_tracker = ProvenanceAdapter(run_id)
    return _provenance_tracker

def setup_logging(log_level: str = "INFO", 
                log_file: Optional[str] = None,
                json_format: bool = True) -> logging.Logger:
    """
    Configure the logging system with optional JSON formatting.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        json_format: If True, use JSON formatter; otherwise use standard format
    
    Returns:
        Configured root logger
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatter
    if json_format:
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def log_provenance(logger: logging.Logger,
                 operation: str,
                 details: Dict[str, Any]) -> None:
    """
    Log a provenance event with structured details.
    
    Args:
        logger: Logger instance to use
        operation: Type of operation being logged
        details: Dictionary of operation details
    """
    tracker = get_provenance_tracker()
    
    # Add run_id to details
    details["run_id"] = tracker.run_id
    
    # Log with extra fields for JSON formatter
    extra = {"extra_fields": {"operation": operation, **details}}
    logger.info(f"Provenance: {operation}", extra=extra)
    
    # Also log to provenance tracker
    if operation == "data_source":
        tracker.log_data_source(
            source_type=details.get("source_type", "unknown"),
            source_path=details.get("source_path", ""),
            checksum=details.get("checksum"),
            parameters=details.get("parameters")
        )
    elif operation == "transformation":
        tracker.log_data_transformation(
            operation=details.get("transformation_type", "unknown"),
            input_ids=details.get("input_ids", []),
            output_id=details.get("output_id", ""),
            parameters=details.get("parameters")
        )
    elif operation == "model_training":
        tracker.log_model_training(
            model_type=details.get("model_type", "unknown"),
            parameters=details.get("parameters", {}),
            input_data_id=details.get("input_data_id", ""),
            metrics=details.get("metrics")
        )

def log_error(logger: logging.Logger,
            error_message: str,
            context: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an error with full context and stack trace.
    
    Args:
        logger: Logger instance to use
        error_message: Error message
        context: Optional dictionary of contextual information
    """
    tracker = get_provenance_tracker()
    
    # Log to standard logger
    extra = {"extra_fields": {"context": context or {}}}
    logger.error(f"Error: {error_message}", exc_info=True, extra=extra)
    
    # Log to provenance tracker
    tracker.log_error(
        error_type=type(context.get("exception", Exception)).__name__ if context and "exception" in context else "UnknownError",
        error_message=error_message,
        context=context
    )

def save_provenance_report(output_path: Optional[str] = None) -> str:
    """
    Save the complete provenance report to a file.
    
    Args:
        output_path: Optional output path for the report
    
    Returns:
        Path to the saved report
    """
    tracker = get_provenance_tracker()
    
    if output_path is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_path = f"results/provenance_report_{timestamp}.json"
    
    report = {
        "run_id": tracker.run_id,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_records": len(tracker.provenance_records),
        "records": tracker.provenance_records
    }
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write report
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    
    return output_path