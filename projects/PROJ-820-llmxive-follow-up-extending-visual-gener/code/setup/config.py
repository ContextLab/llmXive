import os
import random
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List
import json

class Config:
    """Configuration manager for llmXive pipeline."""

    def __init__(self, config_path: Optional[Path] = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        import yaml
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def save(self) -> None:
        """Save configuration to YAML file."""
        import yaml
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)

    def get_seed(self) -> int:
        """Get the random seed."""
        return self.get('seed', 42)

    def set_seed(self, seed: int) -> None:
        """Set the random seed."""
        self.set('seed', seed)
        random.seed(seed)
        os.environ['PYTHONHASHSEED'] = str(seed)

    def get_model_path(self) -> str:
        """Get the model path."""
        return self.get('model_path', 'latent-consistency/lcm-lora-sdv')

    def get_device(self) -> str:
        """Get the device."""
        return self.get('device', 'cpu')

    def get_path(self, path_name: str) -> Path:
        """Get a path from configuration."""
        path = self.get(f'paths.{path_name}', '')
        return Path(path)

def main() -> None:
    """Main function for config module."""
    config = Config()
    print(f"Seed: {config.get_seed()}")
    print(f"Model path: {config.get_model_path()}")
    print(f"Device: {config.get_device()}")

if __name__ == "__main__":
    main()
