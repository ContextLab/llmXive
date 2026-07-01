import os
import random
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional

# Global random seed
RANDOM_SEED = 42

def set_global_seed(seed: int = RANDOM_SEED) -> None:
    """
    Set the global random seed for reproducibility.
    
    Args:
        seed: The seed value to use.
    """
    random.seed(seed)
    np.random.seed(seed)

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to the project root.
    """
    # Assume the project root is the parent of the 'code' directory
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or environment variables.
    
    Args:
        config_path: Optional path to the config file.
        
    Returns:
        Dictionary of configuration values.
    """
    load_dotenv()
    config = {}
    
    # Load from environment variables
    config['DATA_PATH'] = os.getenv('DATA_PATH', str(get_project_root() / 'data'))
    config['OUTPUT_PATH'] = os.getenv('OUTPUT_PATH', str(get_project_root() / 'output'))
    
    # Load from config file if provided
    if config_path and os.path.exists(config_path):
        import yaml
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config.update(file_config)
    
    return config

def get_data_path() -> Path:
    """
    Get the data directory path.
    
    Returns:
        Path to the data directory.
    """
    config = load_config()
    return Path(config['DATA_PATH'])

def get_output_path() -> Path:
    """
    Get the output directory path.
    
    Returns:
        Path to the output directory.
    """
    config = load_config()
    return Path(config['OUTPUT_PATH'])

def get_thresholds() -> Dict[str, float]:
    """
    Get threshold values for validation.
    
    Returns:
        Dictionary of threshold values.
    """
    # Default thresholds
    return {
        'track_loss_max': 0.05,  # 5%
        'calibration_min': 0.9,
    }
