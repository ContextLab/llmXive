"""
Configuration loader for project parameters.
Reads from artifacts/preprocess.yaml if available, otherwise uses defaults.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict

def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. If None, looks for 
                     artifacts/preprocess.yaml in project root.
                     
    Returns:
        Dictionary of configuration parameters.
    """
    if config_path is None:
        config_path = get_project_root() / "artifacts" / "preprocess.yaml"
    
    config_file = Path(config_path)
    
    default_config = {
        "preprocessing": {
            "microbiome": {
                "pseudocount": 0.5,
                "filter_threshold": 0.01,
                "qiime_version": "2023.5"
            },
            "eeg": {
                "filter_low": 0.5,
                "filter_high": 45.0,
                "ica_components": 20,
                "epoch_duration": 120,  # 2 minutes
                "valid_epoch_ratio": 0.8
            }
        },
        "analysis": {
            "correlation": {
                "top_taxa_count": 20,
                "fdr_q_threshold": 0.1
            },
            "matching": {
                "min_pairs_threshold": 10,
                "demographic_features": ["Age", "Sex", "BMI"]
            }
        },
        "random_seed": 42
    }
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            user_config = yaml.safe_load(f)
            # Deep merge would be ideal, but simple update for now
            for section in user_config:
                if section in default_config:
                    default_config[section].update(user_config[section])
    
    return default_config

# Global config instance
CONFIG = load_config()
