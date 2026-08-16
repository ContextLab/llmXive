import yaml
import os
from typing import Dict, Any

def load_config(path: str = "code/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found at {path}")
    
    with open(path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Fill in missing keys with defaults if needed
    defaults = {
        'CODELLAMA_CPU_PATH': 'NOT_SET',
        'CODELLAMA_GPU_PATH': 'NOT_SET',
        'strata_threshold': 50,
        'non_inferiority_delta': 0.05,
        'entropy_n_samples': 10,
        'convergence_k_range': [1, 2, 3],
        'model_temperature': 0.7,
        'model_top_p': 0.95
    }
    
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    return config
