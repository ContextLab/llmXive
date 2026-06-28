"""
Configuration management for social memory network experiments.

This module provides configuration loading, management, and validation
for experiment parameters including model settings, memory buffer config,
and experiment parameters.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union
from dataclasses import dataclass, field
import yaml
from .logging import get_logger

logger = get_logger(__name__)

@dataclass
class Config:
    """Configuration dataclass for experiment parameters."""
    # Model settings
    model_name: str = "opt-125m"
    model_dtype: str = "float32"
    device: str = "cpu"
    
    # Memory buffer settings
    memory_capacity: int = 1000
    memory_action_token: str = "<MEMORY_ACTION>"
    
    # Experiment settings
    seed: int = 42
    num_games: int = 1000
    num_agents: int = 3
    
    # Dataset settings
    dataset_name: str = "synthetic"
    
    # Output settings
    output_dir: str = "projects/PROJ-586-social-memory-networks-modeling-collecti/results"
    log_file: str = "experiment.log"
    
    # Validation settings
    min_validation_rate: float = 0.95  # SC-001 requirement
    
    # Power analysis settings
    power_threshold: float = 0.70
    
    # Context settings
    full_context: bool = True
    limited_context_tokens: int = 512
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "model": {
                "model_name": self.model_name,
                "model_dtype": self.model_dtype,
                "device": self.device
            },
            "memory": {
                "memory_capacity": self.memory_capacity,
                "memory_action_token": self.memory_action_token
            },
            "experiment": {
                "seed": self.seed,
                "num_games": self.num_games,
                "num_agents": self.num_agents
            },
            "dataset": {
                "dataset_name": self.dataset_name
            },
            "output": {
                "output_dir": self.output_dir,
                "log_file": self.log_file
            },
            "validation": {
                "min_validation_rate": self.min_validation_rate
            },
            "power": {
                "power_threshold": self.power_threshold
            },
            "context": {
                "full_context": self.full_context,
                "limited_context_tokens": self.limited_context_tokens
            }
        }

class ConfigManager:
    """Manages configuration loading and saving."""
    
    _instance: Optional["ConfigManager"] = None
    
    def __new__(cls):
        """Singleton pattern for config manager."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._config = Config()
            cls._instance._loaded = False
        return cls._instance
    
    def __init__(self):
        """Initialize config manager (idempotent)."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._config = Config()
            self._loaded = False
    
    def load_config(self, config_path: Optional[str] = None) -> Config:
        """
        Load configuration from YAML file or environment variables.
        
        Args:
            config_path: Path to config YAML file
        
        Returns:
            Loaded Config instance
        """
        config = Config()
        
        # Try to load from file
        if config_path is None:
            # Default config path
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        else:
            config_path = Path(config_path)
        
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    file_config = yaml.safe_load(f)
                
                # Update config from file
                if "experiment" in file_config:
                    exp = file_config["experiment"]
                    config.seed = exp.get("seed", config.seed)
                    config.num_games = exp.get("num_games", config.num_games)
                    config.num_agents = exp.get("num_agents", config.num_agents)
                
                if "model" in file_config:
                    model = file_config["model"]
                    config.model_name = model.get("model_name", config.model_name)
                    config.device = model.get("device", config.device)
                
                if "output" in file_config:
                    output = file_config["output"]
                    config.output_dir = output.get("output_dir", config.output_dir)
                
                logger.info(f"Loaded config from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {e}")
        
        # Override with environment variables
        if os.getenv("EXPERIMENT_SEED"):
            config.seed = int(os.getenv("EXPERIMENT_SEED"))
        if os.getenv("EXPERIMENT_NUM_GAMES"):
            config.num_games = int(os.getenv("EXPERIMENT_NUM_GAMES"))
        if os.getenv("EXPERIMENT_NUM_AGENTS"):
            config.num_agents = int(os.getenv("EXPERIMENT_NUM_AGENTS"))
        if os.getenv("MODEL_DEVICE"):
            config.device = os.getenv("MODEL_DEVICE")
        if os.getenv("OUTPUT_DIR"):
            config.output_dir = os.getenv("OUTPUT_DIR")
        
        self._config = config
        self._loaded = True
        
        return config
    
    def get_config(self) -> Config:
        """Get current configuration."""
        if not self._loaded:
            self.load_config()
        return self._config
    
    def save_config(self, config: Config, config_path: str) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: Config instance to save
            config_path: Path to save config file
        """
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False)
        
        logger.info(f"Saved config to {config_path}")

# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get or create global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> Dict[str, Any]:
    """
    Get configuration as dictionary.
    
    Returns:
        Configuration dictionary
    """
    manager = get_config_manager()
    config = manager.get_config()
    return {
        "model_name": config.model_name,
        "device": config.device,
        "seed": config.seed,
        "num_games": config.num_games,
        "num_agents": config.num_agents,
        "output_dir": config.output_dir,
        "memory_capacity": config.memory_capacity,
        "min_validation_rate": config.min_validation_rate
    }

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration and return as dictionary.
    
    Args:
        config_path: Optional path to config file
    
    Returns:
        Configuration dictionary
    """
    manager = get_config_manager()
    manager.load_config(config_path)
    return get_config()

def reload_config() -> Dict[str, Any]:
    """
    Reload configuration from file/environment.
    
    Returns:
        Updated configuration dictionary
    """
    manager = get_config_manager()
    manager._loaded = False
    return get_config()

def get(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value by key.
    
    Args:
        key: Configuration key
        default: Default value if key not found
    
    Returns:
        Configuration value or default
    """
    config = get_config()
    return config.get(key, default)

def set_config(key: str, value: Any) -> None:
    """
    Set a configuration value.
    
    Args:
        key: Configuration key
        value: Value to set
    """
    config = get_config_manager().get_config()
    
    if key == "model_name":
        config.model_name = value
    elif key == "device":
        config.device = value
    elif key == "seed":
        config.seed = value
    elif key == "num_games":
        config.num_games = value
    elif key == "num_agents":
        config.num_agents = value
    elif key == "output_dir":
        config.output_dir = value
    elif key == "memory_capacity":
        config.memory_capacity = value
    elif key == "min_validation_rate":
        config.min_validation_rate = value

def create_default_config(config_path: str = "config.yaml") -> None:
    """
    Create a default configuration file.
    
    Args:
        config_path: Path to create config file
    """
    config = Config()
    manager = get_config_manager()
    manager.save_config(config, config_path)

def ensure_config_exists(config_path: str = "config.yaml") -> None:
    """
    Ensure configuration file exists, create if not.
    
    Args:
        config_path: Path to config file
    """
    if not Path(config_path).exists():
        create_default_config(config_path)
        logger.info(f"Created default config at {config_path}")

if __name__ == "__main__":
    # Test configuration
    config = get_config()
    print(f"Current config: {config}")
    
    # Create default config
    create_default_config()
    print("Created default config.yaml")
