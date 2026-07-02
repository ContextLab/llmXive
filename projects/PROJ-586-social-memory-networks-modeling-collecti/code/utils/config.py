import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, asdict

@dataclass
class Config:
    seed: int = 42
    device: str = "cpu"
    max_memory_entries: int = 10000
    default_agent_model: str = "opt-125m"
    experiment_dir: str = "data"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class ConfigManager:
    """Manages experiment configuration."""
    
    def __init__(self, config_path: str = "code/config.yaml"):
        self.config_path = Path(config_path)
        self.config: Config = self.load_config()
    
    def load_config(self) -> Config:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                return Config(**data)
        else:
            # Create default config
            default = Config()
            self.save_config(default)
            return default
    
    def save_config(self, config: Optional[Config] = None):
        """Save configuration to file."""
        if config is None:
            config = self.config
        
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(config.to_dict(), f)
    
    def update(self, **kwargs):
        """Update configuration with new values."""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config()

# Global config manager instance
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get or create the global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def get_config() -> Config:
    """Get the current configuration."""
    return get_config_manager().config

def load_config(config_path: str = "code/config.yaml") -> Config:
    """Load configuration from a specific path."""
    manager = ConfigManager(config_path)
    return manager.config

def save_config(config: Config, config_path: str = "code/config.yaml"):
    """Save configuration to a specific path."""
    manager = ConfigManager(config_path)
    manager.config = config
    manager.save_config()

def reload_config():
    """Reload configuration from file."""
    global _config_manager
    if _config_manager:
        _config_manager.config = _config_manager.load_config()

def get(key: str, default: Any = None) -> Any:
    """Get a configuration value by key."""
    config = get_config()
    return getattr(config, key, default)

def set_config(key: str, value: Any):
    """Set a configuration value."""
    manager = get_config_manager()
    manager.update(**{key: value})

def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert a dataclass to a dictionary."""
    return asdict(obj)

def create_default_config() -> Config:
    """Create and return a default configuration."""
    return Config()

def ensure_config_exists(config_path: str = "code/config.yaml"):
    """Ensure configuration file exists, creating if necessary."""
    manager = ConfigManager(config_path)
    if not manager.config_path.exists():
        manager.save_config()
