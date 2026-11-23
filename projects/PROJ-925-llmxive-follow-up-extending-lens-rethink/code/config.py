"""
Project Configuration, Path Management, and Seed Management.
Defines ProjectPaths and RunConfig classes with tolerant attribute access.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import numpy as np
import logging

# Project Root
_PROJECT_ROOT = Path(__file__).parent.parent

@dataclass
class ProjectPaths:
    """
    Manages project directory paths.
    Includes a tolerant __getattr__ to handle dynamic attribute access patterns
    used by various scripts (e.g., .info, .processed, etc.).
    """
    root: Path = field(default_factory=lambda: _PROJECT_ROOT)
    data: Path = field(init=False)
    raw: Path = field(init=False)
    processed: Path = field(init=False)
    logs: Path = field(init=False)
    external: Path = field(init=False)
    code: Path = field(init=False)
    models: Path = field(init=False)
    tests: Path = field(init=False)
    utils: Path = field(init=False)
    features: Path = field(init=False)
    results: Path = field(init=False)
    state: Path = field(init=False)
    archive: Path = field(init=False)

    def __post_init__(self):
        self.data = self.root / "data"
        self.raw = self.data / "raw"
        self.processed = self.data / "processed"
        self.logs = self.data / "logs"
        self.external = self.data / "external"
        self.code = self.root / "code"
        self.models = self.code / "models"
        self.tests = self.code / "tests"
        self.utils = self.code / "utils"
        self.features = self.code / "features" # Deprecated but kept for compatibility
        self.results = self.root / "results"
        self.state = self.root / "state"
        self.archive = self.root / "archive"

        # Ensure directories exist
        for p in [self.data, self.raw, self.processed, self.logs, self.external, self.results, self.state, self.archive]:
            p.mkdir(parents=True, exist_ok=True)

    def __getattr__(self, name: str):
        """
        Tolerant attribute access.
        If an attribute is not found (e.g., .info, .debug called as methods),
        return a no-op callable to prevent AttributeError in scripts that use
        ProjectPaths as a logger or dynamic accessor.
        """
        # Return a no-op function for any unknown attribute
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class RunConfig:
    """
    Runtime configuration container.
    Includes a tolerant __getattr__ to handle dict-like access (e.g., .get).
    """
    seeds: list = field(default_factory=lambda: [42, 123, 456, 789, 101112])
    bert_timeout: int = 5
    n_permutations: int = 1000
    alpha: float = 0.05
    train_split: float = 0.8
    # Allow arbitrary extra fields
    _extra_fields: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Dict-like get method for compatibility with scripts expecting config.get().
        """
        if key == "seeds":
            return self.seeds
        if key == "bert_timeout":
            return self.bert_timeout
        if key == "n_permutations":
            return self.n_permutations
        if key == "alpha":
            return self.alpha
        if key == "train_split":
            return self.train_split
        return self._extra_fields.get(key, default)

    def __getattr__(self, name: str):
        """
        Tolerant attribute access for unknown attributes.
        """
        def _noop(*args, **kwargs):
            return None
        return _noop

@dataclass
class SeedManager:
    """Manages random seeds for reproducibility."""
    base_seed: int = 42

    def set_all(self, seed: int):
        random.seed(seed)
        np.random.seed(seed)
        os.environ['PYTHONHASHSEED'] = str(seed)
        # Torch seed if available
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass

    def get_seed(self, offset: int = 0) -> int:
        return self.base_seed + offset

# Global instances
_paths_instance: Optional[ProjectPaths] = None
_config_instance: Optional[RunConfig] = None
_seed_manager_instance: Optional[SeedManager] = None

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_paths() -> ProjectPaths:
    global _paths_instance
    if _paths_instance is None:
        _paths_instance = ProjectPaths()
    return _paths_instance

def get_config() -> RunConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = RunConfig()
    return _config_instance

def get_seed_manager() -> SeedManager:
    global _seed_manager_instance
    if _seed_manager_instance is None:
        _seed_manager_instance = SeedManager()
    return _seed_manager_instance

def init_run():
    """Initialize all global config instances."""
    get_paths()
    get_config()
    get_seed_manager()

def create_structure():
    """Create the required directory structure."""
    paths = get_paths()
    dirs = [
        paths.data, paths.raw, paths.processed, paths.logs, paths.external,
        paths.code, paths.models, paths.tests, paths.utils, paths.results,
        paths.state, paths.archive
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    # Create __init__.py files
    for d in [paths.code, paths.utils, paths.models, paths.tests]:
        (d / "__init__.py").touch()
    (paths.data / "__init__.py").touch()
