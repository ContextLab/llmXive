import os
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

class Configuration:
    """Application configuration manager."""
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            env_file: Path to .env file. If None, looks for .env in current directory.
        """
        load_dotenv(env_file)
        self._config = {}
        self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration values."""
        self._config = {
            'GDLET_API_URL': os.getenv('GDLET_API_URL', 'https://api.gdeltproject.org/api/v2'),
            'GOOGLE_TRENDS_TIMEOUT': int(os.getenv('GOOGLE_TRENDS_TIMEOUT', '30')),
            'MAX_RETRIES': int(os.getenv('MAX_RETRIES', '3')),
            'BACKOFF_FACTOR': float(os.getenv('BACKOFF_FACTOR', '1.0')),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'DATA_DIR': os.getenv('DATA_DIR', 'data'),
            'CODE_DIR': os.getenv('CODE_DIR', 'code'),
            'OUTPUT_DIR': os.getenv('OUTPUT_DIR', 'data/reports'),
            'START_DATE': os.getenv('START_DATE', '2020-01-01'),
            'END_DATE': os.getenv('END_DATE', '2023-12-31'),
        }
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key.
            default: Default value if key not found.
        
        Returns:
            Configuration value.
        
        Raises:
            ConfigError: If key not found and no default provided.
        """
        if key in self._config:
            return self._config[key]
        elif default is not None:
            return default
        else:
            raise ConfigError(f"Configuration key '{key}' not found")
    
    def set(self, key: str, value: str):
        """Set a configuration value."""
        self._config[key] = value
    
    def validate(self) -> bool:
        """Validate that all required configuration values are present."""
        required_keys = [
            'GDLET_API_URL',
            'GOOGLE_TRENDS_TIMEOUT',
            'MAX_RETRIES',
            'DATA_DIR',
            'CODE_DIR'
        ]
        
        for key in required_keys:
            if key not in self._config or not self._config[key]:
                raise ConfigError(f"Required configuration '{key}' is missing or empty")
        
        return True

def main():
    """Main entry point for configuration test."""
    config = Configuration()
    
    try:
        config.validate()
        print("Configuration is valid")
        print(f"GDLET API URL: {config.get('GDLET_API_URL')}")
        print(f"Max Retries: {config.get('MAX_RETRIES')}")
        print(f"Data Directory: {config.get('DATA_DIR')}")
    except ConfigError as e:
        print(f"Configuration error: {e}")
        exit(1)

if __name__ == "__main__":
    main()