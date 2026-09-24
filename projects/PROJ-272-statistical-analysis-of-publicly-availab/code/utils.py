import logging
import os
import sys
from pathlib import Path
from typing import Optional, Union
from config import get_path, ensure_dirs

_logger_instance = None

def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Set up logging for a specific module/task."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = logging.getLogger("llmXive")
        _logger_instance.setLevel(level)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        _logger_instance.addHandler(ch)
        
        # File handler
        log_path = get_path("data/results/pipeline.log")
        ensure_dirs(log_path)
        fh = logging.FileHandler(log_path)
        fh.setLevel(level)
        fh.setFormatter(formatter)
        _logger_instance.addHandler(fh)
    
    return _logger_instance

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance, initializing logging if necessary."""
    if _logger_instance is None:
        setup_logging(name)
    return logging.getLogger(name)

def normalize_text(text: str) -> str:
    """Normalize text to UTF-8 and handle basic encoding issues."""
    if isinstance(text, bytes):
        text = text.decode('utf-8', errors='ignore')
    return text.strip()

def validate_text_length(text: str, min_words: int = 50) -> bool:
    """Check if text has at least min_words."""
    if not text:
        return False
    words = text.split()
    return len(words) >= min_words
