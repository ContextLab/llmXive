"""
Logging Configuration for Research Pipeline.
"""
import logging
import os
import yaml
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path

def get_logger(name: str = 'research_pipeline') -> logging.Logger:
    """Get a configured logger."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # File handler (optional, could be directed to a log file)
    # fh = logging.FileHandler('research.log')
    # fh.setLevel(logging.DEBUG)
    # logger.addHandler(fh)

    return logger

def initialize_modeling_log(log_path: str):
    """Initialize the modeling_log.yaml file if it doesn't exist."""
    path = Path(log_path)
    if not path.exists():
        log_data = {
            'pipeline_start': datetime.now().isoformat(),
            'tasks': {},
            'power_analysis': {},
            'validity_analysis': {}
        }
        with open(path, 'w') as f:
            yaml.dump(log_data, f, default_flow_style=False)
        logging.info(f"Initialized modeling log at {log_path}")

def update_log_section(section_name: str, data: Dict[str, Any], log_path: str):
    """Update a specific section in the modeling_log.yaml."""
    path = Path(log_path)
    if not path.exists():
        initialize_modeling_log(log_path)

    with open(path, 'r') as f:
        log_data = yaml.safe_load(f) or {}

    log_data[section_name] = data

    with open(path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)

def append_log_entry(section_name: str, key: str, value: Any, log_path: str):
    """Append an entry to a list in a specific section."""
    path = Path(log_path)
    if not path.exists():
        initialize_modeling_log(log_path)

    with open(path, 'r') as f:
        log_data = yaml.safe_load(f) or {}

    if section_name not in log_data:
        log_data[section_name] = []

    log_data[section_name].append({key: value})

    with open(path, 'w') as f:
        yaml.dump(log_data, f, default_flow_style=False)
