import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

def setup_logging(level=logging.INFO) -> logging.Logger:
    logger = logging.getLogger("llmXive")
    logger.setLevel(level)
    
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def log_data_ingestion_step(step_name: str, count: int):
    logger = get_logger(__name__)
    logger.info(f"Data ingestion step '{step_name}': {count} items processed")

def log_coverage_audit_result(p_value: float):
    logger = get_logger(__name__)
    logger.info(f"Coverage audit p-value: {p_value}")
