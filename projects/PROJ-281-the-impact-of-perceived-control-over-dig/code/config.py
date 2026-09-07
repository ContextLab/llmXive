"""
Global configuration, random seeds, and path constants.

This module provides centralized configuration management for the project,
including path definitions, random seed management, and runtime parameters.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any
import numpy as np
import json

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data directories
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"

# Create directories if they don't exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Configuration schema file path
CONFIG_SCHEMA_PATH = PROJECT_ROOT / "contracts" / "analysis.schema.yaml"

# Runtime limits
RUNTIME_LIMIT_HOURS = 6

# Default configuration values
DEFAULT_CONFIG = {
    "filtering": {
        "entropy_threshold": 0.7,
        "min_text_length": 3
    },
    "model_mapping": {
        "fear_to_anxiety": False
    },
    "weights": {
        "weight_filter": 0.5,
        "weight_regularity": 0.5
    },
    "confidence_threshold": 0.6,
    "correlation_significance_threshold": 0.05
}

# Global random seed state
_current_seed = None

class Config:
    """Configuration manager with lazy loading and seed management."""
    
    def __init__(self):
        self._config = None
        self.PROJECT_ROOT = PROJECT_ROOT
        self.RAW_DATA_DIR = RAW_DATA_DIR
        self.PROCESSED_DIR = PROCESSED_DATA_DIR
        self.FIGURES_DIR = FIGURES_DIR
        self.RUNTIME_LIMIT_HOURS = RUNTIME_LIMIT_HOURS
        self.CONFIG_SCHEMA_PATH = CONFIG_SCHEMA_PATH
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from schema file or use defaults."""
        if self._config is not None:
            return self._config
        
        # Try to load from schema file
        if self.CONFIG_SCHEMA_PATH.exists():
            try:
                import yaml
                with open(self.CONFIG_SCHEMA_PATH, 'r') as f:
                    loaded_config = yaml.safe_load(f)
                    # Merge with defaults
                    self._config = self._deep_merge(DEFAULT_CONFIG, loaded_config)
            except ImportError:
                # Fallback if PyYAML not available
                self._config = DEFAULT_CONFIG.copy()
            except Exception as e:
                print(f"Warning: Could not load config from {self.CONFIG_SCHEMA_PATH}: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
        
        return self._config
    
    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated path."""
        config = self._load_config()
        keys = key_path.split('.')
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set_seed(self, seed: int) -> None:
        """Set random seeds for reproducibility."""
        global _current_seed
        _current_seed = seed
        random.seed(seed)
        np.random.seed(seed)
        # If available, set torch seed
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass
    
    def reset_seeds(self) -> None:
        """Reset random seeds to initial state."""
        global _current_seed
        _current_seed = None
        # Reset to a known state (or let them be random)
        random.seed()
        np.random.seed()
        try:
            import torch
            torch.seed()
        except ImportError:
            pass

# Create global config instance
CONFIG = Config()

# Convenience functions for seed management
def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    CONFIG.set_seed(seed)

def reset_seeds() -> None:
    """Reset random seeds to initial state."""
    CONFIG.reset_seeds()

def get_seed() -> Optional[int]:
    """Get current seed value."""
    return _current_seed

def load_config_params() -> Dict[str, Any]:
    """Load configuration parameters for analysis."""
    return CONFIG._load_config()

def get_config_value(key_path: str, default: Any = None) -> Any:
    """Get configuration value by dot-separated path."""
    return CONFIG.get(key_path, default)