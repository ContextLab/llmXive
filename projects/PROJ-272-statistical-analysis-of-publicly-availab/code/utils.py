import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union

from config import get_path, ensure_dirs

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """
    Setup logging infrastructure.
    
    Args:
        log_level (int): Logging level (e.g., logging.INFO).
        
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger("llmXive")
    logger.setLevel(log_level)
    
    if not logger.handlers:
        # File handler
        log_dir = get_path("logs")
        ensure_dirs(log_dir)
        log_file = os.path.join(log_dir, "pipeline.log")
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name (Optional[str]): Logger name. If None, returns the root logger.
        
    Returns:
        logging.Logger: Logger instance.
    """
    base_logger = setup_logging()
    if name:
        return base_logger.getChild(name)
    return base_logger

def normalize_text(text: str) -> str:
    """
    Normalize text to UTF-8 and handle encoding issues.
    
    Args:
        text (str): Input text.
        
    Returns:
        str: Normalized text.
    """
    if not text:
        return ""
    
    # If text is bytes, decode to UTF-8
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    
    # Normalize Unicode characters (NFKC normalization)
    import unicodedata
    text = unicodedata.normalize('NFKC', text)
    
    return text

def validate_text_length(text: str, min_length: int = 50, unit: str = "w") -> Tuple[bool, int]:
    """
    Validate text length.
    
    Args:
        text (str): Input text.
        min_length (int): Minimum required length.
        unit (str): Unit of measurement ('w' for words, 'c' for characters).
        
    Returns:
        Tuple[bool, int]: (is_valid, actual_length)
    """
    if not text:
        return False, 0
    
    if unit == "w":
        # Count words (split by whitespace)
        length = len(text.split())
    elif unit == "c":
        # Count characters
        length = len(text)
    else:
        raise ValueError(f"Invalid unit '{unit}'. Use 'w' for words or 'c' for characters.")
    
    return length >= min_length, length
