"""
Configuration loader for the Automated Detection of Algorithmic Bias pipeline.

Loads project-specific settings from the state directory and defines
global constants required by other pipeline components.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Project root relative to this file
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_STATE_DIR = _PROJECT_ROOT / "state" / "projects"

# Methodology Constants
# Derived from FR-016 and SC-004: Threshold for title overlap verification
CITATION_TITLE_OVERLAP_THRESHOLD = 0.85

# Default config file name
_DEFAULT_CONFIG_FILE = "PROJ-059-automated-detection-of-algorithmic-bias-.yaml"


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""
    pass


def load_project_config(project_id: str = "PROJ-059-automated-detection-of-algorithmic-bias-") -> Dict[str, Any]:
    """
    Load the YAML configuration for a specific project from the state directory.
    
    Args:
        project_id: The project identifier (defaults to current project).
        
    Returns:
        A dictionary containing the project configuration.
        
    Raises:
        ConfigError: If the configuration file is missing or invalid.
    """
    config_path = _STATE_DIR / f"{project_id}.yaml"
    
    if not config_path.exists():
        # Fallback to default if specific ID not found but default exists
        default_path = _STATE_DIR / _DEFAULT_CONFIG_FILE
        if default_path.exists():
            config_path = default_path
        else:
            raise ConfigError(
                f"Configuration file not found at {config_path} "
                f"(or default at {default_path}). "
                "Ensure T001 (project structure) and T002 (state init) are complete."
            )
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
            
        if config is None:
            config = {}
            
        # Merge with defaults if needed
        return _apply_defaults(config)
        
    except yaml.YAMLError as e:
        raise ConfigError(f"Failed to parse YAML configuration: {e}") from e
    except IOError as e:
        raise ConfigError(f"Failed to read configuration file: {e}") from e


def _apply_defaults(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply default values for missing keys in the configuration.
    
    This ensures that downstream components have valid values even if
    the YAML file is minimal.
    """
    defaults = {
        "pipeline": {
            "batch_size": 100,
            "max_workers": 4,
            "timeout_seconds": 3600
        },
        "bias_detection": {
            "lexicon_path": "data/raw/lexicon.csv",
            "sentiment_threshold": 0.5,
            "citation_overlap_threshold": CITATION_TITLE_OVERLAP_THRESHOLD
        },
        "simulation": {
            "sample_size": 10000,
            "skew_range": [0.0, 0.1, 0.2, 0.3, 0.4, 0.5],
            "random_seed": 42
        }
    }
    
    # Simple deep merge for top-level keys
    merged = defaults.copy()
    for key, value in config.items():
        if key in merged and isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key].update(value)
        else:
            merged[key] = value
            
    return merged


# Global configuration instance, loaded on first access
_config: Optional[Dict[str, Any]] = None


def get_config() -> Dict[str, Any]:
    """
    Get the global configuration singleton.
    
    Loads the configuration if it hasn't been loaded yet.
    
    Returns:
        The project configuration dictionary.
    """
    global _config
    if _config is None:
        _config = load_project_config()
    return _config


def get_citation_threshold() -> float:
    """
    Get the citation title overlap threshold constant.
    
    Returns:
        The float threshold value.
    """
    return CITATION_TITLE_OVERLAP_THRESHOLD


# Eagerly load config at import time to fail fast if state is missing
try:
    _config = load_project_config()
except ConfigError:
    # Allow import to succeed but warn; actual usage will raise when get_config() is called
    _config = None
    # Do not raise here to allow tests to run even if state is missing
    # The actual error will be raised when get_config() is invoked.
    
# Expose constants directly for convenience
# Note: These are read-only constants defined at module level
__all__ = [
    "ConfigError",
    "load_project_config",
    "get_config",
    "get_citation_threshold",
    "CITATION_TITLE_OVERLAP_THRESHOLD",
]
