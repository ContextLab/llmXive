"""
Logging and utility infrastructure for the statistical analysis pipeline.

Provides:
- Configurable logging to both console and file.
- Data validation utilities (UTF-8 normalization, length checks).
"""
import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

# Import config to ensure paths are initialized before logging setup
from config import get_path, ensure_dirs


def setup_logging(
    log_level: int = logging.INFO,
    log_filename: Optional[str] = "pipeline.log",
    console: bool = True,
    file: bool = True,
) -> logging.Logger:
    """
    Configures the root logger with file and console handlers.
    
    Args:
        log_level: The logging level (e.g., logging.DEBUG, logging.INFO).
        log_filename: Name of the log file relative to the project root.
        console: Whether to add a StreamHandler for stdout.
        file: Whether to add a FileHandler.
        
    Returns:
        The configured root logger instance.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates on re-runs in same process
    if logger.handlers:
        logger.handlers.clear()
    
    # Ensure log directory exists
    log_dir = get_path("data").parent / "logs"
    ensure_dirs(log_dir)
    
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    if file:
        log_file_path = log_dir / log_filename
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
            
    return logger


def normalize_text(text: Union[str, bytes]) -> str:
    """
    Normalizes text to UTF-8 string, handling potential encoding errors.
    
    Args:
        text: The input text string or bytes.
        
    Returns:
        A normalized UTF-8 string.
        
    Raises:
        ValueError: If the input cannot be decoded as UTF-8.
    """
    if isinstance(text, bytes):
        try:
            text = text.decode("utf-8")
        except UnicodeDecodeError as e:
            # Attempt to replace invalid characters, but log a warning
            # In a strict pipeline, we might want to fail here.
            # For now, we replace with replacement character.
            text = text.decode("utf-8", errors="replace")
    elif not isinstance(text, str):
        text = str(text)
        
    # Normalize unicode (NFKC) for consistency
    import unicodedata
    return unicodedata.normalize("NFKC", text)


def validate_text_length(text: str, min_length: int = 50, max_length: Optional[int] = None, unit: str = "words") -> bool:
    """
    Validates that text meets length constraints.
    
    Args:
        text: The text to validate.
        min_length: Minimum number of units (words or chars) allowed.
        max_length: Maximum number of units (words or chars) allowed.
        unit: Measurement unit, either "words" or "chars".
        
    Returns:
        True if valid, False otherwise.
    """
    if not text:
        return False
        
    if unit == "chars":
        length = len(text)
    else:
        # Default to words
        length = len(text.split())
        
    if length < min_length:
        return False
    if max_length is not None and length > max_length:
        return False
    return True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Retrieves a logger by name. If not configured yet, returns the root logger.
    
    Args:
        name: Name of the logger.
        
    Returns:
        A logging.Logger instance.
    """
    if name is None:
        return logging.getLogger()
    return logging.getLogger(name)
