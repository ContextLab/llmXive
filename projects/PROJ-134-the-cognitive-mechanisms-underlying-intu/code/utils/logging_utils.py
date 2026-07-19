"""
Logging infrastructure for the llmXive project.

Provides configured loggers and helper functions to capture exclusion reasons,
VR mapping logs, and general pipeline steps to the data/logs directory.
"""
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List
import json
import csv

from code.config import get_path


# Ensure the log directory exists
LOG_DIR = Path(get_path("data/logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Format for console and file logs
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Cache for loggers to avoid re-configuration
_loggers: Dict[str, logging.Logger] = {}


def get_logger(name: str = "llmXive") -> logging.Logger:
    """
    Get or create a logger with the specified name, configured to write to file and console.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A configured logging.Logger instance.
    """
    if name in _loggers:
        return _loggers[name]
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid adding handlers if they already exist (for re-runs in same process)
    if not logger.handlers:
        # File Handler
        file_handler = logging.FileHandler(
            LOG_DIR / f"{name.lower().replace('.', '_')}.log"
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    _loggers[name] = logger
    return logger


def get_log_path(filename: str) -> Path:
    """
    Get the full path for a log file in the data/logs directory.
    
    Args:
        filename: The name of the log file.
        
    Returns:
        A Path object pointing to the log file.
    """
    return LOG_DIR / filename


def get_exclusion_log_path() -> Path:
    """
    Get the path for the exclusion log file.
    
    Returns:
        Path to data/logs/exclusion.log
    """
    return get_log_path("exclusion.log")


def get_vr_mapping_log_path() -> Path:
    """
    Get the path for the VR mapping log file.
    
    Returns:
        Path to data/logs/vr_mapping.log
    """
    return get_log_path("vr_mapping.log")


def log_exclusion(reason: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exclusion reason to the exclusion log file.
    
    Args:
        reason: A string describing the reason for exclusion.
        details: Optional dictionary of additional details.
    """
    logger = get_logger("exclusion")
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "reason": reason,
        "details": details or {}
    }
    
    log_msg = json.dumps(log_entry)
    logger.warning(log_msg)
    
    # Also append to a dedicated exclusion.log for easy parsing
    exclusion_path = get_exclusion_log_path()
    with open(exclusion_path, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


def log_vr_mapping(story_id: str, salience_level: str, blend_shape_params: Dict[str, Any]) -> None:
    """
    Log VR mapping details to the VR mapping log file.
    
    Args:
        story_id: The identifier of the story.
        salience_level: The assigned salience level ('low' or 'high').
        blend_shape_params: The dictionary of blend shape parameters used.
    """
    logger = get_logger("vr_mapping")
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "story_id": story_id,
        "salience_level": salience_level,
        "blend_shape_params": blend_shape_params
    }
    
    log_msg = json.dumps(log_entry)
    logger.info(log_msg)
    
    # Append to dedicated VR mapping log
    mapping_path = get_vr_mapping_log_path()
    with open(mapping_path, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")


def log_pipeline_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a general pipeline step execution.
    
    Args:
        step_name: The name of the pipeline step.
        status: The status of the step (e.g., 'STARTED', 'COMPLETED', 'FAILED').
        details: Optional dictionary of additional details.
    """
    logger = get_logger("pipeline")
    timestamp = datetime.now().isoformat()
    
    log_entry = {
        "timestamp": timestamp,
        "step": step_name,
        "status": status,
        "details": details or {}
    }
    
    log_msg = json.dumps(log_entry)
    
    if status == "FAILED":
        logger.error(log_msg)
    elif status == "COMPLETED":
        logger.info(log_msg)
    else:
        logger.debug(log_msg)