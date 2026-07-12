"""
Configuration management for hyperparameters, seeds, and path configuration.
"""
import os
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np

class Config:
    """Singleton configuration manager."""
    
    _instance: Optional['Config'] = None
    _config_dict: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._config_dict = {
            "project_root": "code",
            "seeds": [],
            "hyperparameters": {
                "num_seeds": 30,
                "episodes_per_seed": 5,
                "max_steps": 1000,
                "learning_rate": 0.001,
                "gamma": 0.99,
                "batch_size": 64,
                "buffer_size": 100000,
                "exploration_fraction": 0.1,
                "exploration_final_eps": 0.01,
                "train_freq": 4,
                "target_update_freq": 1000,
                "gradient_steps": 1,
                "device": "cpu",
                "noise_std": 0.1
            },
            "paths": {
                "data": "data",
                "results": "results",
                "models": "models",
                "logs": "logs"
            },
            "environment": {
                "sim_type": "carla",
                "map_size": (1000, 1000),
                "agent_spawn_x": 0.0,
                "agent_spawn_y": 0.0,
                "target_x": 100.0,
                "target_y": 100.0
            }
        }
        
        # Load from file if exists
        config_file = Path("code/config.json")
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                    self._config_dict.update(saved_config)
            except Exception as e:
                print(f"Warning: Could not load config.json: {e}")
                
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self._config_dict
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
        
    def set(self, key: str, value: Any):
        """Set a configuration value by key (supports dot notation)."""
        keys = key.split('.')
        current = self._config_dict
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
      
    def save(self, filepath: Optional[str] = None):
        """Save configuration to a JSON file."""
        filepath = filepath or "code/config.json"
        with open(filepath, 'w') as f:
            json.dump(self._config_dict, f, indent=2)
            
    def reset(self):
        """Reset configuration to defaults."""
        self._config_dict = {
            "project_root": "code",
            "seeds": [],
            "hyperparameters": {
                "num_seeds": 30,
                "episodes_per_seed": 5,
                "max_steps": 1000,
                "learning_rate": 0.001,
                "gamma": 0.99,
                "batch_size": 64,
                "buffer_size": 100000,
                "exploration_fraction": 0.1,
                "exploration_final_eps": 0.01,
                "train_freq": 4,
                "target_update_freq": 1000,
                "gradient_steps": 1,
                "device": "cpu",
                "noise_std": 0.1
            },
            "paths": {
                "data": "data",
                "results": "results",
                "models": "models",
                "logs": "logs"
            },
            "environment": {
                "sim_type": "carla",
                "map_size": (1000, 1000),
                "agent_spawn_x": 0.0,
                "agent_spawn_y": 0.0,
                "target_x": 100.0,
                "target_y": 100.0
            }
        }

# Global instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration singleton."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def init_config():
    """Initialize the global configuration."""
    global _config
    _config = Config()

def get_path(key: str) -> str:
    """Get a path from configuration, resolving relative to project root."""
    config = get_config()
    base = config.get("project_root", "code")
    path_key = f"paths.{key}"
    relative_path = config.get(path_key, key)
    return str(Path(base) / relative_path)

def get_hyperparameter(key: str) -> Any:
    """Get a hyperparameter value."""
    config = get_config()
    return config.get(f"hyperparameters.{key}")

def set_hyperparameter(key: str, value: Any):
    """Set a hyperparameter value."""
    config = get_config()
    config.set(f"hyperparameters.{key}", value)

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
