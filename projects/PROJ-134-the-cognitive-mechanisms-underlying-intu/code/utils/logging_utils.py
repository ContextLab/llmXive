"""
Logging utilities for the research pipeline.

Provides functions to get loggers, log exclusions, and log VR mapping data.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List
import json

from config import ensure_directories

# Constants
LOGS_DIR = Path("data/logs")

def get_log_path(log_type: str) -> Path:
    """
    Get the path for a specific log file.
    
    Args:
        log_type: Type of log (e.g., 'exclusion', 'pipeline').
        
    Returns:
        Path: The path to the log file.
    """
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d")
    return LOGS_DIR / f"{log_type}_{timestamp}.log"

def get_exclusion_log_path() -> Path:
    """Get path for exclusion log."""
    return get_log_path("exclusion")

def get_vr_mapping_log_path() -> Path:
    """Get path for VR mapping log."""
    return get_log_path("vr_mapping")

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance configured for the project.
    
    Args:
        name: Name of the logger.
        
    Returns:
        logging.Logger: Configured logger.
    """
    ensure_directories()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        # File handler
        fh = logging.FileHandler(LOGS_DIR / f"{name}.log")
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger

def log_exclusion(reason: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exclusion reason to the exclusion log file.
    
    Args:
        reason: The reason for exclusion.
        details: Optional dictionary of additional details.
    """
    ensure_directories()
    log_path = get_exclusion_log_path()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "reason": reason,
        "details": details or {}
    }
    
    with open(log_path, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def log_vr_mapping(entries: List[Dict[str, Any]]) -> None:
    """
    Log VR mapping data to the VR mapping log file.
    
    Args:
        entries: List of dictionaries containing mapping data.
    """
    ensure_directories()
    log_path = get_vr_mapping_log_path()
    
    with open(log_path, 'a') as f:
        for entry in entries:
            # Write as CSV-like format or JSON lines as per spec
            # Spec requests: CSV with columns story_id, salience_level, blend_shape_params
            story_id = entry.get('story_id', 'NA')
            salience = entry.get('salience_level', 'NA')
            params = entry.get('blend_shape_params', '{}')
            
            # Ensure params is a string if it's a dict
            if isinstance(params, dict):
                params = json.dumps(params)
            
            f.write(f"{story_id},{salience},{params}\n")

def log_pipeline_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a pipeline step execution.
    
    Args:
        step_name: Name of the step.
        status: Status (e.g., 'started', 'completed', 'failed').
        details: Optional details.
    """
    ensure_directories()
    logger = get_logger("pipeline")
    
    msg = f"Step: {step_name} | Status: {status}"
    if details:
        msg += f" | Details: {json.dumps(details)}"
    
    if status == 'failed':
        logger.error(msg)
    else:
        logger.info(msg)
