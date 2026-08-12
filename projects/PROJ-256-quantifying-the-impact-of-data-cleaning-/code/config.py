"""
Configuration management module.

Loads settings from environment variables and provides a Config class
that acts as a dictionary-like object with fallbacks.
"""
import os
from typing import Any, Dict, Optional

_config_data: Dict[str, Any] = {}

def get_config() -> 'Config':
    """
    Get the global configuration instance.
    
    Returns:
        Config instance.
    """
    if not _config_data:
        reload_config()
    return Config(_config_data)

def reload_config() -> None:
    """
    Reload configuration from environment variables.
    """
    global _config_data
    _config_data = {
        "RAW_DATA_PATH": os.getenv("RAW_DATA_PATH", "data/raw"),
        "PROCESSED_DATA_PATH": os.getenv("PROCESSED_DATA_PATH", "data/processed"),
        "FIGURES_PATH": os.getenv("FIGURES_PATH", "figures"),
        "OUTPUT_PATH": os.getenv("OUTPUT_PATH", "output"),
        "RANDOM_SEED": int(os.getenv("RANDOM_SEED", "42")),
        "BOOTSTRAP_ITERATIONS": int(os.getenv("BOOTSTRAP_ITERATIONS", "1000")),
        "DATASET_URLS": os.getenv("DATASET_URLS", ""),
        "BASELINE_METRICS_PATH": os.getenv("BASELINE_METRICS_PATH", "data/processed/baseline_metrics.json"),
        "CLEANED_METRICS_PATH": os.getenv("CLEANED_METRICS_PATH", "data/processed/cleaned_metrics.json"),
        "NULL_FPR_METRICS_PATH": os.getenv("NULL_FPR_METRICS_PATH", "data/processed/null_fpr_metrics.json"),
    }

class Config:
    """
    Configuration wrapper class.
    
    Provides dictionary-like access with .get() and attribute access.
    Designed to be tolerant of various access patterns.
    """
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self._data.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self._data[key]
    
    def __contains__(self, key: str) -> bool:
        return key in self._data
    
    def keys(self):
        return self._data.keys()
    
    def values(self):
        return self._data.values()
    
    def items(self):
        return self._data.items()
    
    # Tolerant fallback for any other attribute/method access
    def __getattr__(self, name: str) -> Any:
        # If it looks like a logger call (info, debug, warning, error), return a no-op
        if name in ['info', 'debug', 'warning', 'error', 'critical', 'exception']:
            return lambda *args, **kwargs: None
        # Otherwise, try to get from data
        if name in self._data:
            return self._data[name]
        # Default fallback
        return lambda *args, **kwargs: None
    
    def __setattr__(self, name: str, value: Any):
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            self._data[name] = value
