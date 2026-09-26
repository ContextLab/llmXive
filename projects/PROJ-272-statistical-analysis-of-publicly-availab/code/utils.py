import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from config import get_path, ensure_dirs

_logger_instance = None

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging infrastructure for the project.
    
    Configures both a console handler and a file handler.
    Ensures the log directory exists before creating the file handler.
    
    Args:
        name: The name of the logger (usually __name__).
        level: The logging level (e.g., logging.INFO, logging.DEBUG).
    
    Returns:
        A configured logger instance.
    """
    global _logger_instance
    
    # Initialize the root logger for the project only once
    if _logger_instance is None:
        _logger_instance = logging.getLogger("llmXive")
        _logger_instance.setLevel(level)
        
        # Avoid adding handlers if they already exist (idempotency)
        if _logger_instance.handlers:
            return _logger_instance
        
        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        ch.setFormatter(console_formatter)
        _logger_instance.addHandler(ch)
        
        # File handler
        try:
            log_path = get_path("data/results/pipeline.log")
            ensure_dirs(log_path)
            fh = logging.FileHandler(log_path, encoding='utf-8')
            fh.setLevel(level)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
            )
            fh.setFormatter(file_formatter)
            _logger_instance.addHandler(fh)
        except Exception as e:
            # If file logging fails, ensure we still have console logging
            print(f"Warning: Failed to set up file logging: {e}", file=sys.stderr)
    
    return _logger_instance

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Ensures logging is set up before returning the logger.
    
    Args:
        name: The name of the logger (usually __name__).
    
    Returns:
        A logger instance configured with the project's handlers.
    """
    if _logger_instance is None:
        setup_logging(name)
    return logging.getLogger(name)

def normalize_text(text: Union[str, bytes]) -> str:
    """
    Normalize text to UTF-8 string.
    
    Handles bytes input by decoding, and strips whitespace from strings.
    
    Args:
        text: The text to normalize (string or bytes).
    
    Returns:
        A normalized UTF-8 string.
    """
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    if not isinstance(text, str):
        return str(text)
    return text.strip()

def validate_text_length(text: str, min_words: int = 50) -> bool:
    """
    Check if text has at least min_words.
    
    Args:
        text: The text to validate.
        min_words: The minimum number of words required.
    
    Returns:
        True if the text has at least min_words, False otherwise.
    """
    if not text:
        return False
    words = text.split()
    return len(words) >= min_words

def validate_text_encoding(text: Union[str, bytes]) -> bool:
    """
    Validate that text can be encoded/decoded as UTF-8 without errors.
    
    Args:
        text: The text to validate.
    
    Returns:
        True if valid UTF-8, False otherwise.
    """
    try:
        if isinstance(text, bytes):
            text.decode('utf-8')
        else:
            text.encode('utf-8')
        return True
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False

def sanitize_text(text: str) -> str:
    """
    Remove non-printable characters and normalize whitespace.
    
    Args:
        text: The text to sanitize.
    
    Returns:
        Sanitized text string.
    """
    if not text:
        return ""
    
    # Remove non-printable characters (control characters except tab, newline, carriage return)
    sanitized = ''.join(char for char in text if char.isprintable() or char in '\t\n\r')
    
    # Normalize whitespace (replace multiple spaces/newlines with single)
    while '  ' in sanitized or '\n\n' in sanitized:
        sanitized = sanitized.replace('  ', ' ').replace('\n\n', '\n')
    
    return sanitized.strip()

def validate_record(record: dict, required_fields: list, min_text_length: int = 50) -> tuple:
    """
    Validate a data record for required fields and text quality.
    
    Args:
        record: The dictionary representing a data record.
        required_fields: List of field names that must be present and non-null.
        min_text_length: Minimum word count for text field validation.
    
    Returns:
        Tuple of (is_valid: bool, reason: Optional[str])
    """
    if not isinstance(record, dict):
        return False, "Record is not a dictionary"
    
    # Check required fields
    for field in required_fields:
        if field not in record:
            return False, f"Missing required field: {field}"
        if record[field] is None:
            return False, f"Null value in required field: {field}"
    
    # Validate text field if present
    if 'text' in record and 'participant_id' in record:
        text = record.get('text', '')
        if isinstance(text, bytes):
            try:
                text = text.decode('utf-8', errors='ignore')
            except Exception:
                return False, "Invalid text encoding"
        
        if not isinstance(text, str):
            return False, "Text field is not a string"
        
        if len(text.split()) < min_text_length:
            return False, f"Text too short: {len(text.split())} words (min: {min_text_length})"
    
    return True, None