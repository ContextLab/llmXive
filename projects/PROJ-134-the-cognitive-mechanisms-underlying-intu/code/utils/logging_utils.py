"""
Logging utilities for the moral judgments research pipeline.

This module provides standardized logging functions for different types of
pipeline events, including exclusions, VR mappings, and general pipeline steps.
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import ensure_directories


class LogType:
    """Enumeration of log types."""
    EXCLUSION = 'exclusion'
    VR_MAPPING = 'vr_mapping'
    PIPELINE_STEP = 'pipeline_step'
    GENERAL = 'general'


def get_log_path(log_type: str) -> Path:
    """
    Get the file path for a specific log type.
    
    Args:
        log_type: Type of log (exclusion, vr_mapping, pipeline_step, general)
        
    Returns:
        Path to the log file
    """
    ensure_directories()
    log_dir = Path('data/logs')
    
    if log_type == LogType.EXCLUSION:
        return log_dir / 'exclusion.log'
    elif log_type == LogType.VR_MAPPING:
        return log_dir / 'vr_mapping.log'
    elif log_type == LogType.PIPELINE_STEP:
        return log_dir / 'pipeline.log'
    else:
        return log_dir / 'general.log'


def get_vr_mapping_log_path() -> Path:
    """
    Get the specific path for VR mapping logs.
    
    Returns:
        Path to the VR mapping log file
    """
    return get_log_path(LogType.VR_MAPPING)


def get_exclusion_log_path() -> Path:
    """
    Get the specific path for exclusion logs.
    
    Returns:
        Path to the exclusion log file
    """
    return get_log_path(LogType.EXCLUSION)


def get_logger(name: str, log_file: Optional[Path] = None) -> logging.Logger:
    """
    Get a configured logger with file handler.
    
    Args:
        name: Logger name
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Add file handler if log_file is provided
    if log_file:
        ensure_directories()
        file_handler = logging.FileHandler(str(log_file))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add console handler for debugging
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_exclusion(
    reason: str,
    record_id: str,
    dataset: str,
    log_path: Optional[Path] = None
) -> None:
    """
    Log an exclusion event.
    
    Args:
        reason: Reason for exclusion
        record_id: ID of the excluded record
        dataset: Name of the dataset
        log_path: Optional custom log path
    """
    if log_path is None:
        log_path = get_exclusion_log_path()
    
    logger = get_logger('exclusion', log_path)
    logger.warning(f"Excluded {record_id} from {dataset}: {reason}")


def log_vr_mapping(
    story_id: str,
    salience_level: str,
    blend_shapes: Dict[str, float],
    log_path: Optional[Path] = None
) -> None:
    """
    Log a VR mapping decision.
    
    Args:
        story_id: The story identifier
        salience_level: Assigned salience level ('low' or 'high')
        blend_shapes: Dictionary of blend shape parameters
        log_path: Optional custom log path
    """
    if log_path is None:
        log_path = get_vr_mapping_log_path()
    
    logger = get_logger('vr_mapping', log_path)
    
    # Format blend shapes for logging
    blend_str = ', '.join([f"{k}={v:.4f}" for k, v in blend_shapes.items()])
    
    log_message = (
        f"STORY_ID={story_id} -> SALIENCE={salience_level} | "
        f"BLEND_SHAPES=[{blend_str}]"
    )
    
    logger.info(log_message)

def log_pipeline_step(
    step_name: str,
    status: str,
    details: Optional[Dict[str, Any]] = None,
    log_path: Optional[Path] = None
) -> None:
    """
    Log a pipeline step execution.
    
    Args:
        step_name: Name of the pipeline step
        status: Status (start, complete, error)
        details: Optional details about the step
        log_path: Optional custom log path
    """
    if log_path is None:
        log_path = get_log_path(LogType.PIPELINE_STEP)
    
    logger = get_logger('pipeline', log_path)
    
    if details:
        details_str = ', '.join([f"{k}={v}" for k, v in details.items()])
        logger.info(f"{step_name} [{status}]: {details_str}")
    else:
        logger.info(f"{step_name} [{status}]")
