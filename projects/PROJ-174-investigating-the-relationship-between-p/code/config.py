"""
Configuration loader for the pipeline.
Loads and validates configuration from YAML file.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config(config_path: Path) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Dictionary containing configuration values
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    if not isinstance(config_path, Path):
        config_path = Path(config_path)
        
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Apply defaults for missing keys
    defaults = {
        'seeds': {'random': 42, 'numpy': 42},
        'thresholds': [0.40, 0.50, 0.60],
        'paths': {
            'raw_data': 'data/raw',
            'processed_data': 'data/processed',
            'results': 'results',
            'external_stimuli': 'data/external/stimuli'
        },
        'aggregation': False,
        'preprocessing': {
            'lowpass_cutoff': 4.0,
            'blink_threshold': 30.0,
            'max_blink_duration': 0.3
        },
        'analysis': {
            'fdr_method': 'benjamini_hochberg',
            'min_trials_per_subject': 20
        },
        'classification': {
            'window_duration': 2.0,
            'update_interval': 0.2,
            'l2_regularization': 1.0
        }
    }
    
    # Merge defaults with loaded config
    def merge_dicts(default, loaded):
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
        return result
    
    return merge_dicts(defaults, config)