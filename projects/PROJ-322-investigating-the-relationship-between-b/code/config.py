import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Global state for methodology validation mode
_is_synthetic = False
_methodology_validation_mode = False

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = os.getenv("LLMXIVE_CONFIG", "config.yaml")
    
    config_file = Path(config_path)
    if not config_file.exists():
        return {}
    
    with open(config_file, "r") as f:
        return yaml.safe_load(f) or {}

def is_synthetic() -> bool:
    """Check if the project is running in synthetic data mode."""
    return _is_synthetic

def is_methodology_validation_mode() -> bool:
    """Check if the project is in Methodology Validation Mode."""
    return _methodology_validation_mode

def set_synthetic_mode(enabled: bool) -> None:
    """Enable or disable synthetic data mode globally."""
    global _is_synthetic
    _is_synthetic = enabled
    logging.info(f"Synthetic mode set to: {enabled}")

def check_data_availability() -> bool:
    """
    Check if real data exists in the expected directories.
    Returns True if real data is found, False otherwise.
    """
    data_dirs = [
        Path("data/raw"),
        Path("data/processed"),
        Path("data/results")
    ]
    
    for d in data_dirs:
        if d.exists() and any(d.iterdir()):
            return True
    
    # Check for specific expected files
    expected_files = [
        Path("data/results/manifest.csv"),
        Path("data/processed/connectivity_matrices.json")
    ]
    
    for f in expected_files:
        if f.exists():
            return True
    
    return False

def initialize_methodology_validation_mode() -> bool:
    """
    Initialize the methodology validation mode.
    Returns True if mode was activated (no real data found), False otherwise.
    """
    global _methodology_validation_mode
    
    if not check_data_availability():
        _methodology_validation_mode = True
        _is_synthetic = True
        logging.warning("No real data found. Activating Methodology Validation Mode with synthetic data.")
        return True
    
    _methodology_validation_mode = False
    _is_synthetic = False
    logging.info("Real data found. Running in standard mode.")
    return False

def get_memory_limit_gb() -> float:
    """Get the memory limit in GB."""
    return float(os.getenv("LLMXIVE_MEMORY_LIMIT_GB", "6.0"))

def get_runtime_limit_hours() -> float:
    """Get the runtime limit in hours."""
    return float(os.getenv("LLMXIVE_RUNTIME_LIMIT_HOURS", "6.0"))

def get_warning_runtime_hours() -> float:
    """Get the warning runtime threshold in hours."""
    return get_runtime_limit_hours() * 0.9  # 90% of limit
