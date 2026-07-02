import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from dataclasses import dataclass, field, asdict
import yaml
from .logging import get_logger

@dataclass
class Config:
    """Configuration for the social memory network experiments."""
    seed: int = 42
    device: str = "cpu"
    experiment_name: str = "default_experiment"
    output_dir: str = "results"
    data_dir: str = "data"
    log_file: str = "experiment.log"
    model_name: str = "facebook/opt-125m"
    max_context_length: int = 512
    num_agents: int = 3
    num_games: int = 1000
    context_condition: str = "full"  # Options: "full", "limited"
    limited_context_tokens: int = 256
    scaling_agent_counts: List[int] = field(default_factory=lambda: [3, 5, 7])
    scaling_games_per_count: int = 800
    anova_alpha: float = 0.05
    power_target: float = 0.80

class ConfigManager:
    """Manages configuration loading and saving."""

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        self._config: Optional[Config] = None
        self._config_path: Path = Path(config_path) if config_path else Path("code/utils/config.yaml")
        self._logger = get_logger(__name__)

    def load_config(self) -> Config:
        """Load configuration from YAML file or create default."""
        if self._config is not None:
            return self._config

        if self._config_path.exists():
            self._logger.info(f"Loading config from {self._config_path}")
            with open(self._config_path, 'r') as f:
                data = yaml.safe_load(f)
                # Handle potential type mismatches from YAML (e.g., list vs tuple)
                if 'scaling_agent_counts' in data and isinstance(data['scaling_agent_counts'], tuple):
                    data['scaling_agent_counts'] = list(data['scaling_agent_counts'])
                self._config = Config(**data)
        else:
            self._logger.info(f"Config file not found at {self._config_path}, creating default")
            self._config = Config()
            self.save_config()

        return self._config

    def save_config(self, config: Optional[Config] = None) -> None:
        """Save configuration to YAML file."""
        if config is None:
            config = self._config
            if config is None:
                config = Config()

        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, 'w') as f:
            yaml.dump(dataclass_to_dict(config), f, default_flow_style=False)
        self._logger.info(f"Saved config to {self._config_path}")

    def reload_config(self) -> Config:
        """Force reload of configuration from disk."""
        self._config = None
        return self.load_config()

    @property
    def config(self) -> Config:
        """Get the current configuration."""
        if self._config is None:
            return self.load_config()
        return self._config

# Global config manager instance
_global_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Get or create the global config manager."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigManager()
    return _global_config_manager

def get_config() -> Config:
    """Get the current configuration."""
    return get_config_manager().config

def load_config(config_path: Optional[Union[str, Path]] = None) -> Config:
    """Load configuration from a specific path."""
    manager = ConfigManager(config_path)
    return manager.load_config()

def save_config(config: Optional[Config] = None, config_path: Optional[Union[str, Path]] = None) -> None:
    """Save configuration to a specific path."""
    manager = ConfigManager(config_path)
    manager.save_config(config)

def reload_config() -> Config:
    """Reload configuration from disk."""
    return get_config_manager().reload_config()

def get(key: str, default: Any = None) -> Any:
    """Get a specific config value by key."""
    config = get_config()
    return getattr(config, key, default)

def set_config(key: str, value: Any) -> None:
    """Set a specific config value."""
    config = get_config()
    if hasattr(config, key):
        setattr(config, key, value)
        get_config_manager().save_config(config)
    else:
        raise ValueError(f"Invalid config key: {key}")

def dataclass_to_dict(obj: Any) -> Dict[str, Any]:
    """Convert a dataclass instance to a dictionary."""
    result = {}
    for field_name in obj.__dataclass_fields__:
        value = getattr(obj, field_name)
        if isinstance(value, list):
            result[field_name] = value
        elif hasattr(value, '__dataclass_fields__'):
            result[field_name] = dataclass_to_dict(value)
        else:
            result[field_name] = value
    return result

def create_default_config() -> Config:
    """Create a default configuration."""
    return Config()

def ensure_config_exists() -> Path:
    """Ensure config file exists, creating it if necessary."""
    manager = get_config_manager()
    manager.load_config()
    return manager._config_path