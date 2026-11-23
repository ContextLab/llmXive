import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with structured formatting.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Create console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    
    # Create formatter
    formatter = StructuredFormatter()
    ch.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(ch)
    
    return logger

def log_convergence_warning(logger: logging.Logger, message: str):
    """Log a convergence warning."""
    logger.warning(f"CONVERGENCE WARNING: {message}")

def log_fallback(logger: logging.Logger, message: str):
    """Log a fallback event."""
    logger.warning(f"FALLBACK: {message}")

def log_error_context(logger: logging.Logger, message: str, exc_info: Optional[Exception] = None):
    """Log an error with context."""
    if exc_info:
        logger.error(f"ERROR: {message}", exc_info=True)
    else:
        logger.error(f"ERROR: {message}")

def main():
    """
    Entry point for script execution.
    """
    logger = get_logger("test_logger")
    logger.info("Test info message")
    logger.warning("Test warning message")
    logger.error("Test error message")

if __name__ == "__main__":
    main()
