"""Configuration management for data paths and random seeds.

This module provides a centralized configuration system for the project,
handling:
- Data directory paths (raw, processed, results, figures)
- Random seed management for reproducibility
- Configuration file loading and merging
- Directory structure initialization
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class Config:
    """Configuration holder with dict-like access."""

    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def __getitem__(self, key: str) -> Any:
        if key not in self._data:
            raise KeyError(f"Configuration key '{key}' not found")
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with a default fallback."""
        return self._data.get(key, default)

    def __repr__(self) -> str:
        return f"Config({self._data})"


_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """Load or return the global configuration singleton.

    Reads from `code/config.yaml` if present, otherwise uses defaults.
    Ensures all required directories exist on disk.

    Returns:
        Config: The global configuration object.
    """
    global _CONFIG
    if _CONFIG is None:
        project_root = Path(__file__).parent.parent

        default_paths = {
            "raw_dir": str(project_root / "data" / "raw"),
            "processed_dir": str(project_root / "data" / "processed"),
            "results_dir": str(project_root / "results"),
            "figures_dir": str(project_root / "results" / "figures"),
            "log_file": str(project_root / "code" / "modeling_log.yaml"),
            "cleaned_data": str(project_root / "data" / "processed" / "cleaned_data.csv"),
            "engineered_data": str(project_root / "data" / "processed" / "engineered_data.csv"),
            "model_results": str(project_root / "results" / "model_results.yaml"),
            "report": str(project_root / "results" / "report.pdf"),
            "validity_metrics": str(project_root / "results" / "validity_metrics.yaml"),
            "metadata": str(project_root / "data" / "metadata.yaml")
        }

        # Start with defaults
        config_dict = {
            "project": "PROJ-018",
            "seed": 42,
            "paths": default_paths
        }

        # Try to load from config.yaml if it exists
        config_path = Path(__file__).parent / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded = yaml.safe_load(f)
                    if loaded:
                        # Merge project name
                        if "project" in loaded:
                            config_dict["project"] = loaded["project"]

                        # Merge seed
                        if "seed" in loaded:
                            config_dict["seed"] = loaded["seed"]

                        # Merge paths (override defaults with loaded values)
                        if "paths" in loaded:
                            for k, v in loaded["paths"].items():
                                if k in default_paths:
                                    # Resolve relative paths against project root if needed
                                    if not Path(v).is_absolute():
                                        v = str(project_root / v)
                                    config_dict["paths"][k] = v
            except Exception as e:
                # If config file is malformed, log warning and stick to defaults
                print(f"Warning: Could not load config.yaml: {e}. Using defaults.")

        _CONFIG = Config(config_dict)

        # Ensure all directories exist
        for path_str in _CONFIG["paths"].values():
            p = Path(path_str)
            if p.suffix:  # It's a file path, ensure parent exists
                p.parent.mkdir(parents=True, exist_ok=True)
            else:  # It's a directory
                p.mkdir(parents=True, exist_ok=True)

    return _CONFIG


def set_random_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility across libraries.

    Args:
        seed: Random seed integer. If None, uses seed from config (default 42).
    """
    if seed is None:
        seed = get_config().get("seed", 42)

    # Set Python's random seed
    random.seed(seed)

    # Set environment variable for hash reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Set numpy seed if available (lazy import to avoid hard dependency)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    # Set torch seeds if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def get_data_path(relative_path: str) -> Path:
    """Get absolute path for a data file relative to the project root.

    Args:
        relative_path: Path relative to the project root
                     (e.g., 'data/raw/survey.csv').

    Returns:
        Path: Absolute Path object.
    """
    project_root = Path(__file__).parent.parent
    full_path = project_root / relative_path
    return full_path


def get_config_path(key: str) -> Path:
    """Get the absolute path for a configuration-defined file.

    Args:
        key: The key in the 'paths' section of the config
             (e.g., 'cleaned_data', 'model_results').

    Returns:
        Path: Absolute Path object for the file.
    """
    config = get_config()
    path_str = config["paths"].get(key)
    if path_str is None:
        raise KeyError(f"Path key '{key}' not found in configuration")
    return Path(path_str)