"""
Configuration management for the MOND validity assessment pipeline.

Handles loading of metadata, paths, and simulation parameters from YAML files.
"""

import os
import yaml
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Standard directory structure
DIRS = {
    "code": PROJECT_ROOT / "code",
    "data": PROJECT_ROOT / "data",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "results": PROJECT_ROOT / "results",
    "tests": PROJECT_ROOT / "tests",
    "state": PROJECT_ROOT / "state",
    "specs": PROJECT_ROOT / "specs",
    "figures": PROJECT_ROOT / "figures",
}

# Ensure directories exist
def ensure_dirs():
    """Create all standard directories if they don't exist."""
    for d in DIRS.values():
        d.mkdir(parents=True, exist_ok=True)
    return DIRS

# Configuration cache
_config_cache = None

def load_config(config_path=None):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to config file. Defaults to 'data/metadata.yaml'
                    if not provided.
                    
    Returns:
        dict: Configuration dictionary
    """
    global _config_cache
    
    if _config_cache is not None:
        return _config_cache
        
    if config_path is None:
        config_path = DIRS["data"] / "metadata.yaml"
    else:
        config_path = Path(config_path)
        
    if not config_path.exists():
        # Create a default metadata file if it doesn't exist
        create_default_metadata()
        
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
        
    _config_cache = config
    return config

def get_config(key=None, default=None):
    """
    Get a specific configuration value.
    
    Args:
        key: Dot-separated key path (e.g., 'download.retry_count')
        default: Default value if key not found
                
    Returns:
        Configuration value or default
    """
    config = load_config()
    
    if key is None:
        return config
        
    # Navigate nested dict
    parts = key.split('.')
    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default
            
    return value

def create_default_metadata():
    """Create a default metadata.yaml file if it doesn't exist."""
    metadata_path = DIRS["data"] / "metadata.yaml"
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    default_metadata = {
        "project": {
            "name": "PROJ-076-assessing-the-validity-of-modified-newto",
            "description": "Assessing the Validity of Modified Newtonian Dynamics with Galaxy Rotation Curves",
            "version": "0.1.0"
        },
        "data": {
            "source": "SPARC",
            "url": "http://astroweb.cs.washington.edu/SPARC/",
            "download_timestamp": None,
            "version": "1.0"
        },
        "models": {
            "mond": {
                "a0": 1.2e-10,  # m/s^2
                "interpolating_function": "simple"
            },
            "nfw": {
                "concentration_prior": {
                    "enabled": True,
                    "scaling_exponent": -0.5  # Negative as per plan summary
                }
            }
        },
        "analysis": {
            "inclination_threshold": 10.0,  # degrees
            "min_points": 15,
            "alpha": 0.05,  # Significance level
            "bootstrap_iterations": 1000,
            "chi2_thresholds": [1.0, 1.25, 1.5, 1.75]
        },
        "paths": {
            "raw_data": "data/raw/sparc_data.zip",
            "processed_data": "data/processed/filtered_galaxies.csv",
            "fit_results": "results/fit_summary.csv",
            "sensitivity_data": "results/sensitivity_data.csv",
            "residual_stats": "results/residual_stats.csv",
            "sensitivity_report": "results/sensitivity_report.md",
            "analysis_verdict": "results/analysis_verdict.md"
        }
    }
    
    with open(metadata_path, 'w') as f:
        yaml.dump(default_metadata, f, default_flow_style=False, sort_keys=False)
        
    return metadata_path
