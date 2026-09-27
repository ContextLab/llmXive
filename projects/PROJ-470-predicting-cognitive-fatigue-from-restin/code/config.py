"""
Configuration loader for the pipeline.
"""
import yaml
from pathlib import Path

def load_config(config_path: str = "code/config.yaml") -> dict:
    """
    Load configuration from a YAML file.
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure required keys exist with defaults
    defaults = {
        'filter_low': 1.0,
        'filter_high': 40.0,
        'artifact_threshold_uV': 100,
        'random_seed': 42,
        'notch_frequency': 50.0,
        'min_segment_length': 120
    }
    
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    return config
