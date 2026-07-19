import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import json
import datetime

class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs as structured JSON.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry)

def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get or create a logger with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        log_file: Optional path to write logs to
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(StructuredFormatter())
    logger.addHandler(console_handler)
    
    # File handler if log_file is provided
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)
    
    return logger

def log_convergence_warning(logger: logging.Logger, message: str, details: Optional[Dict[str, Any]] = None):
    """
    Log a convergence warning with optional details.
    
    Args:
        logger: Logger instance
        message: Warning message
        details: Optional dictionary of additional details
    """
    warning_data = {
        "type": "convergence_warning",
        "message": message
    }
    if details:
        warning_data["details"] = details
    
    logger.warning(json.dumps(warning_data))

def log_fallback(logger: logging.Logger, fallback_type: str, reason: str, original_attempt: Optional[str] = None):
    """
    Log a fallback event when a primary method fails and a fallback is used.
    
    Args:
        logger: Logger instance
        fallback_type: Type of fallback (e.g., "Fixed-Effects", "NLP extraction")
        reason: Reason for fallback
        original_attempt: Description of the original attempt that failed
    """
    fallback_data = {
        "type": "fallback",
        "fallback_type": fallback_type,
        "reason": reason,
        "original_attempt": original_attempt
    }
    
    logger.warning(json.dumps(fallback_data))

def log_error_context(logger: logging.Logger, context: str, error: Exception):
    """
    Log an error with context information.
    
    Args:
        logger: Logger instance
        context: Contextual information about the error
        error: The exception that occurred
    """
    error_data = {
        "type": "error",
        "context": context,
        "error_type": type(error).__name__,
        "error_message": str(error)
    }
    
    logger.error(json.dumps(error_data))

def main():
    """
    Main entry point for testing the logger infrastructure.
    Demonstrates structured logging for convergence warnings and fallbacks.
    """
    from utils.config import get_project_root, ensure_directory
    
    project_root = get_project_root()
    log_dir = project_root / "data" / "logs"
    ensure_directory(log_dir)
    
    log_file = log_dir / "pipeline.log"
    logger = get_logger("llmXive_pipeline", log_file)
    
    # Demonstrate convergence warning
    log_convergence_warning(
        logger, 
        "Random-effects model failed to converge", 
        {"iteration": 42, "tolerance": 1e-6}
    )
    
    # Demonstrate fallback logging
    log_fallback(
        logger, 
        "Fixed-Effects", 
        "Convergence failure in Random-effects model",
        "REML optimization did not converge within 100 iterations"
    )
    
    # Demonstrate error context logging
    try:
        raise ValueError("Simulated extraction error")
    except Exception as e:
        log_error_context(logger, "Data extraction phase", e)
    
    logger.info("Logger infrastructure test completed successfully.")
    print(f"Logs written to: {log_file}")

if __name__ == "__main__":
    main()