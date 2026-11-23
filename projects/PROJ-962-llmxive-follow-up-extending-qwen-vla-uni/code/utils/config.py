"""
config.py - Environment configuration management.
"""
import os
import yaml
from typing import Dict, Any, Optional

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.yaml')

def get_config_path() -> str:
    return CONFIG_PATH

def load_config_from_file(path: Optional[str] = None) -> Dict[str, Any]:
    path = path or CONFIG_PATH
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def get_config() -> Dict[str, Any]:
    return load_config_from_file()

def set_config_value(key: str, value: Any) -> None:
    config = get_config()
    config[key] = value
    with open(CONFIG_PATH, 'w') as f:
        yaml.dump(config, f)

def get_clustering_params() -> Dict[str, Any]:
    config = get_config()
    return config.get('clustering', {
        'k_reduction_step_size': 5,
        'max_k_reduction_attempts': 10,
        'silhouette_threshold': 0.25,
        'max_clusters': 50
    })

def get_data_params() -> Dict[str, Any]:
    config = get_config()
    return config.get('data', {
        'dataset_name': 'Qwen-VLA/Hy-Embodied',
        'batch_size': 1000,
        'streaming': True
    })

def get_simulation_params() -> Dict[str, Any]:
    config = get_config()
    return config.get('simulation', {
        'dt': 0.01,
        'max_steps': 100,
        'joint_limits': {
            'min': -3.14,
            'max': 3.14
        }
    })