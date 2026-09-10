"""
Custom logging handler for llmXive research pipeline.
Provides structured logging for research metrics like reward_fidelity_level
and recovery_segment_id.
"""
import logging
import os
import json
from typing import Optional, Dict, Any
from pathlib import Path
import yaml

class ResearchLogFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON for research metrics."""
    
    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super().__init__(fmt, datefmt)
        self.metric_keys = {
            'reward_fidelity_level',
            'recovery_segment_id',
            'task_id',
            'success_status',
            'token_count'
        }

    def format(self, record: logging.LogRecord) -> str:
        # Check if this record contains research metrics
        has_metrics = any(hasattr(record, key) for key in self.metric_keys)
        
        if has_metrics:
            # Create a structured JSON log entry
            log_entry = {
                'timestamp': self.formatTime(record, self.datefmt),
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
            }
            
            # Add any metric attributes present
            for key in self.metric_keys:
                if hasattr(record, key):
                    log_entry[key] = getattr(record, key)
            
            return json.dumps(log_entry)
        else:
            return super().format(record)

class StructuredResearchHandler(logging.Handler):
    """Handler that captures and formats research-specific metrics."""
    
    def __init__(self, log_path: str):
        super().__init__()
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Set formatter
        self.setFormatter(ResearchLogFormatter())

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(msg + '\n')
        except Exception:
            self.handleError(record)

def setup_logger(
    name: str = "llmXive",
    log_file: str = "logs/run.log",
    level: int = logging.INFO,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup a research logger with both file and console handlers.
    
    Args:
        name: Logger name
        log_file: Path to the log file
        level: Logging level
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler for structured research logs
    file_handler = StructuredResearchHandler(log_file)
    file_handler.setLevel(level)
    logger.addHandler(file_handler)

    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logger.addHandler(console_handler)

    return logger

def log_metric(
    logger: logging.Logger,
    message: str,
    **kwargs: Any
) -> None:
    """
    Log a research metric with key-value pairs.
    
    Args:
        logger: Logger instance
        message: Log message
        **kwargs: Metric key-value pairs (e.g., reward_fidelity_level='dense')
    """
    # Create a log record with custom attributes
    record = logger.makeRecord(
        logger.name,
        logging.INFO,
        "",
        0,
        message,
        (),
        None
    )
    
    # Attach metric attributes to the record
    for key, value in kwargs.items():
        setattr(record, key, value)
    
    logger.handle(record)

def load_config(config_path: str = "code/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
