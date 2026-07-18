"""
Logging utilities for the llmXive science pipeline.

Provides centralized logging configuration and helper functions
for specific log types (exclusions, VR mappings, pipeline steps).
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List

from code.config import ensure_directories

class LogType:
    """Constants for different log types."""
    EXCLUSION = 'exclusion'
    VR_MAPPING = 'vr_mapping'
    PIPELINE_STEP = 'pipeline_step'
    GENERAL = 'general'

def get_log_path(log_type: str) -> Path:
    """
    Get the file path for a specific log type.
    
    Args:
        log_type: The type of log (exclusion, vr_mapping, etc.)
        
    Returns:
        Path object for the log file.
    """
    base_dir = Path('data/logs')
    ensure_directories(base_dir)
    
    if log_type == LogType.EXCLUSION:
        return base_dir / 'exclusion.log'
    elif log_type == LogType.VR_MAPPING:
        return base_dir / 'vr_mapping.log'
    elif log_type == LogType.PIPELINE_STEP:
        return base_dir / 'pipeline.log'
    else:
        return base_dir / 'general.log'

def get_vr_mapping_log_path() -> Path:
    """
    Get the specific path for VR mapping logs.
    
    Returns:
        Path object for the vr_mapping.log file.
    """
    return get_log_path(LogType.VR_MAPPING)

def get_exclusion_log_path() -> Path:
    """
    Get the specific path for exclusion logs.
    
    Returns:
        Path object for the exclusion.log file.
    """
    return get_log_path(LogType.EXCLUSION)

def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: The name of the logger (usually __name__).
        
    Returns:
        Configured logging.Logger instance.
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
        
    logger.setLevel(logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Create file handler for general logs
    general_log_path = get_log_path(LogType.GENERAL)
    file_handler = logging.FileHandler(general_log_path)
    file_handler.setLevel(logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_exclusion(reason: str, record_id: str, extra_details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an exclusion event to the exclusion log file.
    
    Args:
        reason: The reason for exclusion.
        record_id: The ID of the excluded record.
        extra_details: Optional dictionary of additional details.
    """
    log_path = get_exclusion_log_path()
    ensure_directories(log_path.parent)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = {
        'timestamp': timestamp,
        'record_id': record_id,
        'reason': reason,
        'details': extra_details or {}
    }
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"{log_entry}\n")
        
    logger = logging.getLogger('exclusion')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        
    logger.info(f"Excluded {record_id}: {reason}")

def log_vr_mapping(mappings: List[Dict[str, Any]]) -> None:
    """
    Log VR mapping events to the vr_mapping log file.
    
    Args:
        mappings: List of dictionaries containing mapping details.
                Expected keys: story_id, salience_level.
    """
    log_path = get_vr_mapping_log_path()
    ensure_directories(log_path.parent)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(log_path, 'a', encoding='utf-8') as f:
        for mapping in mappings:
            story_id = mapping.get('story_id', 'unknown')
            salience_level = mapping.get('salience_level', 'unknown')
            f.write(f"{timestamp} | {story_id} -> {salience_level}\n")
    
    logger = logging.getLogger('vr_mapping')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        
    logger.info(f"Logged {len(mappings)} VR mapping entries to {log_path}")

def log_pipeline_step(step_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log a pipeline step execution.
    
    Args:
        step_name: Name of the pipeline step.
        status: Status of the step (started, completed, failed).
        details: Optional dictionary of additional details.
    """
    log_path = get_log_path(LogType.PIPELINE_STEP)
    ensure_directories(log_path.parent)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    log_entry = {
        'timestamp': timestamp,
        'step': step_name,
        'status': status,
        'details': details or {}
    }
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"{log_entry}\n")
        
    logger = logging.getLogger('pipeline')
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.FileHandler(log_path)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        
    logger.info(f"Pipeline step '{step_name}' - {status}")