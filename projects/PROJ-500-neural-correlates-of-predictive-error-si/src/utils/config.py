"""
Configuration management module.
Provides singleton configuration for paths, seeds, and parameters.
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

# Singleton instance
_config_instance: Optional[Dict[str, Any]] = None


def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Get the configuration singleton, loading from file if provided.

    Args:
        config_path: Optional path to a YAML configuration file

    Returns:
        Configuration dictionary
    """
    global _config_instance

    if _config_instance is not None and config_path is None:
        return _config_instance

    # Default configuration
    default_config = {
        # Paths
        'project_root': str(Path(__file__).parent.parent.parent),
        'data_dir': str(Path(__file__).parent.parent.parent / 'data'),
        'output_dir': str(Path(__file__).parent.parent.parent / 'data' / 'processed'),
        'logs_dir': str(Path(__file__).parent.parent.parent / 'logs'),
        'figures_dir': str(Path(__file__).parent.parent.parent / 'figures'),

        # Random seeds
        'random_seed': 42,
        'numpy_seed': 42,

        # Signal processing parameters
        'low_frequency_cutoff': 1.0,  # Hz
        'high_frequency_cutoff': 40.0,  # Hz
        'epoch_pre_time': -0.250,  # seconds (baseline window)
        'epoch_post_time': 0.500,  # seconds
        'ica_components': 0.99,  # Variance explained for ICA

        # Artifact rejection
        'max_trial_loss_percent': 5.0,
        'underpowered_subject_threshold': 20,

        # MMN analysis parameters
        'mmn_time_window_start': -0.250,  # seconds
        'mmn_time_window_end': 0.0,  # seconds
        'mmn_electrodes': ['CP3', 'CP4', 'C3', 'C4'],

        # Statistical modeling
        'permutation_n': 1000,
        'fdr_alpha': 0.05,
    }

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                default_config.update(file_config)

    _config_instance = default_config
    return _config_instance


def reset_config():
    """Reset the configuration singleton (useful for testing)."""
    global _config_instance
    _config_instance = None


def save_config(config_path: str, config: Optional[Dict[str, Any]] = None):
    """
    Save current configuration to a YAML file.

    Args:
        config_path: Path to save the configuration
        config: Optional configuration dictionary (uses current if None)
    """
    if config is None:
        config = get_config()

    Path(config_path).parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)


def get_path(key: str) -> Path:
    """
    Get a configuration value as a Path object.

    Args:
        key: Configuration key

    Returns:
        Path object for the configuration value
    """
    config = get_config()
    value = config.get(key, '')
    return Path(value)
