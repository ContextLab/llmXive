"""
Logging utilities for the project.
"""
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as JSON lines.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance configured for the project.
    
    If no name is provided, uses the default project logger.
    Outputs to both console and a file in data/results/ if the directory exists.
    """
    logger_name = name or "llmXive"
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional, if data/results exists)
    log_dir = Path("data/results")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"app_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    json_formatter = JSONFormatter()
    file_handler.setFormatter(json_formatter)
    logger.addHandler(file_handler)
    
    return logger

def log_result(logger: logging.Logger, result: dict, message: str = "Result") -> None:
    """
    Helper to log a dictionary result as a JSON string.
    """
    logger.info(f"{message}: {json.dumps(result)}")
