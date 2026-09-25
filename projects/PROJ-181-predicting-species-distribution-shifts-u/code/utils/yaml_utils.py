"""
YAML utilities for the project.
Handles writing and reading YAML configuration and logs.
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from config import LOGS_DIR
from logging_config import get_logger

def write_preprocess_counts(data: Dict[str, Any]) -> None:
    """
    Write preprocessing counts to the YAML log file.
    
    Args:
        data: Dictionary containing species, before_count, after_count, timestamp, and distance_used_km.
    """
    logger = get_logger("yaml_utils")
    logger.info(f"Writing preprocess counts to YAML: {data}")
    
    # Ensure LOGS_DIR exists
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    output_path = LOGS_DIR / "preprocess_counts.yaml"
    
    try:
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Preprocess counts written to: {output_path}")
    except Exception as e:
        logger.error(f"Failed to write YAML file: {e}")
        raise

def read_yaml_file(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Read a YAML file and return its contents as a dictionary.
    
    Args:
        file_path: Path to the YAML file.
        
    Returns:
        Dictionary with the file contents, or None if the file does not exist.
    """
    logger = get_logger("yaml_utils")
    
    if not file_path.exists():
        logger.warning(f"YAML file not found: {file_path}")
        return None
    
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return data
    except Exception as e:
        logger.error(f"Failed to read YAML file {file_path}: {e}")
        raise
