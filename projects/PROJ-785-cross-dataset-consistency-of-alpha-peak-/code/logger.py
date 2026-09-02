import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import traceback

from config import get_project_root, ensure_directories_exist
from exceptions import DataIntegrityError, MissingMetadataError, PipelineFailureError

# Global logger instance
_logger: Optional[logging.Logger] = None
_configured: bool = False

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    Includes timestamp, level, logger name, message, and optional extra context.
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

        # Include extra fields if present
        if hasattr(record, "extra_data"):
            log_entry["context"] = record.extra_data

        # Include exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }

        return json.dumps(log_entry)

class ConsoleFormatter(logging.Formatter):
    """
    Custom formatter for console output with human-readable text.
    """
    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)
        logger_name = record.name.ljust(20)
        message = record.getMessage()
        
        output = f"[{timestamp}] {level} {logger_name}: {message}"
        
        if hasattr(record, "extra_data"):
            output += f" | Context: {record.extra_data}"
        
        if record.exc_info:
            output += "\n" + "".join(traceback.format_exception(*record.exc_info))
        
        return output

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Retrieve or create a logger with the specified name.
    Ensures the logger is configured with the custom formatters.
    """
    global _configured
    if not _configured:
        configure_root_logger()
    
    return logging.getLogger(name)

def configure_root_logger(log_file: Optional[str] = None) -> None:
    """
    Configure the root logger with both console and file handlers.
    Uses structured JSON formatting for file logs and human-readable for console.
    """
    global _configured, _logger
    
    if _configured:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    root_logger.handlers.clear()

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = ConsoleFormatter()
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # File Handler (Structured JSON)
    if log_file:
        log_path = Path(log_file)
        ensure_directories_exist(log_path.parent)
        
        file_handler = logging.FileHandler(log_path, mode='a')
        file_handler.setLevel(logging.DEBUG) # Capture all levels for audit
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

    _configured = True

def log_structured_event(
    event_type: str, 
    message: str, 
    level: str = "INFO", 
    logger_name: str = "llmXive",
    **kwargs
) -> None:
    """
    Logs a structured event with optional context data.
    
    Args:
        event_type: Type of event (e.g., 'DATASET_DOWNLOADED', 'PIPELINE_START')
        message: Human-readable description
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        logger_name: Name of the logger
        **kwargs: Additional context data to include in the log
    """
    logger = get_logger(logger_name)
    
    # Map level string to logging constant
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL
    }
    log_level = level_map.get(level.upper(), logging.INFO)

    # Prepare extra data
    extra_data = {"event_type": event_type, **kwargs}

    # Create a log record with extra data
    record = logger.makeRecord(
        logger.name, log_level, "", 0, message, (), None
    )
    record.extra_data = extra_data

    logger.handle(record)

def log_data_integrity_error(
    error: DataIntegrityError,
    context: Optional[Dict[str, Any]] = None,
    logger_name: str = "llmXive"
) -> None:
    """
    Specialized logging for DataIntegrityError exceptions.
    Ensures the error is logged at ERROR level with full traceback.
    """
    logger = get_logger(logger_name)
    extra = context or {}
    logger.error(
        f"Data Integrity Error: {str(error)}",
        exc_info=True,
        extra={"extra_data": extra}
    )

def log_pipeline_failure(
    pipeline_name: str,
    error: Exception,
    logger_name: str = "llmXive"
) -> None:
    """
    Logs a pipeline failure event.
    """
    logger = get_logger(logger_name)
    logger.critical(
        f"Pipeline Failure in {pipeline_name}: {str(error)}",
        exc_info=True,
        extra={"extra_data": {"pipeline": pipeline_name}}
    )
