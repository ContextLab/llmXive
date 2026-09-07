"""
Custom logging handler for llmXive research pipeline.
Captures specific research metrics (reward_fidelity_level, recovery_segment_id)
and formats them for structured analysis.
"""
import logging
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path

class ResearchLogFormatter(logging.Formatter):
    """
    Custom formatter that appends research-specific metadata to log records.
    Ensures fields like `reward_fidelity_level` and `recovery_segment_id`
    are present in the output, even if set via `extra`.
    """
    
    def __init__(self, fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"):
        super().__init__(fmt)
    
    def format(self, record: logging.LogRecord) -> str:
        # Ensure standard attributes exist
        if not hasattr(record, 'reward_fidelity_level'):
            record.reward_fidelity_level = "N/A"
        if not hasattr(record, 'recovery_segment_id'):
            record.recovery_segment_id = "N/A"
        if not hasattr(record, 'task_id'):
            record.task_id = "N/A"
        
        # Prepend custom fields to the message for easy parsing
        custom_info = f" [reward_fidelity_level={record.reward_fidelity_level}] [recovery_segment_id={record.recovery_segment_id}]"
        
        # Append to the base message
        if isinstance(record.msg, str):
            record.msg = record.msg + custom_info
        
        return super().format(record)

class StructuredResearchHandler(logging.Handler):
    """
    A handler that writes structured JSON lines for research metrics,
    while also passing the formatted string to the base stream/file.
    Useful for programmatic parsing of specific research variables.
    """
    def __init__(self, stream):
        super().__init__()
        self.stream = stream
    
    def emit(self, record: logging.LogRecord):
        try:
            log_data = {
                "timestamp": self.formatTime(record, self.datefmt),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "metrics": {
                    "reward_fidelity_level": getattr(record, 'reward_fidelity_level', "N/A"),
                    "recovery_segment_id": getattr(record, 'recovery_segment_id', "N/A"),
                    "task_id": getattr(record, 'task_id', "N/A"),
                    "model_name": getattr(record, 'model_name', "N/A")
                }
            }
            self.stream.write(json.dumps(log_data) + "\n")
            self.flush()
        except Exception:
            self.handleError(record)

def setup_logger(
    name: str = "llmxive",
    log_file: str = "logs/run.log",
    level: int = logging.INFO,
    config_path: str = "code/config.yaml"
) -> logging.Logger:
    """
    Initializes the project logger with both standard and structured handlers.
    Reads configuration from config.yaml if available, otherwise uses defaults.
    
    Args:
        name: Logger name
        log_file: Path to the log file relative to project root
        level: Logging level
        config_path: Path to config file (optional)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # File Handler
    file_handler = logging.FileHandler(log_file, mode='a')
    file_handler.setLevel(level)
    file_handler.setFormatter(ResearchLogFormatter())
    
    # Structured Handler (for metric extraction)
    structured_handler = StructuredResearchHandler(open(log_file, 'a'))
    structured_handler.setLevel(level)
    structured_handler.setFormatter(logging.Formatter('%(message)s')) # JSON is self-contained
    
    logger.addHandler(file_handler)
    logger.addHandler(structured_handler)
    
    return logger

def log_metric(
    logger: logging.Logger,
    message: str,
    reward_fidelity_level: Optional[str] = None,
    recovery_segment_id: Optional[str] = None,
    task_id: Optional[str] = None,
    model_name: Optional[str] = None,
    level: int = logging.INFO
) -> None:
    """
    Helper function to log a message with specific research metrics.
    
    Args:
        logger: Logger instance
        message: Log message
        reward_fidelity_level: The fidelity level (e.g., 'dense', 'binary')
        recovery_segment_id: The ID of the recovery segment
        task_id: The task identifier
        model_name: The model used
        level: Log level
    """
    logger.log(
        level,
        message,
        extra={
            'reward_fidelity_level': reward_fidelity_level or "N/A",
            'recovery_segment_id': recovery_segment_id or "N/A",
            'task_id': task_id or "N/A",
            'model_name': model_name or "N/A"
        }
    )
