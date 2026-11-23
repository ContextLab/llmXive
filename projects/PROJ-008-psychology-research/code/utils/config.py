"""
Configuration management and seed pinning for the llmXive psychology research pipeline.

This module provides:
- ProjectConfig: A dataclass holding all project paths and configuration settings.
- get_config(): Singleton accessor for the project configuration.
- set_seed(): Deterministic seed pinning for reproducibility (random, numpy, torch if available).
- Path helpers: get_data_path, get_output_path, get_code_path, etc.
"""
import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List

# Determine project root based on the structure defined in tasks.md
# The project is at projects/PROJ-008-psychology-research/ relative to repo root.
# When running scripts, we assume the current working directory is the project root.
# If running from within the repo root, we detect the project folder.

def _find_project_root() -> Path:
    """
    Locate the project root directory.
    Looks for 'code/', 'data/', 'tasks.md' in the current directory or parent.
    """
    current = Path.cwd()
    # Check current directory first
    if (current / "code").exists() and (current / "data").exists() and (current / "tasks.md").exists():
        return current

    # Check parent directory (in case we are in a subfolder like code/utils)
    parent = current.parent
    if (parent / "code").exists() and (parent / "data").exists() and (parent / "tasks.md").exists():
        return parent

    # Fallback: assume current is root if it contains tasks.md
    if (current / "tasks.md").exists():
        return current

    raise FileNotFoundError(
        "Could not locate project root. Ensure 'tasks.md', 'code/', and 'data/' exist in the current or parent directory."
    )

@dataclass
class ProjectConfig:
    """
    Centralized configuration for the project.
    All paths are resolved relative to the project root.
    """
    root: Path = field(default_factory=_find_project_root)
    seed: int = 42
    debug: bool = False

    # Directory paths
    code_dir: Path = field(init=False)
    data_dir: Path = field(init=False)
    data_raw_dir: Path = field(init=False)
    data_processed_dir: Path = field(init=False)
    data_interim_dir: Path = field(init=False)
    tests_dir: Path = field(init=False)
    docs_dir: Path = field(init=False)
    contracts_dir: Path = field(init=False)
    scripts_dir: Path = field(init=False)
    figures_dir: Path = field(init=False)

    def __post_init__(self):
        self.code_dir = self.root / "code"
        self.data_dir = self.root / "data"
        self.data_raw_dir = self.data_dir / "raw"
        self.data_processed_dir = self.data_dir / "processed"
        self.data_interim_dir = self.data_dir / "interim"
        self.tests_dir = self.root / "tests"
        self.docs_dir = self.root / "docs"
        self.contracts_dir = self.root / "contracts"
        self.scripts_dir = self.root / "scripts"
        self.figures_dir = self.root / "figures"

        # Ensure directories exist
        self._ensure_dirs()

    def _ensure_dirs(self):
        """Create all required directories if they don't exist."""
        dirs = [
            self.code_dir,
            self.data_dir,
            self.data_raw_dir,
            self.data_processed_dir,
            self.data_interim_dir,
            self.tests_dir,
            self.docs_dir,
            self.contracts_dir,
            self.scripts_dir,
            self.figures_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_data_path(self, subpath: str) -> Path:
        """Resolve a path relative to data/raw."""
        return self.data_raw_dir / subpath

    def get_output_path(self, subpath: str) -> Path:
        """Resolve a path relative to data/processed."""
        return self.data_processed_dir / subpath

    def get_code_path(self, subpath: str) -> Path:
        """Resolve a path relative to code/."""
        return self.code_dir / subpath

    def get_contracts_path(self, subpath: str) -> Path:
        """Resolve a path relative to contracts/."""
        return self.contracts_dir / subpath

    def get_docs_path(self, subpath: str) -> Path:
        """Resolve a path relative to docs/."""
        return self.docs_dir / subpath

    def get_scripts_path(self, subpath: str) -> Path:
        """Resolve a path relative to scripts/."""
        return self.scripts_dir / subpath

    def get_tests_path(self, subpath: str) -> Path:
        """Resolve a path relative to tests/."""
        return self.tests_dir / subpath

# Singleton instance
_config_instance: Optional[ProjectConfig] = None

def get_config() -> ProjectConfig:
    """Get the singleton ProjectConfig instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ProjectConfig()
    return _config_instance

def set_seed(seed: Optional[int] = None) -> None:
    """
    Set the random seed for reproducibility across all relevant libraries.
    Defaults to the seed defined in ProjectConfig (42) if not provided.
    """
    if seed is None:
        seed = get_config().seed

    # Python random
    random.seed(seed)

    # Numpy (if available)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

    # PyTorch (if available)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

    # TensorFlow (if available)
    try:
        import tensorflow as tf
        tf.random.set_seed(seed)
    except ImportError:
        pass

# Convenience functions
def get_data_path(subpath: str) -> Path:
    return get_config().get_data_path(subpath)

def get_output_path(subpath: str) -> Path:
    return get_config().get_output_path(subpath)

def get_code_path(subpath: str) -> Path:
    return get_config().get_code_path(subpath)

def get_contracts_path(subpath: str) -> Path:
    return get_config().get_contracts_path(subpath)

def get_docs_path(subpath: str) -> Path:
    return get_config().get_docs_path(subpath)

def get_scripts_path(subpath: str) -> Path:
    return get_config().get_scripts_path(subpath)

def get_tests_path(subpath: str) -> Path:
    return get_config().get_tests_path(subpath)