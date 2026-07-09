"""
Utility functions for the meta-analysis pipeline.
Includes logging setup, config loading, and checksum generation.
"""
import os
import yaml
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional

def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configure logging for the pipeline."""
    log_level = getattr(logging, log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load a YAML configuration file."""
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def generate_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """Generate a checksum for a file."""
    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def parse_inclusion_criteria(criteria_path: Path) -> Dict[str, Any]:
    """
    Parse the inclusion criteria YAML file.
    This function is a placeholder for T017's output format.
    """
    if not criteria_path.exists():
        raise FileNotFoundError(f"Inclusion criteria file not found: {criteria_path}")
    
    with open(criteria_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)
