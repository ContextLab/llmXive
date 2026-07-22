"""
Configuration management for llmXive project.

All configuration is defined here to ensure a single source of truth.
"""

import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional
import yaml


class Config:
    """Centralized configuration class."""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration.

        Args:
            config_path: Optional path to YAML config file (not used per constraints)
        """
        # Project root
        self.project_root = Path(__file__).resolve().parent.parent

        # Random seed for reproducibility
        self.seed = 42

        # Paths
        self.paths = {
            'raw': self.project_root / 'data' / 'raw',
            'training': self.project_root / 'data' / 'training',
            'held_out': self.project_root / 'data' / 'held_out',
            'processed': self.project_root / 'data' / 'processed',
            'processed_rules': self.project_root / 'data' / 'processed' / 'rules',
            'figures': self.project_root / 'figures',
            'contracts': self.project_root / 'contracts',
        }

        # Thresholds and parameters
        self.thresholds = {
            'fidelity': 0.9,
            'min_support': 0.1,
            'max_depth': 10,
        }

        # Sweep configuration for T027a
        self.sweep = {
            'method': 'min_support',
            'thresholds': [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        }

        # Model parameters
        self.model = {
            'max_depth': 10,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
        }

        # Embedding model
        self.embedding_model = 'sentence-transformers/all-MiniLM-L6-v2'

        # Ensure directories exist
        self._ensure_directories()

    def _ensure_directories(self):
        """Create all required directories."""
        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key."""
        keys = key.split('.')
        value = self
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            elif hasattr(value, k):
                value = getattr(value, k)
            else:
                return default
        return value


_config_instance: Optional[Config] = None


def get_config() -> Dict[str, Any]:
    """
    Get configuration as a dictionary.

    Returns:
        Configuration dictionary
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()

    # Convert to dictionary for compatibility
    return {
        'seed': _config_instance.seed,
        'paths': {
            'raw': str(_config_instance.paths['raw']),
            'training': str(_config_instance.paths['training']),
            'held_out': str(_config_instance.paths['held_out']),
            'processed': str(_config_instance.paths['processed']),
            'processed_rules': str(_config_instance.paths['processed_rules']),
            'figures': str(_config_instance.paths['figures']),
            'contracts': str(_config_instance.paths['contracts']),
        },
        'thresholds': _config_instance.thresholds,
        'sweep': _config_instance.sweep,
        'model': _config_instance.model,
        'embedding_model': _config_instance.embedding_model,
    }
