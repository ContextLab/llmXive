"""
Structured logging utility for Socratic Transformers project.

Handles degenerate dialogue events as JSON lines following the schema:
{"event_type": str, "timestamp": str, "details": dict}
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class SocraticJsonFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.
    
    Formats log records as JSON lines with the required schema:
    {
        "event_type": str,      # Log level name (INFO, ERROR, etc.)
        "timestamp": str,        # ISO format timestamp
        "details": dict          # Additional context from log record
    }
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format a log record as a JSON line."""
        event_data = {
            "event_type": record.levelname,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": {
                "message": record.getMessage(),
                "logger": record.name,
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
        }
        
        # Add exception info if present
        if record.exc_info:
            event_data["details"]["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            event_data["details"].update(record.extra_data)
        
        return json.dumps(event_data)


class SocraticLogger(logging.Logger):
    """
    Custom logger class with additional helper methods for dialogue events.
    """
    
    def log_event(self, event_type: str, message: str, **kwargs: Any) -> None:
        """
        Log a structured event with additional details.
        
        Args:
            event_type: Type of event (e.g., "critique_generated", "quality_gate_failed")
            message: Main message text
            **kwargs: Additional details to include in the event
        """
        extra = kwargs.pop('extra', {})
        extra['event_type'] = event_type
        extra.update(kwargs)
        
        self.info(message, extra={'extra_data': extra})


# Register custom logger class
logging.setLoggerClass(SocraticLogger)


def get_logger(name: str, log_file: Optional[str] = None) -> SocraticLogger:
    """
    Get or create a logger with optional JSON file handler.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to log file. If provided, logs are written as JSON lines.
    
    Returns:
        Configured SocraticLogger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler with standard formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler with JSON formatting if log_file specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(SocraticJsonFormatter())
        logger.addHandler(file_handler)
    
    return logger


def log_event(
    logger: logging.Logger,
    event_type: str,
    message: str,
    **kwargs: Any
) -> None:
    """
    Convenience function to log a structured event.
    
    Args:
        logger: Logger instance to use
        event_type: Type of event
        message: Main message text
        **kwargs: Additional details
    """
    if isinstance(logger, SocraticLogger):
        logger.log_event(event_type, message, **kwargs)
    else:
        extra = {'extra_data': {'event_type': event_type, **kwargs}}
        logger.info(message, extra=extra)


def init_default_logger(
    project_root: Optional[Path] = None,
    log_dir_name: str = "logs"
) -> SocraticLogger:
    """
    Initialize the default logger for the project.
    
    Args:
        project_root: Root directory of the project. Defaults to current working directory.
        log_dir_name: Name of the directory to store logs.
    
    Returns:
        Configured default logger
    """
    if project_root is None:
        project_root = Path.cwd()
    
    log_dir = project_root / log_dir_name
    log_file = log_dir / "events.jsonl"
    
    return get_logger("socratic", str(log_file))


def main() -> None:
    """
    Demonstration of the logging utility.
    """
    logger = init_default_logger()
    
    logger.info("Logger initialized successfully")
    
    log_event(
        logger,
        "dialogue_start",
        "Beginning dialogue generation process",
        sample_id="12345",
        dataset="gsm8k"
    )
    
    log_event(
        logger,
        "critique_generated",
        "Critique generated for initial answer",
        critique_length=45,
        has_logical_keywords=True
    )
    
    try:
        # Simulate an error
        raise ValueError("Test error for demonstration")
    except Exception:
        logger.exception("Error occurred during processing")
    
    log_event(
        logger,
        "dialogue_complete",
        "Dialogue generation completed successfully",
        final_score=0.85
    )


if __name__ == "__main__":
    main()