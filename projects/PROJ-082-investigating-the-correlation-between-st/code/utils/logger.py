import logging
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import datetime

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs JSON logs for structured analysis."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        # Include extra context if present
        if hasattr(record, 'context'):
            log_entry["context"] = record.context
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Name of the logger.
        log_file: Optional path to a log file. If provided, logs are written to file.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Ensure directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = StructuredFormatter()
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger

def log_convergence_warning(logger: logging.Logger, message: str) -> None:
    """Log a convergence warning with structured context."""
    logger.warning(f"CONVERGENCE_WARNING: {message}")

def log_fallback(logger: logging.Logger, fallback_reason: str, new_method: str) -> None:
    """Log a fallback event with structured context."""
    logger.warning(f"FALLBACK_TRIGGERED: Reason={fallback_reason}, NewMethod={new_method}")

def log_error_context(logger: logging.Logger, error: Exception, context: Dict[str, Any]) -> None:
    """Log an error with additional context."""
    logger.error(f"ERROR_CONTEXT: {str(error)}", extra={"context": context})

def main() -> None:
    """Test the logger infrastructure."""
    # Ensure data/logs directory exists
    log_path = "data/logs/logger_test.log"
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger = get_logger("test_logger", log_path)
    
    logger.info("Logger initialized successfully")
    logger.warning("This is a test warning")
    
    log_convergence_warning(logger, "Random effects model failed to converge; switching to fixed effects.")
    log_fallback(logger, "Convergence failure", "Fixed Effects Model")
    log_error_context(logger, ValueError("Invalid input"), {"study_id": "STUDY_001", "value": None})
    
    print(f"Logs written to {log_path}")

if __name__ == "__main__":
    main()