"""
Configuration management for llmXive project.
All paths, seeds, and thresholds are defined here.
"""
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default paths relative to project root
DEFAULT_PATHS = {
    # Raw Data
    'raw_data_dir': PROJECT_ROOT / 'data' / 'raw',
    'training_dir': PROJECT_ROOT / 'data' / 'training',
    'held_out_dir': PROJECT_ROOT / 'data' / 'held_out',
    
    # Processed Data
    'processed_dir': PROJECT_ROOT / 'data' / 'processed',
    'feature_matrix': PROJECT_ROOT / 'data' / 'processed' / 'feature_matrix.csv',
    'rules_dir': PROJECT_ROOT / 'data' / 'processed' / 'rules',
    'global_rules': PROJECT_ROOT / 'data' / 'processed' / 'rules' / 'global_rules.json',
    
    # Benchmark & Evaluation
    'benchmark_results': PROJECT_ROOT / 'data' / 'processed' / 'benchmark_results.json',
    'accuracy_deltas': PROJECT_ROOT / 'data' / 'processed' / 'accuracy_deltas.csv',
    'statistical_analysis': PROJECT_ROOT / 'data' / 'processed' / 'statistical_analysis.json',
    'sweep_config': PROJECT_ROOT / 'data' / 'processed' / 'sweep_config.json',
    'sensitivity_sweep': PROJECT_ROOT / 'data' / 'processed' / 'sensitivity_sweep.csv',
    
    # Logs & State
    'state_file': PROJECT_ROOT / 'data' / 'state.json',
    'logs_dir': PROJECT_ROOT / 'logs',
}

# Default Seeds for Reproducibility
DEFAULT_SEEDS = {
    'random_seed': 42,
    'numpy_seed': 42,
    'torch_seed': 42,
}

# Default Thresholds & Parameters
DEFAULT_THRESHOLDS = {
    'fidelity_threshold': 0.90,
    'min_support': 0.05,
    'max_depth': 5,
    'rule_count_limit': 100,
}

# Model Parameters
DEFAULT_MODEL_PARAMS = {
    'max_depth': 5,
    'min_samples_split': 2,
    'min_samples_leaf': 1,
}

class Config:
    """
    Configuration container.
    """
    def __init__(self, paths: Optional[Dict[str, Path]] = None, seeds: Optional[Dict[str, int]] = None, thresholds: Optional[Dict[str, float]] = None):
        self.paths = {**DEFAULT_PATHS, **(paths or {})}
        self.seeds = {**DEFAULT_SEEDS, **(seeds or {})}
        self.thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.model_params = DEFAULT_MODEL_PARAMS

        # Ensure directories exist
        for path in self.paths.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)

    def get(self, key: str, default: Any = None) -> Any:
        """Get config value by key (supports dot notation for nested)."""
        # Simple flat lookup for now
        if key in self.paths:
            return self.paths[key]
        if key in self.seeds:
            return self.seeds[key]
        if key in self.thresholds:
            return self.thresholds[key]
        return default

_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Singleton accessor for the global configuration.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def reset_config() -> None:
    """Reset the singleton instance (useful for testing)."""
    global _config_instance
    _config_instance = None

# Backwards compatibility for direct dict access if needed
def __getitem__(self, key):
    return get_config().get(key)

def __setitem__(self, key, value):
    cfg = get_config()
    if key in cfg.paths:
        cfg.paths[key] = value
    elif key in cfg.seeds:
        cfg.seeds[key] = value
    elif key in cfg.thresholds:
        cfg.thresholds[key] = value

# Expose config as a module-level dict-like object if imported directly
# However, the preferred usage is get_config()
# This block ensures `from config import get_config` works as expected
# and allows `config['paths']['...']` if needed.
# To support `config = get_config(); config['paths']['...']` we rely on the Config class logic or a wrapper.
# The current implementation returns a Config object which has .paths dict.
# If the code expects a dict, we can return the paths dict directly or adapt.
# Given the existing imports in other files (e.g. `from config import get_config`),
# we assume they call `get_config()` and access `.paths` or `.get()`.
# However, some existing code might do `config['paths']`.
# Let's ensure Config supports dict-like access for keys in paths/seeds/thresholds.
# Actually, looking at the imports in other files, they use `get_config()`.
# Let's stick to the object interface but ensure it's robust.

# To support `from config import get_config` and then `cfg = get_config(); cfg['paths']['...']`
# we need Config to implement __getitem__.
# Let's add that to the class definition above implicitly by ensuring the return type is compatible.
# The current class doesn't implement __getitem__. Let's add it.
# (Re-defining the class logic in the __init__ to include __getitem__ is not possible here without re-writing the class)
# Instead, we will rely on the fact that `get_config()` returns a Config object,
# and we assume the calling code accesses `.paths` or `.get()`.
# If the calling code expects a dict, we might need to adjust.
# Looking at `code/evaluation/benchmark.py` imports: `from config import get_config`.
# It likely does `config = get_config(); config['paths']['...']`.
# So we MUST implement __getitem__ on Config.

# Re-defining the class logic to include dict-like access:
class Config:
    """
    Configuration container with dict-like access.
    """
    def __init__(self, paths: Optional[Dict[str, Path]] = None, seeds: Optional[Dict[str, int]] = None, thresholds: Optional[Dict[str, float]] = None):
        self._paths = {**DEFAULT_PATHS, **(paths or {})}
        self._seeds = {**DEFAULT_SEEDS, **(seeds or {})}
        self._thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
        self.model_params = DEFAULT_MODEL_PARAMS
        self._all = {**self._paths, **self._seeds, **self._thresholds}

        # Ensure directories exist
        for path in self._paths.values():
            if isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)

    def __getitem__(self, key: str) -> Any:
        if key in self._all:
            return self._all[key]
        raise KeyError(f"Config key '{key}' not found.")

    def get(self, key: str, default: Any = None) -> Any:
        return self._all.get(key, default)

    @property
    def paths(self) -> Dict[str, Path]:
        return self._paths

    @property
    def seeds(self) -> Dict[str, int]:
        return self._seeds

    @property
    def thresholds(self) -> Dict[str, float]:
        return self._thresholds

# Re-bind the singleton logic
_config_instance = None
def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
def reset_config() -> None:
    global _config_instance
    _config_instance = None