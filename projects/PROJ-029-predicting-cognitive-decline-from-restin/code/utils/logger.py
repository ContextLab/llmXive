import logging
import os
from pathlib import Path
from typing import Optional
from config import get_config, ensure_dir

_logger_instance = None

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """Set up a logger with console and file handlers."""
    global _logger_instance
    
    if _logger_instance is None:
        _logger_instance = logging.getLogger("llmXive")
        _logger_instance.setLevel(logging.DEBUG)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        _logger_instance.addHandler(ch)
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if log_file:
        ensure_dir(Path(log_file).parent)
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logger.addHandler(fh)
    
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    """Get or create a logger instance."""
    config = get_config()
    log_dir = Path(config.get('log_dir', 'logs'))
    ensure_dir(log_dir)
    
    # Use a single file for all logs to avoid clutter
    log_file = log_dir / "pipeline.log"
    return setup_logger(name, str(log_file), getattr(logging, config.get('log_level', 'INFO')))

def log_excluded_subjects(subject_id: str, reason: str, logger: Optional[logging.Logger] = None):
    """Log excluded subject details."""
    if logger is None:
        logger = get_logger()
    logger.warning(f"Excluded subject {subject_id}: {reason}")

def log_feature_filtering(feature: str, reason: str, logger: Optional[logging.Logger] = None):
    """Log feature filtering details."""
    if logger is None:
        logger = get_logger()
    logger.info(f"Filtered feature {feature}: {reason}")
