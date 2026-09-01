"""
Configuration management for the pipeline.
Handles loading config files, merging defaults, and environment overrides.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from pathlib import Path as PathLib

# Delayed import to avoid circular dependency with ci_limits
# We only need ci_limits for environment reporting, which can be done lazily.
# However, get_cpu_count and get_memory_limit_gb are needed for defaults.
# To break the cycle: ci_limits.py no longer imports config.
# config.py imports ci_limits for helper functions.
# This is safe now because ci_limits does not depend on config.
from ci_limits import get_cpu_count, get_memory_limit_gb, get_environment_report

logger = __import__('logging').getLogger(__name__)

DEFAULT_CONFIG = {
    "random_seed": 42,
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "code": "code",
        "results": "results"
    },
    "processing": {
        "filter_low": 1.0,
        "filter_high": 40.0,
        "notch_freq": [50.0, 60.0],
        "epoch_duration": 2.0,
        "min_epochs_per_condition": 100
    },
    "limits": {
        "max_cpu": get_cpu_count(),
        "max_memory_gb": get_memory_limit_gb()
    }
}

def deep_merge(base: Dict, override: Dict) -> Dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG

def get_env_config() -> Dict[str, Any]:
    """Return configuration derived from environment variables."""
    env_config = {}
    # Example: Override paths or limits via env vars
    if "DATA_RAW_PATH" in os.environ:
        env_config.setdefault("paths", {})["data_raw"] = os.environ["DATA_RAW_PATH"]
    if "DATA_PROCESSED_PATH" in os.environ:
        env_config.setdefault("paths", {})["data_processed"] = os.environ["DATA_PROCESSED_PATH"]
    return env_config

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file, merging with defaults and env overrides.
    """
    config = get_default_config()
    env_config = get_env_config()
    config = deep_merge(config, env_config)

    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config = deep_merge(config, file_config)
        except Exception as e:
            logger.warning(f"Could not load config file {config_path}: {e}")

    return config

def get_seed(config: Optional[Dict[str, Any]] = None) -> int:
    """Extract random seed from config."""
    if config is None:
        config = load_config()
    return config.get("random_seed", 42)

def get_paths(config: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """
    Return Path objects for all configured directories.
    Ensures paths are absolute relative to project root.
    """
    if config is None:
        config = load_config()

    paths_dict = config.get("paths", {})
    project_root = Path.cwd()
    
    result = {}
    for key, path_str in paths_dict.items():
        # Resolve relative to project root
        full_path = project_root / path_str
        result[key] = full_path
        
        # Ensure directory exists
        full_path.mkdir(parents=True, exist_ok=True)

    return result

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> None:
    """Create all directories defined in config."""
    paths = get_paths(config)
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

def main():
    """CLI entry point for configuration inspection."""
    cfg = load_config()
    print(f"Loaded Config:\n{cfg}")
    env_report = get_environment_report()
    print(f"Environment Report:\n{env_report}")

if __name__ == "__main__":
    main()
