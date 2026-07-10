"""
Logging Configuration Module.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(level)
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

def log_missing_geometric_data(message: str):
    logger = get_logger("data.descriptors")
    logger.warning(f"Missing Geometric Data: {message}")

def log_metallic_outlier(count: int):
    logger = get_logger("data.descriptors")
    logger.warning(f"Detected {count} metallic outliers (zero/negative band gap).")

def log_feature_extraction_error(message: str):
    logger = get_logger("data.descriptors")
    logger.error(f"Feature Extraction Error: {message}")