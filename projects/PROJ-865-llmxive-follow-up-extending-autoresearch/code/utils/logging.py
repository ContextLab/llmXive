import logging
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

def log_stage_start(stage_name: str, input_path: str, output_path: str):
    """Log the start of a pipeline stage."""
    logger = get_logger(stage_name)
    logger.info(f"--- Stage Start: {stage_name} ---")
    logger.info(f"Input: {input_path}")
    logger.info(f"Output: {output_path}")
    logger.info(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")

def log_stage_end(stage_name: str, success: bool):
    """Log the end of a pipeline stage."""
    logger = get_logger(stage_name)
    status = "SUCCESS" if success else "FAILURE"
    logger.info(f"--- Stage End: {stage_name} - {status} ---")

def log_resource_usage():
    """Log current resource usage."""
    logger = get_logger("resource_monitor")
    try:
        import psutil
        process = psutil.Process()
        mem = process.memory_info().rss / 1024 / 1024
        logger.info(f"Current Memory Usage: {mem:.2f} MB")
    except ImportError:
        logger.warning("psutil not installed, skipping resource log.")
