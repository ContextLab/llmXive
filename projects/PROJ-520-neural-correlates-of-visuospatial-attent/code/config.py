"""
Configuration management for the neural correlates pipeline.

This module handles loading configuration from YAML files, managing file paths,
and providing environment-specific settings.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from pathlib import Path as PathLib

# Avoid circular imports by not importing ci_limits here
# Instead, define environment checks locally if needed

def get_cpu_count() -> int:
    """Get the number of available CPU cores."""
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1

def get_memory_limit_gb() -> float:
    """Get the memory limit in GB based on environment."""
    # Default to 7GB for CI limits
    return 7.0

def get_environment_report() -> Dict[str, Any]:
    """Get a report of the current environment."""
    return {
        'cpu_count': get_cpu_count(),
        'memory_limit_gb': get_memory_limit_gb(),
        'platform': sys.platform
    }

def deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_default_config() -> Dict[str, Any]:
    """Get the default configuration."""
    return {
        'random_seed': 42,
        'paths': {
            'raw_data': 'data/raw',
            'processed_data': 'data/processed',
            'results': 'results',
            'figures': 'figures'
        },
        'processing': {
            'bandpass_filter': {'low': 1, 'high': 40},
            'notch_filter': {'freqs': [50, 60]},
            'epoch_length': 2.0,
            'baseline_window': [-1.0, 0.0]
        },
        'features': {
            'alpha_band': {'low': 8, 'high': 12},
            'beta_band': {'low': 13, 'high': 30},
            'alpha_electrodes': ['P3', 'Pz', 'P4'],
            'beta_electrodes': ['F3', 'Fz', 'F4']
        },
        'classification': {
            'n_folds': 5,
            'n_permutations': 1000
        }
    }

def get_env_config() -> Dict[str, Any]:
    """Get environment-specific overrides."""
    # Check for environment variable overrides
    config_overrides = {}
    
    if os.getenv('CI', 'false').lower() == 'true':
        config_overrides = {
            'processing': {
                'n_jobs': min(2, get_cpu_count())
            }
        }
    
    return config_overrides

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or use defaults.
    
    Args:
        config_path: Optional path to configuration file. If None, uses default config.
    
    Returns:
        Merged configuration dictionary
    """
    config = get_default_config()
    env_config = get_env_config()
    config = deep_merge(config, env_config)
    
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
            config = deep_merge(config, file_config)
    
    return config

def get_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """Get the random seed from configuration."""
    if config is None:
        config = load_config()
    return config.get('random_seed', 42)

def get_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """
    Get paths for data and results directories.
    
    Args:
        config: Optional configuration dictionary. If None, loads default config.
    
    Returns:
        Dictionary of Path objects for various directories
    """
    if config is None:
        config = load_config()
    
    path_config = config.get('paths', {})
    
    # Define base paths
    base = PathLib.cwd()
    
    paths = {
        'raw_data': base / path_config.get('raw_data', 'data/raw'),
        'processed_data': base / path_config.get('processed_data', 'data/processed'),
        'results': base / path_config.get('results', 'results'),
        'figures': base / path_config.get('figures', 'figures'),
        'config_file': base / 'config.yaml',
        # Specific file paths
        'raw_epochs': base / path_config.get('raw_data', 'data/raw') / 'raw_epochs.fif',
        'processed_epochs': base / path_config.get('processed_data', 'data/processed') / 'epochs_cleaned.fif',
        'tf_power': base / path_config.get('processed_data', 'data/processed') / 'tf_power.npy',
        'features_matrix': base / path_config.get('processed_data', 'data/processed') / 'features_matrix.csv',
        'feature_metadata': base / path_config.get('processed_data', 'data/processed') / 'feature_metadata.json',
        't_test_results': base / path_config.get('processed_data', 'data/processed') / 't_test_results.json',
        'sensitivity_analysis': base / path_config.get('processed_data', 'data/processed') / 'sensitivity_analysis.csv',
        'final_results': base / 'results.json'
    }
    
    return paths

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """Create all necessary directories if they don't exist."""
    paths = get_paths(config)
    for path in paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)

def main():
    """Main function to print configuration."""
    config = load_config()
    paths = get_paths(config)
    
    print("Configuration loaded successfully")
    print(f"Random seed: {config.get('random_seed')}")
    print("Paths:")
    for key, path in paths.items():
        print(f"  {key}: {path}")

if __name__ == "__main__":
    main()
