"""
Configuration management module.
Loads settings from YAML and manages environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. If None, uses default location.
        
    Returns:
        Dictionary with configuration values
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config" / "logging.yaml"
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        # Default configuration if file doesn't exist
        return {
            "output_dir": "data/raw",
            "TIMEOUT_GRAPHS": 300,
            "random_seed": 42,
            "log_level": "INFO"
        }
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load config file {config_path}: {str(e)}")
    
    # Override with environment variables if present
    if 'OUTPUT_DIR' in os.environ:
        config['output_dir'] = os.environ['OUTPUT_DIR']
    if 'TIMEOUT_GRAPHS' in os.environ:
        try:
            config['TIMEOUT_GRAPHS'] = int(os.environ['TIMEOUT_GRAPHS'])
        except ValueError:
            pass
    
    return config
