import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

class StructuredFormatter(logging.Formatter):
    """
    Custom logging formatter that outputs structured JSON logs.
    Includes timestamp, log level, stage, and arbitrary extra fields.
    """
    def __init__(self, stage: str = "general"):
        super().__init__()
        self.stage = stage

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "stage": self.stage,
            "message": record.getMessage(),
            "logger": record.name,
            "function": record.funcName,
            "line": record.lineno
        }

        # Attach extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        # Handle exceptions if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)

def get_logger(name: str, stage: str = "general", log_file: Optional[str] = None) -> logging.Logger:
    """
    Creates and configures a logger with the StructuredFormatter.
    
    Args:
        name: Name of the logger (usually __name__).
        stage: The pipeline stage name for context.
        log_file: Optional path to a file to write logs to.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter(stage))
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter(stage))
        logger.addHandler(file_handler)
    
    return logger

def _attach_extra(logger: logging.Logger, data: Dict[str, Any]) -> logging.Logger:
    """Helper to attach extra data to log records via a custom Filter or by wrapping."""
    # Since we can't easily inject into the record without a custom filter, 
    # we will rely on the caller passing data via the logging methods if supported,
    # or we use a custom LogRecord factory. 
    # For simplicity in this specific implementation, we will use a closure-based approach
    # or simply assume the user passes data in the message or we modify the formatter logic.
    # 
    # Better approach: Use a custom Filter.
    class DataFilter(logging.Filter):
        def __init__(self, data):
            super().__init__()
            self.data = data
        
        def filter(self, record):
            record.extra_data = self.data
            return True

    logger.addFilter(DataFilter(data))
    return logger

def log_stage_start(logger: logging.Logger, stage_name: str, config: Optional[Dict[str, Any]] = None) -> None:
    """Logs the beginning of a pipeline stage."""
    logger.info(f"--- Stage '{stage_name}' started ---", extra={"stage_override": stage_name})
    if config:
        logger.info("Stage configuration", extra={"config": config})

def log_stage_complete(logger: logging.Logger, stage_name: str, duration_seconds: Optional[float] = None, artifact_path: Optional[str] = None) -> None:
    """Logs the successful completion of a pipeline stage."""
    msg = f"--- Stage '{stage_name}' completed ---"
    if duration_seconds is not None:
        msg += f" (Duration: {duration_seconds:.2f}s)"
    logger.info(msg)
    if artifact_path:
        log_artifact(logger, "output_file", artifact_path)

def log_stage_failure(logger: logging.Logger, stage_name: str, error: Exception) -> None:
    """Logs a failure in a pipeline stage."""
    logger.error(f"--- Stage '{stage_name}' FAILED ---", exc_info=True)
    logger.error(f"Error: {str(error)}")

def log_artifact(logger: logging.Logger, artifact_name: str, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
    """Logs the creation or presence of an artifact."""
    data = {"artifact_name": artifact_name, "path": path}
    if metadata:
        data["metadata"] = metadata
    logger.info(f"Artifact logged: {artifact_name}", extra={"data": data})

# Convenience function to create a standard project logger
def create_project_logger(stage_name: str, log_dir: str = "logs") -> logging.Logger:
    """
    Creates a logger for the project with a specific stage and log file.
    """
    log_file_path = f"{log_dir}/{stage_name}.log"
    return get_logger(__name__, stage=stage_name, log_file=log_file_path)