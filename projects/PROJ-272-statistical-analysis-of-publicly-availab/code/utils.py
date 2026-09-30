"""
code/utils.py
Utility functions for logging, text normalization, and validation.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from config import get_path, ensure_dirs

def setup_logging(log_file: Optional[Path] = None) -> None:
    """
    Sets up logging configuration.
    """
    log_level = os.environ.get('LOG_LEVEL', 'INFO')
    format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        ensure_dirs(log_file)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format=format_str,
        handlers=handlers
    )

def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger instance.
    """
    return logging.getLogger(name)

def normalize_text(text: str) -> str:
    """
    Normalizes text to UTF-8.
    """
    if not isinstance(text, str):
        return ""
    return text.encode('utf-8').decode('utf-8', errors='ignore')

def validate_text_length(text: str, min_words: int = 50) -> bool:
    """
    Validates if text meets minimum word count.
    """
    if not isinstance(text, str):
        return False
    words = len(text.split())
    return words >= min_words

def validate_text_encoding(text: str) -> bool:
    """
    Validates text encoding.
    """
    try:
        text.encode('utf-8')
        return True
    except UnicodeEncodeError:
        return False

def sanitize_text(text: str) -> str:
    """
    Sanitizes text by removing non-printable characters.
    """
    if not isinstance(text, str):
        return ""
    return ''.join(char for char in text if char.isprintable() or char in '\n\r\t')

def validate_record(record: Dict) -> bool:
    """
    Validates a record for required fields.
    """
    required = ['participant_id', 'label', 'text']
    return all(k in record and record[k] is not None for k in required)
