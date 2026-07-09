"""
llmXive Research Pipeline - Base Configuration and Seed Management.

This module provides a centralized configuration loader that handles:
- Environment variable overrides for all project settings
- Deterministic seed management for reproducibility
- Validation of critical configuration parameters
"""

import os
import random
from typing import Any, Dict, Optional, Set

import numpy as np


class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


class Config:
    """
    Centralized configuration manager for the cold-rolling texture project.

    Loads settings from environment variables with fallback to defaults.
    Supports deterministic seed management for reproducibility.
    """

    # Required configuration keys that MUST be present
    REQUIRED_KEYS: Set[str] = {
        'COLD_ROLLING_REDUCTIONS',  # Comma-separated list of reduction percentages
        'DATA_SOURCE_HF_ID',        # HuggingFace dataset ID
        'RANDOM_SEED',              # Seed for reproducibility
    }

    # Default values for optional configuration
    DEFAULTS: Dict[str, Any] = {
        'COLD_ROLLING_REDUCTIONS': '10,20,30,40,50,60,70',
        'DATA_SOURCE_HF_ID': 'llmXive/ebsd-fcc-metals',
        'RANDOM_SEED': '42',
        'LOG_LEVEL': 'INFO',
        'CONFIDENCE_THRESHOLD': '0.1',
        'MAX_WORKERS': '4',
    }

    def __init__(self):
        """Initialize configuration from environment variables and defaults."""
        self._values: Dict[str, str] = {}
        self._load_from_environment()
        self._validate_required()
        self._parse_numeric_fields()

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables, falling back to defaults."""
        for key, default in self.DEFAULTS.items():
            # Environment variables override defaults
            env_value = os.environ.get(key)
            self._values[key] = env_value if env_value is not None else default

    def _validate_required(self) -> None:
        """Ensure all required configuration keys are present and non-empty."""
        missing_keys = []
        for key in self.REQUIRED_KEYS:
            if key not in self._values or not self._values[key]:
                missing_keys.append(key)

        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration keys: {', '.join(missing_keys)}. "
                f"Please set the following environment variables or ensure defaults are valid."
            )

    def _parse_numeric_fields(self) -> None:
        """Parse numeric configuration fields into appropriate types."""
        # Parse cold rolling reductions as list of floats
        reductions_str = self._values.get('COLD_ROLLING_REDUCTIONS', '')
        try:
            self.reductions = [float(r.strip()) for r in reductions_str.split(',') if r.strip()]
            if not self.reductions:
                raise ConfigurationError(
                    "COLD_ROLLING_REDUCTIONS must contain at least one numeric value."
                )
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid format for COLD_ROLLING_REDUCTIONS: {e}"
            ) from e

        # Parse random seed as integer
        seed_str = self._values.get('RANDOM_SEED', '42')
        try:
            self.seed = int(seed_str)
        except ValueError:
            raise ConfigurationError(
                f"RANDOM_SEED must be a valid integer, got: {seed_str}"
            )

        # Parse confidence threshold as float
        conf_str = self._values.get('CONFIDENCE_THRESHOLD', '0.1')
        try:
            self.confidence_threshold = float(conf_str)
            if not 0.0 <= self.confidence_threshold <= 1.0:
                raise ConfigurationError(
                    f"CONFIDENCE_THRESHOLD must be between 0.0 and 1.0, got: {self.confidence_threshold}"
                )
        except ValueError as e:
            raise ConfigurationError(
                f"Invalid format for CONFIDENCE_THRESHOLD: {e}"
            ) from e

        # Parse log level
        self.log_level = self._values.get('LOG_LEVEL', 'INFO').upper()

        # Parse max workers
        workers_str = self._values.get('MAX_WORKERS', '4')
        try:
            self.max_workers = int(workers_str)
            if self.max_workers < 1:
                raise ConfigurationError(
                    f"MAX_WORKERS must be at least 1, got: {self.max_workers}"
                )
        except ValueError:
            raise ConfigurationError(
                f"MAX_WORKERS must be a valid integer, got: {workers_str}"
            )

    @property
    def data_source_hf_id(self) -> str:
        """Get the HuggingFace dataset ID."""
        return self._values.get('DATA_SOURCE_HF_ID', 'llmXive/ebsd-fcc-metals')

    def set_seed(self) -> None:
        """
        Set random seeds for reproducibility across all libraries.

        This ensures deterministic behavior for:
        - Python's random module
        - NumPy random operations
        - Any other seeded operations in the pipeline
        """
        random.seed(self.seed)
        np.random.seed(self.seed)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value by key.

        Args:
            key: Configuration key name
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._values.get(key, default)

    def __repr__(self) -> str:
        return (
            f"Config(seed={self.seed}, "
            f"reductions={self.reductions}, "
            f"confidence_threshold={self.confidence_threshold}, "
            f"hf_id={self.data_source_hf_id})"
        )


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get or create the global configuration instance.

    Returns:
        Global Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def initialize_seeds() -> None:
    """
    Initialize all random seeds for reproducibility.

    Call this function at the start of any script that requires
    deterministic behavior.
    """
    config = get_config()
    config.set_seed()


# Convenience accessors
reductions = property(lambda self: get_config().reductions)
seed = property(lambda self: get_config().seed)
confidence_threshold = property(lambda self: get_config().confidence_threshold)
data_source_hf_id = property(lambda self: get_config().data_source_hf_id)

# Module-level initialization
initialize_seeds()