"""
Logging infrastructure for the project.
"""
import logging
import sys
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any

def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logger."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(name)

class ContextLogRecord(logging.LogRecord):
    """Log record with additional context."""
    def __init__(self, name, level, pathname, lineno, msg, args, exc_info, func=None, sinfo=None, **kwargs):
        super().__init__(name, level, pathname, lineno, msg, args, exc_info, func, sinfo)
        self.context = kwargs.get('context', {})

def log_error_to_file(error_msg: str, path: str):
    """Log error message to a specific file."""
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f"{error_msg}\n")

def log_execution_failure(task_id: str, error: Exception, path: str):
    """Log execution failure details."""
    log_entry = {
        "task_id": task_id,
        "error_type": type(error).__name__,
        "error_message": str(error),
        "status": "failed"
    }
    with open(path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry) + "\n")
