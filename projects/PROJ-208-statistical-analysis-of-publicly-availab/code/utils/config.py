"""
Configuration manager for the statistical analysis project.
Handles random seeds, paths, and thresholds for reproducible research.
"""

import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import yaml


# Default configuration values
DEFAULT_CONFIG: Dict[str, Any] = {
    "random_seeds": {
        "global_seed": 42,
        "numpy_seed": 42,
        "python_seed": 42,
    },
    "paths": {
        "project_root": "code/../../",
        "data_raw": "data/raw/",
        "data_processed": "data/processed/",
        "data_figures": "data/figures/",
        "data_logs": "data/logs/",
        "state": "state/",
        "code": "code/",
        "tests": "tests/",
    },
    "thresholds": {
        "dataset_completeness": 0.95,
        "repository_minimum": 100,
        "outlier_threshold_days": 30,
        "collinearity_vif": 5,
        "coverage_minimum": 0.80,
    },
    "api": {
        "rate_limit_delay": 1.0,
        "max_retries": 3,
        "timeout_seconds": 30,
    },
}


class Config:
    """Central configuration manager for the project."""

    _instance: Optional["Config"] = None

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize configuration with defaults or provided values."""
        self.config = config if config else DEFAULT_CONFIG.copy()
        self._resolve_paths()

    @classmethod
    def get_instance(cls) -> "Config":
        """Get or create the global configuration instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """Reset the configuration instance (useful for testing)."""
        cls._instance = None

    def _resolve_paths(self) -> None:
        """Resolve relative paths to absolute Path objects."""
        project_root = Path(self.config["paths"]["project_root"])
        if not project_root.is_absolute():
            # Resolve relative to this file's location
            project_root = Path(__file__).parent.parent.parent / project_root
        self.config["paths"]["project_root"] = project_root

        for key in self.config["paths"]:
            if key != "project_root":
                path = self.config["paths"][key]
                if isinstance(path, str):
                    self.config["paths"][key] = project_root / path

    def set_random_seed(self, seed: Optional[int] = None) -> None:
        """Set random seeds for reproducibility."""
        if seed is None:
            seed = self.config["random_seeds"]["global_seed"]

        random.seed(seed)
        np.random.seed(seed)
        self.config["random_seeds"]["global_seed"] = seed

    def get_path(self, key: str) -> Path:
        """Get a configured path by key."""
        path = self.config["paths"].get(key)
        if isinstance(path, str):
            return Path(path)
        return path

    def get_threshold(self, key: str, default: Optional[float] = None) -> float:
        """Get a threshold value by key."""
        value = self.config["thresholds"].get(key, default)
        if value is None:
            raise KeyError(f"Threshold '{key}' not found in configuration")
        return float(value)

    def get_api_config(self, key: Optional[str] = None) -> Dict[str, Any]:
        """Get API configuration or a specific key."""
        if key is None:
            return self.config["api"].copy()
        return self.config["api"].get(key)

    def save(self, path: str) -> None:
        """Save configuration to a YAML file."""
        with open(path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

    @classmethod
    def load_from_yaml(cls, path: str) -> "Config":
        """Load configuration from a YAML file."""
        with open(path, "r") as f:
            config = yaml.safe_load(f)
        return cls(config)

    def validate(self) -> bool:
        """Validate configuration values are reasonable."""
        errors = []

        # Validate paths exist
        project_root = self.config["paths"]["project_root"]
        if not isinstance(project_root, Path):
            project_root = Path(project_root)
        if not project_root.exists():
            errors.append(f"Project root does not exist: {project_root}")

        # Validate data directories exist
        for dir_key in ["data_raw", "data_processed", "data_figures", "data_logs"]:
            path = self.config["paths"].get(dir_key)
            if isinstance(path, Path) and not path.exists():
                errors.append(f"Data directory does not exist: {path}")

        # Validate thresholds are in valid ranges
        completeness = self.config["thresholds"]["dataset_completeness"]
        if not 0 <= completeness <= 1:
            errors.append(f"Dataset completeness must be between 0 and 1: {completeness}")

        repo_min = self.config["thresholds"]["repository_minimum"]
        if repo_min <= 0:
            errors.append(f"Repository minimum must be positive: {repo_min}")

        outlier_days = self.config["thresholds"]["outlier_threshold_days"]
        if outlier_days <= 0:
            errors.append(f"Outlier threshold must be positive: {outlier_days}")

        vif = self.config["thresholds"]["collinearity_vif"]
        if vif <= 0:
            errors.append(f"VIF threshold must be positive: {vif}")

        coverage = self.config["thresholds"]["coverage_minimum"]
        if not 0 <= coverage <= 1:
            errors.append(f"Coverage minimum must be between 0 and 1: {coverage}")

        # Validate API settings
        rate_limit = self.config["api"]["rate_limit_delay"]
        if rate_limit <= 0:
            errors.append(f"Rate limit delay must be positive: {rate_limit}")

        max_retries = self.config["api"]["max_retries"]
        if max_retries <= 0:
            errors.append(f"Max retries must be positive: {max_retries}")

        timeout = self.config["api"]["timeout_seconds"]
        if timeout <= 0:
            errors.append(f"Timeout must be positive: {timeout}")

        if errors:
            for error in errors:
                print(f"Configuration validation error: {error}")
            return False

        return True

# Global configuration access functions
def get_config() -> Config:
    """Get the global configuration instance."""
    return Config.get_instance()

def set_seed(seed: int) -> None:
    """Set the global random seed for reproducibility."""
    get_config().set_random_seed(seed)

def get_path(key: str) -> Path:
    """Get a configured path by key."""
    return get_config().get_path(key)

def get_threshold(key: str, default: Optional[float] = None) -> float:
    """Get a threshold value by key."""
    return get_config().get_threshold(key, default)

def get_api_config(key: Optional[str] = None) -> Dict[str, Any]:
    """Get API configuration or a specific key."""
    return get_config().get_api_config(key)

def save_config(path: str) -> None:
    """Save the global configuration to a YAML file."""
    get_config().save(path)

def load_config(path: str) -> Config:
    """Load configuration from a YAML file and set as global."""
    Config._instance = Config.load_from_yaml(path)
    return Config._instance

if __name__ == "__main__":
    # Test the configuration manager
    print("Testing configuration manager...")
    config = get_config()

    # Validate configuration
    is_valid = config.validate()
    print(f"Configuration valid: {is_valid}")

    # Print key settings
    print(f"\nProject root: {config.get_path('project_root')}")
    print(f"Data raw: {config.get_path('data_raw')}")
    print(f"Data processed: {config.get_path('data_processed')}")
    print(f"Data figures: {config.get_path('data_figures')}")
    print(f"State: {config.get_path('state')}")

    print(f"\nDataset completeness threshold: {get_threshold('dataset_completeness')}")
    print(f"Repository minimum: {get_threshold('repository_minimum')}")
    print(f"Outlier threshold (days): {get_threshold('outlier_threshold_days')}")
    print(f"VIF collinearity threshold: {get_threshold('collinearity_vif')}")

    print(f"\nRandom seed: {config.config['random_seeds']['global_seed']}")

    # Test seed setting
    set_seed(123)
    print(f"New random seed: {config.config['random_seeds']['global_seed']}")

    print("\nConfiguration manager test complete.")
