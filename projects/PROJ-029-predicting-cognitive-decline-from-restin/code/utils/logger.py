"""
Logging utilities.
"""
import logging
import os
from pathlib import Path
from typing import Optional
from config import get_config, ensure_dir

def setup_logger(name: str, log_file: Optional[Path] = None, level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File handler if specified
        if log_file:
            ensure_dir(log_file.parent)
            fh = logging.FileHandler(log_file)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
    
    return logger

def get_logger(name: str = "llmXive") -> logging.Logger:
    return setup_logger(name)

def log_excluded_subjects(log_file: Path, subject_id: str, reason: str) -> None:
    ensure_dir(log_file.parent)
    with open(log_file, 'a') as f:
        f.write(f"{subject_id}: {reason}\n")

def log_feature_filtering(log_file: Path, feature: str, reason: str) -> None:
    ensure_dir(log_file.parent)
    with open(log_file, 'a') as f:
        f.write(f"Feature {feature} filtered: {reason}\n")
