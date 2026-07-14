"""
Configuration Module for the Microglial Morphology Project.

Centralizes all configuration parameters including paths, random seeds,
and constants for CPU-only execution.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def get_project_root() -> Path:
    """
    Get the project root directory.

    Assumes the project structure is:
    projects/PROJ-123-.../

    Returns:
        Path to the project root.
    """
    # Try to find the project root by looking for a known file
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / 'tasks.md').exists():
            return parent
    # Fallback to current directory
    return Path.cwd()


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.

    Args:
        config_path: Path to the config file. Defaults to config.yaml in project root.

    Returns:
        Dictionary containing configuration parameters.
    """
    if config_path is None:
        config_path = get_project_root() / 'config.yaml'

    if not config_path.exists():
        # Return default configuration
        return get_default_config()

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration parameters.

    Returns:
        Dictionary with default configuration values.
    """
    project_root = get_project_root()

    return {
        # Paths
        'project_root': str(project_root),
        'data_dir': str(project_root / 'data'),
        'raw_data_dir': str(project_root / 'data' / 'raw'),
        'processed_data_dir': str(project_root / 'data' / 'processed'),
        'intermediate_data_dir': str(project_root / 'data' / 'intermediates'),
        'figures_dir': str(project_root / 'figures'),
        'reports_dir': str(project_root / 'reports'),
        'specs_dir': str(project_root / 'specs'),

        # Random seeds for reproducibility
        'random_seed': 42,
        'numpy_seed': 42,
        'python_seed': 42,

        # Execution settings
        'cpu_only': True,
        'max_workers': 4,  # Conservative for CPU-only execution
        'memory_limit_gb': 8,

        # Image processing parameters
        'image_pixel_size_um': 0.325,  # Example: microns per pixel
        'denoise_strength': 1.0,
        'background_subtraction_radius': 50,

        # Morphology analysis parameters
        'sholl_radius_start': 0,
        'sholl_radius_step': 5,  # microns
        'sholl_radius_end': 100,
        'branch_point_threshold': 3,  # pixels

        # Statistical analysis parameters
        'p_value_threshold': 0.05,
        'vif_threshold': 5.0,

        # Logging
        'log_level': 'INFO',
        'log_to_file': True,
    }


# Global configuration instance
CONFIG = load_config()


def get_path(key: str) -> Path:
    """
    Get a configuration path as a Path object.

    Args:
        key: Configuration key for the path (e.g., 'raw_data_dir').

    Returns:
        Path object for the configured directory.
    """
    path_str = CONFIG.get(key, '')
    return Path(path_str)


def ensure_dirs() -> None:
    """
    Ensure all configured directories exist.
    """
    dirs = [
        'data_dir',
        'raw_data_dir',
        'processed_data_dir',
        'intermediate_data_dir',
        'figures_dir',
        'reports_dir',
    ]

    for dir_key in dirs:
        dir_path = get_path(dir_key)
        dir_path.mkdir(parents=True, exist_ok=True)
