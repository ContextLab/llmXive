"""
Configuration package for the molecular toxicity prediction pipeline.

This package manages structural alert definitions, hyperparameters, and
runtime configuration settings.
"""

from pathlib import Path

# Root directory for configuration files
CONFIG_ROOT = Path(__file__).parent

# Default configuration files
STRUCTURAL_ALERTS_FILE = CONFIG_ROOT / "structural_alerts.json"

def get_config_path(filename: str) -> Path:
    """
    Resolve a configuration file path relative to the config root.
    
    Args:
        filename: Name of the configuration file.
        
    Returns:
        Absolute Path object for the configuration file.
    """
    return CONFIG_ROOT / filename
