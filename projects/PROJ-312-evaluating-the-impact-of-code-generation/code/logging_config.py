import json
import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

def setup_logging(log_file: str = "logs/pipeline.log") -> logging.Logger:
    """Configure logging with file and console handlers."""
    logger = logging.getLogger("llmXive")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name."""
    return logging.getLogger(name)

def capture_rate_limit_headers(headers: Dict[str, str]) -> Dict[str, Any]:
    """Capture and log rate limit headers."""
    return {
        "X-RateLimit-Remaining": headers.get("X-RateLimit-Remaining"),
        "X-RateLimit-Reset": headers.get("X-RateLimit-Reset")
    }
