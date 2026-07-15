"""
Base configuration loader for paths and seeds.

This module provides a centralized configuration management system for the
EnterpriseClawBench extension project. It handles path resolution relative to
the project root, seed management for reproducibility, and environment variable
overrides.

Usage:
    from src.config import Config
    cfg = Config()
    print(cfg.data_raw)
"""

import os
import json
import random
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """
    Centralized configuration manager.

    Loads paths relative to the project root and manages random seeds
    for reproducibility across the pipeline.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        config_path: Optional[Path] = None,
        seed: Optional[int] = None,
    ):
        """
        Initialize the configuration.

        Args:
            project_root: The root directory of the project. Defaults to
                          the directory containing this module's parent's parent.
            config_path: Optional path to a JSON config file for overrides.
            seed: Optional random seed for reproducibility.
        """
        if project_root is None:
            # Default to the repository root (two levels up from this file)
            project_root = Path(__file__).resolve().parent.parent.parent

        self.project_root = project_root
        self.seed = seed if seed is not None else int(os.environ.get("LLMXIVE_SEED", 42))

        # Set global seeds immediately for reproducibility
        random.seed(self.seed)
        # Note: numpy and torch seeds are set in their respective modules
        # when imported, using this config's seed.

        # Load path definitions
        self._paths = self._load_paths()

        # Load overrides if a config file is provided
        if config_path and config_path.exists():
            self._load_overrides(config_path)

    def _load_paths(self) -> Dict[str, Path]:
        """
        Define the standard directory structure relative to the project root.

        Returns:
            A dictionary mapping logical names to absolute Path objects.
        """
        base = self.project_root
        paths = {
            # Source code
            "src": base / "src",
            "tests": base / "tests",
            "specs": base / "specs",

            # Data directories
            "data_raw": base / "data" / "raw",
            "data_processed": base / "data" / "processed",
            "data_results": base / "data" / "results",
            "data_models": base / "data" / "models",
            "figures": base / "figures",

            # Intermediate/state
            "state": base / "state",
        }

        # Ensure directories exist (optional, but good for initialization)
        # We do not raise if they don't exist, as some might be created later.
        # However, we ensure the main data dirs exist if possible.
        for p in paths.values():
            p.mkdir(parents=True, exist_ok=True)

        return paths

    def _load_overrides(self, config_path: Path) -> None:
        """
        Load configuration overrides from a JSON file.

        Args:
            config_path: Path to the JSON configuration file.
        """
        with open(config_path, "r", encoding="utf-8") as f:
            overrides = json.load(f)

        if "seed" in overrides:
            self.seed = overrides["seed"]
            random.seed(self.seed)

        if "paths" in overrides:
            for key, value in overrides["paths"].items():
                if key in self._paths:
                    # Convert relative overrides to absolute if they are relative
                    if not os.path.isabs(value):
                        value = self.project_root / value
                    self._paths[key] = Path(value)

    def __getattr__(self, name: str) -> Any:
        """
        Allow accessing path keys as attributes (e.g., config.data_raw).
        """
        if name in self._paths:
            return self._paths[name]
        raise AttributeError(f"Configuration has no attribute '{name}'")

    def __getitem__(self, name: str) -> Path:
        """
        Allow accessing path keys via dictionary syntax (e.g., config['data_raw']).
        """
        if name in self._paths:
            return self._paths[name]
        raise KeyError(f"Configuration has no key '{name}'")

    def get(self, name: str, default: Optional[Path] = None) -> Optional[Path]:
        """
        Safe dictionary-style access.
        """
        return self._paths.get(name, default)

    def to_dict(self) -> Dict[str, str]:
        """
        Export the current configuration as a dictionary of strings.

        Useful for logging or serialization.
        """
        return {k: str(v) for k, v in self._paths.items()}

    def __repr__(self) -> str:
        return f"Config(seed={self.seed}, root={self.project_root})"


# Singleton instance for convenience
_global_config: Optional[Config] = None


def get_config() -> Config:
    """
    Retrieve the global configuration instance.

    Returns:
        The global Config instance, creating one if it doesn't exist.
    """
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def reset_config(
    project_root: Optional[Path] = None,
    config_path: Optional[Path] = None,
    seed: Optional[int] = None,
) -> Config:
    """
    Reset the global configuration with new parameters.

    Args:
        project_root: New project root.
        config_path: New config file path.
        seed: New seed.
    """
    global _global_config
    _global_config = Config(project_root=project_root, config_path=config_path, seed=seed)
    return _global_config
