"""
Configuration management for the project.
Provides default values for seeds, paths, and constants.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values
DEFAULT_CONFIG = {
    'seed': 42,
    'window_size': 30,
    'step_size': 10,
    'atlas': 'Schaefer100',
    'deviation_flag': True,  # Flag for Schaefer-100 deviation (T005)
    'memory_limit_gb': 7,
    'max_runtime_hours': 4,
    'data_dir': 'data',
    'results_dir': 'results',
    'code_dir': 'code',
    'temp_dir': 'data/intermediate',
    'fd_threshold': 0.5,
    'ica_aroma_flags': ['--afni', '--no-reports'],
    'n_permutations': 1000
}

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables or return defaults.
    
    Returns:
        Dictionary containing configuration values.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if present
    for key in config:
        env_key = f"LLMXIVE_{key.upper()}"
        if env_key in os.environ:
            value = os.environ[env_key]
            # Try to convert to appropriate type
            if isinstance(config[key], bool):
                config[key] = value.lower() in ('true', '1', 'yes')
            elif isinstance(config[key], int):
                config[key] = int(value)
            elif isinstance(config[key], float):
                config[key] = float(value)
            else:
                config[key] = value
    
    return config

def ensure_directories():
    """
    Create required directory structures if they don't exist.
    """
    config = get_config()
    directories = [
        config['data_dir'],
        config['results_dir'],
        config['code_dir'],
        config['temp_dir'],
        'data/raw',
        'data/processed',
        'data/metrics',
        'data/atlas',
        'results/plots',
        'tests',
        'contracts',
        'docs'
    ]
    
    for dir_path in directories:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        os.chmod(dir_path, 0o755)

if __name__ == '__main__':
    # Test configuration loading
    config = get_config()
    print("Loaded configuration:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Ensure directories exist
    ensure_directories()
    print("\nDirectories created/verified.")