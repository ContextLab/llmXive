"""
Configuration management for the pipeline.
Handles loading YAML configs, merging defaults, and retrieving seeds/paths.
Updated to include CI environment limits integration.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

# Import CI limits module to integrate environment constraints
from ci_limits import get_environment_report

CONFIG_PATH = Path("code/config.yaml")

DEFAULTS = {
    "random_seed": 42,
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "logs": "logs",
        "figures": "figures"
    },
    "processing": {
        "cpu_limit": None,  # Will be overridden by CI detection
        "ram_limit_gb": None
    }
}

def deep_merge(base: Dict, override: Dict) -> Dict:
    """
    Recursively merge override dict into base dict.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file and merge with defaults.
    Integrates CI environment limits if not explicitly set in config.
    """
    path = config_path or CONFIG_PATH
    config = DEFAULTS.copy()
    
    if path.exists():
        with open(path, 'r') as f:
            user_config = yaml.safe_load(f) or {}
            config = deep_merge(config, user_config)
    
    # If CPU/RAM limits are not set in config, detect from environment
    if config["processing"]["cpu_limit"] is None:
        env_report = get_environment_report()
        config["processing"]["cpu_limit"] = env_report["cpu_limit"]
        config["processing"]["ram_limit_gb"] = env_report["ram_limit_gb"]
    
    return config

def get_seed(config: Dict[str, Any]) -> int:
    """
    Extract random seed from config.
    """
    return config.get("random_seed", DEFAULTS["random_seed"])

def get_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """
    Extract and resolve paths from config.
    """
    raw_paths = config.get("paths", DEFAULTS["paths"])
    return {k: Path(v) for k, v in raw_paths.items()}

def main():
    """
    CLI to dump current configuration.
    """
    import json
    config = load_config()
    # Convert Path objects to strings for JSON serialization
    serializable_config = {}
    for k, v in config.items():
        if isinstance(v, dict):
            serializable_config[k] = {kk: str(vv) if isinstance(vv, Path) else vv for kk, vv in v.items()}
        elif isinstance(v, Path):
            serializable_config[k] = str(v)
        else:
            serializable_config[k] = v
    
    print(json.dumps(serializable_config, indent=2))

if __name__ == "__main__":
    main()
