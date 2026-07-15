import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Configuration management class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_path: Path to the config.yaml file. If None, uses default locations.
        """
        self.config_path = config_path or self._find_config_path()
        self._config = self._load_config()
        
        # Load environment variables
        self._load_env()
        
    def _find_config_path(self) -> str:
        """Find the config.yaml file."""
        possible_paths = [
            "code/config/config.yaml",
            "config.yaml",
            "code/config.yaml"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Create default config if not found
        return self._create_default_config()
        
    def _create_default_config(self) -> str:
        """Create a default config.yaml file."""
        default_config = {
            'output_dir': 'data/processed',
            'seed': 42,
            'max_runtime_hours': 6,
            'max_ram_gb': 7,
            'primary_doi': '10.5281/zenodo.10043838',
            'fallback_doi': '10.5281/zenodo.11023456'
        }
        
        config_path = "code/config/config.yaml"
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        logging.info(f"Created default config at {config_path}")
        return config_path
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config if config else {}
        except Exception as e:
            raise ConfigError(f"Failed to load config from {self.config_path}: {str(e)}")
            
    def _load_env(self):
        """Load environment variables, overriding config if present."""
        env_vars = ['PRIMARY_DOI', 'FALLBACK_DOI', 'OUTPUT_DIR']
        
        for var in env_vars:
            if var in os.environ:
                env_key = var.lower()
                if var == 'PRIMARY_DOI':
                    self._config['primary_doi'] = os.environ[var]
                elif var == 'FALLBACK_DOI':
                    self._config['fallback_doi'] = os.environ[var]
                elif var == 'OUTPUT_DIR':
                    self._config['output_dir'] = os.environ[var]
                    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key.
            default: Default value if key not found.
            
        Returns:
            The configuration value or default.
        """
        return self._config.get(key, default)
        
    def __getitem__(self, key: str) -> Any:
        """Get configuration value using dictionary syntax."""
        if key not in self._config:
            raise KeyError(f"Configuration key '{key}' not found")
        return self._config[key]
        
    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration."""
        return key in self._config

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the singleton configuration instance.
    
    Returns:
        The Config instance.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def main():
    """Main function for testing configuration."""
    config = get_config()
    print("Configuration loaded:")
    for key, value in config._config.items():
        print(f"  {key}: {value}")
    return config

if __name__ == "__main__":
    main()
