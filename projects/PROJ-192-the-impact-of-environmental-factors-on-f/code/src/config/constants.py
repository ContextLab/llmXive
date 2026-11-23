"""
Configuration loader for project constants.
Wraps the YAML constants file for programmatic access.
"""
import yaml
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def get_config():
    """
    Load and return configuration from src/config/constants.yaml.
    Returns a dictionary of configuration values.
    """
    config_path = Path(__file__).parent / "constants.yaml"
    
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}. Using defaults.")
        return {
            "vif_threshold": 5,
            "p_value_threshold": 0.05,
            "min_samples": 10,
            "max_ram_gb": 7,
            "permutations": 999
        }

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {
            "vif_threshold": 5,
            "p_value_threshold": 0.05,
            "min_samples": 10,
            "max_ram_gb": 7,
            "permutations": 999
        }
