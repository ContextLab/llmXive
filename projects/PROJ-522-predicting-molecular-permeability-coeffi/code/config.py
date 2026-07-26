import os
import yaml
from pathlib import Path

def load_config():
    """
    Load configuration from code/config/logging.yaml and environment variables.
    Returns a dictionary with all configuration values.
    """
    config_path = Path(__file__).parent / "config" / "logging.yaml"
    
    config = {}
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            yaml_config = yaml.safe_load(f)
            config.update(yaml_config)
    
    # Override with environment variables if present
    if 'TIMEOUT_GRAPHS' in os.environ:
        config['TIMEOUT_GRAPHS'] = int(os.environ['TIMEOUT_GRAPHS'])
    
    # Default values
    config.setdefault('TIMEOUT_GRAPHS', 120) # Default 2 hours
    config.setdefault('RANDOM_SEED', 42)
    
    return config