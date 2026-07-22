"""
Configuration management module for the corrosion potential prediction pipeline.
Handles random seeds, file paths, and environment configuration.
"""

import os
import random
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

from utils.logging import get_logger
from utils.exceptions import CorrosionPipelineError

logger = get_logger(__name__)

@dataclass
class ProjectConfig:
    """Holds all project-wide configuration settings."""
    random_seeds: Dict[str, int] = field(default_factory=dict)
    file_paths: Dict[str, str] = field(default_factory=dict)
    data_sources: Dict[str, Any] = field(default_factory=dict)
    processing: Dict[str, Any] = field(default_factory=dict)
    model_training: Dict[str, Any] = field(default_factory=dict)
    validation: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Set defaults if not provided
        if not self.random_seeds:
            self.random_seeds = {
                'global_seed': 42,
                'train_test_split_seed': 42,
                'model_training_seed': 42,
                'permutation_test_seed': 42
            }
        if not self.file_paths:
            self.file_paths = {
                'raw_data_dir': 'data/raw',
                'processed_data_dir': 'data/processed',
                'log_dir': 'data/logs',
                'state_dir': 'state',
                'figures_dir': 'figures',
                'processed_dataset_path': 'data/processed/corrosion_dataset.parquet',
                'model_results_path': 'data/processed/model_results.json',
                'pipeline_log_path': 'data/logs/pipeline.log'
            }

class ConfigManager:
    """Manages loading, saving, and accessing project configuration."""

    _instance: Optional['ConfigManager'] = None
    _config: Optional[ProjectConfig] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._load_config()

    @classmethod
    def _load_config(cls, config_path: Optional[str] = None) -> ProjectConfig:
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = "config/pipeline_config.yaml"

        config_path = Path(config_path)

        if not config_path.exists():
            raise CorrosionPipelineError(
                f"Configuration file not found: {config_path}. "
                "Please ensure config/pipeline_config.yaml exists."
            )

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            return ProjectConfig(
                random_seeds=config_data.get('random_seeds', {}),
                file_paths=config_data.get('file_paths', {}),
                data_sources=config_data.get('data_sources', {}),
                processing=config_data.get('processing', {}),
                model_training=config_data.get('model_training', {}),
                validation=config_data.get('validation', {})
            )
        except yaml.YAMLError as e:
            raise CorrosionPipelineError(f"Failed to parse config file: {e}")

    def get_config(self) -> ProjectConfig:
        """Return the current configuration."""
        return self._config

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values."""
        for key, value in updates.items():
            if hasattr(self._config, key):
                current = getattr(self._config, key)
                if isinstance(current, dict) and isinstance(value, dict):
                    current.update(value)
                else:
                    setattr(self._config, key, value)
        logger.info(f"Configuration updated: {list(updates.keys())}")

    def save_config(self, output_path: Optional[str] = None):
        """Save current configuration to YAML file."""
        if output_path is None:
            output_path = "config/pipeline_config.yaml"

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        config_dict = {
            'random_seeds': self._config.random_seeds,
            'file_paths': self._config.file_paths,
            'data_sources': self._config.data_sources,
            'processing': self._config.processing,
            'model_training': self._config.model_training,
            'validation': self._config.validation
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)

        logger.info(f"Configuration saved to {output_path}")

# Global config manager instance
_config_manager = None

def get_config() -> ProjectConfig:
    """Get the global configuration instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.get_config()

def set_random_seed(seed: Optional[int] = None, seed_name: str = 'global_seed') -> int:
    """
    Set random seed for reproducibility.

    Args:
        seed: The seed value. If None, uses the value from config.
        seed_name: The name of the seed in config (default: 'global_seed')

    Returns:
        The seed value that was set.
    """
    config = get_config()

    if seed is None:
        seed = config.random_seeds.get(seed_name, 42)

    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

    logger.info(f"Random seed set to {seed} ({seed_name})")
    return seed

def get_path(key: str) -> Path:
    """
    Get a file path from configuration.

    Args:
        key: The key in file_paths configuration

    Returns:
        Path object for the configured path
    """
    config = get_config()
    path_str = config.file_paths.get(key)

    if path_str is None:
        raise CorrosionPipelineError(f"Path key not found in config: {key}")

    return Path(path_str)

def get_data_path() -> Path:
    """Get the raw data directory path."""
    return get_path('raw_data_dir')

def get_processed_data_path() -> Path:
    """Get the processed data directory path."""
    return get_path('processed_data_dir')

def get_log_path() -> Path:
    """Get the log directory path."""
    return get_path('log_dir')

def save_config(output_path: Optional[str] = None):
    """Save configuration to file."""
    ConfigManager().save_config(output_path)

def update_config(updates: Dict[str, Any]):
    """Update configuration values."""
    ConfigManager().update_config(updates)

# Convenience functions for common paths
def get_processed_dataset_path() -> Path:
    """Get the path to the processed dataset."""
    return get_path('processed_dataset_path')

def get_model_results_path() -> Path:
    """Get the path to model results."""
    return get_path('model_results_path')

def get_pipeline_log_path() -> Path:
    """Get the path to the pipeline log."""
    return get_path('pipeline_log_path')

def get_split_indices_path() -> Path:
    """Get the path to split indices."""
    return get_path('split_indices_path')

def get_split_validation_path() -> Path:
    """Get the path to split validation results."""
    return get_path('split_validation_path')

def get_diagnostics_path() -> Path:
    """Get the diagnostics directory path."""
    return get_path('diagnostics_path')

def get_count_report_path() -> Path:
    """Get the count report file path."""
    return get_path('count_report_path')

def get_figures_path() -> Path:
    """Get the figures directory path."""
    return get_path('figures_dir')

def get_interpretability_path() -> Path:
    """Get the interpretability results directory path."""
    return get_path('interpretability_dir')

def get_astm_tolerance_config_path() -> Path:
    """Get the ASTM G59 tolerance configuration path."""
    return get_path('astm_tolerance_config')

def get_verified_datasets_config_path() -> Path:
    """Get the verified datasets configuration path."""
    return get_path('verified_datasets_config')
