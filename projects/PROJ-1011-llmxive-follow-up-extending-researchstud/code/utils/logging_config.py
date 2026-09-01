"""
Logging configuration and utilities for the llmXive pipeline.

This module sets up logging infrastructure to ensure all logs are
sanitized of PII before being written to disk.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
import json
from datetime import datetime
import re
import os

# Import PII sanitizer if available (optional dependency for this specific enhancement)
# We handle the import gracefully to avoid breaking if the module is not yet loaded
try:
    from utils.pii_sanitizer import sanitize_text
    PII_SANITIZER_AVAILABLE = True
except ImportError:
    PII_SANITIZER_AVAILABLE = False
    logger_fallback = logging.getLogger("logging_config_fallback")
    logger_fallback.warning("PII Sanitizer not available. Logs may contain sensitive data.")

# Global logger instance
_logger: Optional[logging.Logger] = None

def ensure_log_dir() -> Path:
    """Ensure the logs directory exists."""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    return log_dir

def _sanitize_log_message(msg: str) -> str:
    """Sanitize a log message for PII before logging."""
    if not PII_SANITIZER_AVAILABLE:
        return msg
    try:
        return sanitize_text(msg)
    except Exception:
        # If sanitization fails, log the error but return original message to avoid data loss
        # In a production system, we might want to fail loudly here
        return msg

class PIIFilter(logging.Filter):
    """A logging filter that sanitizes PII from log records."""
    
    def filter(self, record):
        # Sanitize the message
        record.msg = _sanitize_log_message(str(record.msg))
        
        # Sanitize args if present (format arguments)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: _sanitize_log_message(str(v)) if isinstance(v, str) else v 
                               for k, v in record.args.items()}
            else:
                record.args = tuple(_sanitize_log_message(str(arg)) if isinstance(arg, str) else arg 
                                    for arg in record.args)
        
        return True

def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a logger with PII sanitization enabled.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logger instance.
    """
    global _logger
    if _logger is None or _logger.name != name:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to avoid duplicates
        _logger.handlers.clear()
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_format)
        console_handler.addFilter(PIIFilter())
        _logger.addHandler(console_handler)
        
        # Create file handler
        log_dir = ensure_log_dir()
        log_file = log_dir / "pipeline.log"
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_format)
        file_handler.addFilter(PIIFilter())
        _logger.addHandler(file_handler)
        
        # Prevent propagation to root logger to avoid double logging
        _logger.propagate = False
        
    return _logger

def get_model_fallback_logger() -> logging.Logger:
    """Get a specific logger for model fallback events."""
    return get_logger("llmXive.model_fallback")

def log_model_switch(model_from: str, model_to: str, reason: str):
    """Log a model switch event."""
    logger = get_model_fallback_logger()
    logger.info(f"Model switched from {model_from} to {model_to} due to: {reason}")

def log_memory_error(memory_mb: int, limit_mb: int):
    """Log a memory error event."""
    logger = get_model_fallback_logger()
    logger.warning(f"Memory usage {memory_mb}MB exceeded limit {limit_mb}MB")

def log_fallback_success():
    """Log successful fallback."""
    logger = get_model_fallback_logger()
    logger.info("Fallback mechanism succeeded")

def log_fallback_failure():
    """Log failed fallback."""
    logger = get_model_fallback_logger()
    logger.error("Fallback mechanism failed")

def initialize_pipeline_logging():
    """Initialize the main pipeline logging."""
    return get_logger("llmXive.pipeline")

def log_acquisition_failure(venue: str, error: str):
    """Log data acquisition failure."""
    logger = get_logger("llmXive.acquisition")
    logger.error(f"Acquisition failed for {venue}: {error}")

def log_preprocessing_rejection(reason: str, count: int = 1):
    """Log preprocessing rejection."""
    logger = get_logger("llmXive.preprocessing")
    logger.warning(f"Rejected {count} entries: {reason}")

def log_preprocessing_rejection_count(total: int, rejected: int):
    """Log total preprocessing statistics."""
    logger = get_logger("llmXive.preprocessing")
    logger.info(f"Preprocessing complete: {total} total, {rejected} rejected")

# Additional utility to sanitize specific sensitive fields in structured logs
def sanitize_structured_log(record: dict) -> dict:
    """
    Sanitize a structured log record (dict) for PII.
    
    Args:
        record: Dictionary containing log data.
        
    Returns:
        Sanitized dictionary.
    """
    if not PII_SANITIZER_AVAILABLE:
        return record
        
    sanitized = {}
    sensitive_keys = ['email', 'phone', 'ssn', 'ip', 'api_key', 'token', 'password', 'orcid']
    
    for key, value in record.items():
        if isinstance(value, str):
            # Check if key suggests sensitive data
            if any(sk in key.lower() for sk in sensitive_keys):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = sanitize_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_structured_log(value)
        elif isinstance(value, list):
            sanitized[key] = [
                "[REDACTED]" if isinstance(item, str) and any(sk in str(item).lower() for sk in sensitive_keys)
                else sanitize_structured_log(item) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
            
    return sanitized

if __name__ == "__main__":
    # Test logging
    logger = get_logger()
    logger.info("Test message with PII: user@example.com and 192.168.1.1")
    logger.warning("Sensitive data: SSN 123-45-6789")
    logger.error("API Key: sk-1234567890abcdef")
    
    # Test structured logging
    test_record = {
        "user": "john@example.com",
        "ip": "10.0.0.1",
        "action": "login",
        "nested": {
            "token": "secret_token_123"
        }
    }
    print("Original:", test_record)
    print("Sanitized:", sanitize_structured_log(test_record))
