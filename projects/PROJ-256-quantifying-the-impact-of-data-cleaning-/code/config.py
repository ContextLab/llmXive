import os
from typing import List, Optional, Any, Dict
from dotenv import load_dotenv

class Config:
    """Configuration manager that loads from environment variables and .env file."""
    
    def __init__(self):
        load_dotenv()
        self._config = {
            'DATASET_URLS': os.getenv('DATASET_URLS', 'https://archive.ics.uci.edu/ml/datasets/'),
            'OUTPUT_PATH': os.getenv('OUTPUT_PATH', 'data/processed'),
            'RANDOM_SEED': int(os.getenv('RANDOM_SEED', '42')),
            'BOOTSTRAP_ITERATIONS': int(os.getenv('BOOTSTRAP_ITERATIONS', '1000')),
            'RAW_DATA_PATH': os.getenv('RAW_DATA_PATH', 'data/raw'),
            'PROCESSED_DATA_PATH': os.getenv('PROCESSED_DATA_PATH', 'data/processed'),
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'OUTCOME_COL': os.getenv('OUTCOME_COL', 'outcome'),
            'PREDICTOR_COL': os.getenv('PREDICTOR_COL', 'predictor'),
            'REGRESSION_COLS': os.getenv('REGRESSION_COLS', 'predictor').split(','),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self._config[key] = value
    
    def __getitem__(self, key: str) -> Any:
        """Allow dict-like access."""
        return self._config[key]
    
    def __contains__(self, key: str) -> bool:
        """Allow 'in' operator."""
        return key in self._config
    
    # Logger-style no-op methods for tolerance
    def info(self, *args, **kwargs):
        pass
    
    def debug(self, *args, **kwargs):
        pass
    
    def warning(self, *args, **kwargs):
        pass
    
    def error(self, *args, **kwargs):
        pass
    
    def critical(self, *args, **kwargs):
        pass
    
    def exception(self, *args, **kwargs):
        pass
    
    def log(self, *args, **kwargs):
        pass

# Global config instance
_config_instance = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reload_config() -> Config:
    """Reload configuration from environment."""
    global _config_instance
    _config_instance = Config()
    return _config_instance