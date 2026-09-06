import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from config import ensure_dirs

# Global configuration cache
_config_cache: Dict[str, Any] = {}
_env_loaded: bool = False

def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, defaults to project root .env.
    
    Returns:
        Dictionary of loaded environment variables.
    """
    global _env_loaded
    if _env_loaded:
        return os.environ.copy()
    
    if env_path is None:
        env_path = Path.cwd() / ".env"
    else:
        env_path = Path(env_path)
    
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        _env_loaded = True
        return {k: v for k, v in os.environ.items() if v is not None}
    else:
        # If .env doesn't exist, return empty dict but don't crash
        # The project will rely on defaults in config.yaml
        _env_loaded = True
        return {}

def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, defaults to project root.
    
    Returns:
        Dictionary of configuration values.
    """
    if config_path is None:
        config_path = Path.cwd() / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def merge_configs(env_vars: Dict[str, str], yaml_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge environment variables into YAML config.
    Environment variables take precedence for top-level keys.
    
    Args:
        env_vars: Dictionary of environment variables.
        yaml_config: Dictionary from YAML config file.
    
    Returns:
        Merged configuration dictionary.
    """
    merged = yaml_config.copy()
    
    # Map common env vars to config keys
    env_mapping = {
        'DATA_RAW_PATH': 'paths.data_raw',
        'DATA_PROCESSED_PATH': 'paths.data_processed',
        'RESULTS_PATH': 'paths.results',
        'LOGS_PATH': 'paths.logs',
        'ANALYSIS_SEED': 'defaults.analysis_seed',
        'ALPHA_LEVEL': 'defaults.alpha_level',
        'BOOTSTRAP_COUNT': 'defaults.bootstrap_count',
    }
    
    for env_key, config_path in env_mapping.items():
        if env_key in env_vars:
            value = env_vars[env_key]
            # Convert to appropriate type
            if config_path.endswith('_seed') or config_path.endswith('_count'):
                try:
                    value = int(value)
                except ValueError:
                    pass
            elif config_path.endswith('_level'):
                try:
                    value = float(value)
                except ValueError:
                    pass
            
            # Navigate and set in merged dict
            keys = config_path.split('.')
            current = merged
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]
            current[keys[-1]] = value
    
    return merged

def get_config() -> Dict[str, Any]:
    """
    Get the full merged configuration.
    
    Returns:
        Merged configuration dictionary.
    """
    if _config_cache:
        return _config_cache.copy()
    
    env_vars = load_env_file()
    yaml_config = load_config_file()
    merged = merge_configs(env_vars, yaml_config)
    
    _config_cache.update(merged)
    return _config_cache.copy()

def get_path(key: str, default: Optional[str] = None) -> Path:
    """
    Get a path value from configuration.
    
    Args:
        key: Dot-notation key (e.g., 'paths.data_raw').
        default: Default value if key not found.
    
    Returns:
        Path object.
    """
    config = get_config()
    keys = key.split('.')
    current = config
    
    try:
        for k in keys:
            current = current[k]
    except (KeyError, TypeError):
        if default is not None:
            current = default
        else:
            raise KeyError(f"Configuration key not found: {key}")
    
    return Path(current)

def get_data_raw_path() -> Path:
    """Get the raw data directory path."""
    return get_path('paths.data_raw', 'data/raw')

def get_data_processed_path() -> Path:
    """Get the processed data directory path."""
    return get_path('paths.data_processed', 'data/processed')

def get_results_path() -> Path:
    """Get the results directory path."""
    return get_path('paths.results', 'results')

def get_logs_path() -> Path:
    """Get the logs directory path."""
    return get_path('paths.logs', 'logs')

def get_analysis_seed() -> int:
    """Get the analysis random seed."""
    seed = get_path('defaults.analysis_seed', 42)
    return int(seed)

def get_alpha_level() -> float:
    """Get the significance alpha level."""
    alpha = get_path('defaults.alpha_level', 0.05)
    return float(alpha)

def get_bootstrap_count() -> int:
    """Get the number of bootstrap iterations."""
    count = get_path('defaults.bootstrap_count', 1000)
    return int(count)

def create_sample_env_file(output_path: Optional[str] = None) -> None:
    """
    Create a sample .env file with default values.
    
    Args:
        output_path: Path to write the .env file. Defaults to project root.
    """
    if output_path is None:
        output_path = Path.cwd() / ".env"
    else:
        output_path = Path(output_path)
    
    content = """# Environment Configuration for Political News Exposure Study
# Copy this file to .env and modify as needed

# Data Paths (relative to project root or absolute)
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed
RESULTS_PATH=results
LOGS_PATH=logs

# Analysis Parameters
ANALYSIS_SEED=42
ALPHA_LEVEL=0.05
BOOTSTRAP_COUNT=1000
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

def create_sample_config_file(output_path: Optional[str] = None) -> None:
    """
    Create a sample config.yaml file with default values.
    
    Args:
        output_path: Path to write the config.yaml file. Defaults to project root.
    """
    if output_path is None:
        output_path = Path.cwd() / "config.yaml"
    else:
        output_path = Path(output_path)
    
    content = """# Configuration for Political News Exposure Study
# Values can be overridden by .env file

paths:
  data_raw: data/raw
  data_processed: data/processed
  results: results
  logs: logs

defaults:
  analysis_seed: 42
  alpha_level: 0.05
  bootstrap_count: 1000

logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

schema_validation:
  strict_mode: true
  required_columns:
    - IAT_D_score
    - political_ideology
    - news_exposure_freq
"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)