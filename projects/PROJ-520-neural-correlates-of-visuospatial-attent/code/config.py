import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from pathlib import Path as PathLib

# Default configuration
DEFAULT_CONFIG = {
    'SEED': 42,
    'DATA_PATH': 'data/raw',
    'OUTPUT_PATH': 'data/processed',
    'RAM_LIMIT_GB': 7.0,
    'CPU_LIMIT': 2,
    'BENCHMARK_ACCURACY': 0.65
}

def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables."""
    config = get_default_config()
    
    if 'SEED' in os.environ:
        config['SEED'] = int(os.environ['SEED'])
    if 'DATA_PATH' in os.environ:
        config['DATA_PATH'] = os.environ['DATA_PATH']
    if 'OUTPUT_PATH' in os.environ:
        config['OUTPUT_PATH'] = os.environ['OUTPUT_PATH']
    if 'RAM_LIMIT_GB' in os.environ:
        config['RAM_LIMIT_GB'] = float(os.environ['RAM_LIMIT_GB'])
    if 'CPU_LIMIT' in os.environ:
        config['CPU_LIMIT'] = int(os.environ['CPU_LIMIT'])
    if 'BENCHMARK_ACCURACY' in os.environ:
        config['BENCHMARK_ACCURACY'] = float(os.environ['BENCHMARK_ACCURACY'])
        
    return config

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file or use defaults.
    
    Args:
        config_path: Path to YAML config file. If None, uses defaults + env vars.
        
    Returns:
        Configuration dictionary
    """
    config = get_default_config()
    
    # Override with environment variables
    env_config = get_env_config()
    config = deep_merge(config, env_config)
    
    # Override with file if provided
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                config = deep_merge(config, file_config)
                
    return config

def get_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """Get the random seed from configuration."""
    if config is None:
        config = load_config()
    return config.get('SEED', 42)

def get_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """Get data paths from configuration.
    
    Returns:
        Dictionary with 'raw' and 'processed' Path objects
    """
    if config is None:
        config = load_config()
        
    return {
        'raw': Path(config['DATA_PATH']),
        'processed': Path(config['OUTPUT_PATH'])
    }

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """Ensure all required directories exist."""
    paths = get_paths(config)
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

def main():
    """Main entry point for standalone execution."""
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    config = load_config()
    logger.info(f"Configuration: {config}")
    
    paths = get_paths(config)
    logger.info(f"Data paths: {paths}")
    
    ensure_directories(config)
    logger.info("Directories ensured")

if __name__ == "__main__":
    main()
