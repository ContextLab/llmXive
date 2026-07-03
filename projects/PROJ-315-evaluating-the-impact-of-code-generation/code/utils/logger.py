"""
Logging utilities for the research pipeline.

Provides structured logging, error reporting, and specific loggers for
validation failures (Completeness, Power Insufficiency).
"""
import logging
import sys
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

class ResearchFormatter(logging.Formatter):
    """Custom formatter for research logs with timestamps and levels."""
    def format(self, record):
        log_fmt = f"[{datetime.now().isoformat()}] [{record.levelname}] {record.name}: {record.msg}"
        return log_fmt

def get_logger(name: str = "research") -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name.
        
    Returns:
        Configured logging.Logger.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(ResearchFormatter())
    logger.addHandler(ch)
    
    # File handler (optional, directed to logs/research.log)
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    fh = logging.FileHandler(logs_dir / "research.log")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(ResearchFormatter())
    logger.addHandler(fh)
    
    return logger

def log_data_completeness(completeness: float, threshold: float) -> None:
    """Log data completeness check result."""
    logger = get_logger("validation.completeness")
    status = "PASS" if completeness >= threshold else "FAIL"
    logger.info(f"Data Completeness: {completeness:.4f} (Threshold: {threshold:.4f}) - {status}")

def log_power_insufficiency(llm_count: int, non_llm_count: int, min_required: int) -> None:
    """
    Log power insufficiency failure.
    
    Args:
        llm_count: Number of LLM-generated samples.
        non_llm_count: Number of non-LLM samples.
        min_required: Minimum required per group.
    """
    logger = get_logger("validation.power")
    msg = (f"POWER INSUFFICIENCY DETECTED. "
           f"LLM Count: {llm_count}, Non-LLM Count: {non_llm_count}. "
           f"Required: >= {min_required} per group.")
    logger.error(msg)

def log_validation_error(message: str) -> None:
    """Log a generic validation error."""
    logger = get_logger("validation.error")
    logger.error(f"VALIDATION ERROR: {message}")

def log_analysis_result(result_type: str, data: Dict[str, Any]) -> None:
    """Log analysis results in a structured way."""
    logger = get_logger("analysis.results")
    logger.info(f"Analysis Result [{result_type}]: {json.dumps(data, indent=2)}")
