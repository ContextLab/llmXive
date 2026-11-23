import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union, Dict, Any
from config import get_path, ensure_dirs

def setup_logging(log_file: Optional[Path] = None) -> logging.Logger:
    """Sets up logging to console and optionally to a file."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    # File handler
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger

def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the given name."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        logger.setLevel(logging.INFO)
    return logger

def normalize_text(text: str) -> str:
    """
    Normalizes text to UTF-8.
    This function handles various encodings and normalizes the text to UTF-8.
    """
    if not text:
        return ""
    try:
        # Try to encode as UTF-8, which will fail if the text is not valid UTF-8
        # and then we can try to decode it from a common encoding like 'latin-1'
        # and re-encode to UTF-8
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        try:
            # If it's not valid UTF-8, try to decode from latin-1 and then encode to UTF-8
            return text.encode('latin-1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            # If all else fails, return the original text
            return text

def validate_text_length(text: str, min_length: int = 50) -> bool:
    """Validates that the text length is at least min_length words."""
    if not text:
        return False
    return len(text.split()) >= min_length

def validate_text_encoding(text: str) -> bool:
    """Validates that the text is valid UTF-8."""
    try:
        text.encode('utf-8')
        return True
    except UnicodeEncodeError:
        return False

def sanitize_text(text: str) -> str:
    """Sanitizes text by removing non-printable characters."""
    if not text:
        return ""
    return ''.join(char for char in text if char.isprintable())

def validate_record(record: Dict[str, Any]) -> bool:
    """Validates a record dictionary."""
    if not record:
        return False
    if 'participant_id' not in record or 'label' not in record or 'text' not in record:
        return False
    if not isinstance(record['participant_id'], (str, int)):
        return False
    if record['label'] is None:
        return False
    if not isinstance(record['text'], str) or len(record['text'].split()) < 50:
        return False
    return True
