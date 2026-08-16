"""
Configuration management module.
Handles loading of YAML config, seeds, and paths.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from ci_limits import get_environment_report

DEFAULT_CONFIG = {
    "random_seed": 42,
    "paths": {
        "raw": "data/raw",
        "processed": "data/processed",
        "epochs": "epochs_cleaned.fif",
        "features": "features_matrix.csv",
        "results": "results.json"
    },
    "preprocessing": {
        "l_freq": 1.0,
        "h_freq": 40.0,
        "notch_freq": 50.0,
        "ica_n_components": 0.95
    },
    "epoching": {
        "tmin": -1.0,
        "tmax": 1.0,
        "baseline": (None, 0)
    },
    "feature_extraction": {
        "fmin": 1.0,
        "fmax": 40.0,
        "n_freqs": 20
    },
    "classification": {
        "n_folds": 5,
        "n_permutations": 100
    }
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

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from YAML file or return defaults."""
    if config_path is None:
        # Try common locations
        possible_paths = [
            Path("config.yaml"),
            Path("config.yml"),
            Path("specs") / "001-neural-correlates-of-visuospatial-attent" / "config.yaml"
        ]
        for p in possible_paths:
            if p.exists():
                config_path = p
                break
    
    config = DEFAULT_CONFIG.copy()
    
    if config_path and config_path.exists():
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            if user_config:
                config = deep_merge(config, user_config)
    
    # Ensure paths are Path objects
    if "paths" in config:
        for k, v in config["paths"].items():
            if isinstance(v, str):
                config["paths"][k] = Path(v)
    
    return config

def get_seed(config: Dict[str, Any]) -> int:
    """Get random seed from config."""
    return config.get("random_seed", 42)

def get_paths(config: Dict[str, Any]) -> Dict[str, Path]:
    """Get path dictionary from config."""
    paths = config.get("paths", {})
    # Ensure root paths are absolute relative to project root if needed
    # For now, assume they are relative to CWD
    return paths

def main():
    """CLI entry point for config validation."""
    config = load_config()
    print("Configuration loaded successfully:")
    print(f"  Seed: {config['random_seed']}")
    print(f"  Paths: {config['paths']}")
    env_report = get_environment_report()
    print(f"  Environment: {env_report}")

if __name__ == "__main__":
    main()
