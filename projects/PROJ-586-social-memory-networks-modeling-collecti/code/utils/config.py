"""
Configuration management for the social memory network experiments.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field, asdict

@dataclass
class Config:
    """Experiment configuration."""
    seed: int = 42
    device: str = "cpu"
    model_name: str = "opt-125m"
    num_agents: int = 5
    num_games: int = 1000
    context_condition: str = "full"
    limited_context_threshold: int = 512
    output_dir: str = "results"
    log_dir: str = "logs"
    data_dir: str = "data"
    
    # Memory buffer settings
    memory_buffer_size: int = 10000
    memory_action_timeout: float = 5.0
    
    # Validation settings
    min_validation_rate: float = 0.95
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

class ConfigManager:
    """Manages configuration loading and saving."""
    
    _instance: Optional['ConfigManager'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config: Optional[Config] = None
        return cls._instance
    
    def load_config(self, config_path: Optional[Union[str, Path]] = None) -> Config:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path("code/config.yaml")
        else:
            config_path = Path(config_path)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_dict = yaml.safe_load(f)
            self.config = Config(**config_dict)
        else:
            # Create default config
            self.config = Config()
            self.save_config(config_path)
        
        return self.config
    
    def save_config(self, config_path: Union[str, Path], config: Optional[Config] = None):
        """Save configuration to YAML file."""
        if config is None:
            config = self.config
            if config is None:
                raise ValueError("No config to save")
        
        config_path = Path(config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False)
    
    def get_config(self) -> Config:
        """Get current configuration."""
        if self.config is None:
            self.load_config()
        return self.config
    
    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        if self.config is None:
            self.load_config()
        
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
    
    def reload_config(self, config_path: Optional[Union[str, Path]] = None):
        """Reload configuration from file."""
        self.config = None
        return self.load_config(config_path)

# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> Config:
    """Get the current configuration."""
    return get_config_manager().get_config()

def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from file."""
    return get_config_manager().load_config(config_path)

def save_config(config_path: Union[str, Path], config: Optional[Config] = None):
    """Save configuration to file."""
    get_config_manager().save_config(config_path, config)

def reload_config(config_path: Optional[Union[str, Path]] = None):
    """Reload configuration from file."""
    return get_config_manager().reload_config(config_path)

def get(key: str, default: Any = None) -> Any:
    """Get a configuration value by key."""
    config = get_config()
    return getattr(config, key, default)

def set_config(config: Config):
    """Set the global configuration."""
    get_config_manager().config = config

def dataclass_to_dict(obj) -> Dict[str, Any]:
    """Convert a dataclass to a dictionary."""
    return asdict(obj)

def create_default_config() -> Config:
    """Create and return a default configuration."""
    return Config()

def ensure_config_exists(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Ensure config file exists, creating it if necessary."""
    manager = get_config_manager()
    return manager.load_config(config_path)
