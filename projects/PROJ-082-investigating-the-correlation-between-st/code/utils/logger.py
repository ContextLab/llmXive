import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import datetime

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        if hasattr(record, "extra_data"):
            log_data["data"] = record.extra_data
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a configured logger instance."""
    logger_name = name or "llmXive"
    logger = logging.getLogger(logger_name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # File handler
    log_dir = Path(__file__).parent.parent.parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_dir / "pipeline.log")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = StructuredFormatter()
    file_handler.setFormatter(file_formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_convergence_warning(logger: logging.Logger, message: str, details: Optional[Dict[str, Any]] = None) -> None:
    """Log a convergence warning with optional details."""
    extra = {"data": details} if details else {}
    logger.warning(message, extra=extra)

def log_fallback(logger: logging.Logger, original_method: str, fallback_method: str, reason: str) -> None:
    """Log a fallback event."""
    details = {
        "original_method": original_method,
        "fallback_method": fallback_method,
        "reason": reason
    }
    logger.warning(f"Falling back from {original_method} to {fallback_method}: {reason}", extra={"data": details})

def log_error_context(logger: logging.Logger, operation: str, error: Exception, context: Optional[Dict[str, Any]] = None) -> None:
    """Log an error with context."""
    details = {"operation": operation, "error_type": type(error).__name__, "error_message": str(error)}
    if context:
        details["context"] = context
    
    logger.error(f"Error during {operation}: {error}", extra={"data": details}, exc_info=True)