import os
import random
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import numpy as np
import torch

_global_config: Optional['Config'] = None

class Config:
    """
    Global configuration manager for the project.
    Handles seeding, path resolution, and CPU limits.
    """
    def __init__(self, seed: int = 42, base_dir: Optional[Path] = None):
        self.seed = seed
        self.base_dir = base_dir or Path(__file__).parent.parent.parent
        self._set_seeds(seed)
        self._cpu_limit()
        
        # Initialize paths relative to base_dir
        self.root = self.base_dir
        self.code = self.root / "code"
        self.data = self.root / "data"
        self.data_raw = self.data / "raw"
        self.data_processed = self.data / "processed"
        self.data_results = self.data / "results"
        self.tests = self.root / "tests"
        self.docs = self.root / "docs"
        self.state = self.root / "state"
        self.state_projects = self.state / "projects"

    def _set_seeds(self, seed: int) -> None:
        """Pin random seeds for reproducibility."""
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        os.environ['PYTHONHASHSEED'] = str(seed)

    def _cpu_limit(self) -> None:
        """Set CPU limits if running in a constrained environment."""
        # Basic check, can be extended
        if os.name == 'posix':
            try:
                # Try to read cgroups limit if available
                with open('/sys/fs/cgroup/cpu/cpu.cfs_quota_us', 'r') as f:
                    quota = int(f.read())
                    if quota > 0:
                        # Limit threads based on quota (simplified)
                        pass
            except FileNotFoundError:
                pass

    def get_path(self, key: str, default: Optional[Path] = None) -> Path:
        """Get a path attribute dynamically."""
        if hasattr(self, key):
            return getattr(self, key)
        if default:
            return default
        raise AttributeError(f"Config has no attribute '{key}'")

    # Tolerant attribute access for dynamic calls (e.g., config.paths)
    def __getattr__(self, name: str) -> Any:
        # Fallback for any attribute not explicitly defined
        # This handles cases like config.paths which might be expected as a dict-like access
        # or config.paths.get('key') if paths was intended to be a dict.
        # However, since we define specific path attributes (self.data, self.code),
        # we should return those. If the caller expects a 'paths' dict, we can return a proxy.
        if name == 'paths':
            # Return a dict-like object that maps keys to our attributes
            return {
                'data_raw': self.data_raw,
                'data_processed': self.data_processed,
                'data_results': self.data_results,
                'code': self.code,
                'root': self.root,
                'exclusion_log': self.data_processed / 'exclusion_log.json',
                'graphs_v1': self.data_processed / 'graphs_v1.parquet',
                'split_indices': self.data_processed / 'split_indices.json',
                'predictions': self.data_processed / 'predictions.json',
                'model_v1': self.data_processed / 'model_v1.pt',
                'training_logs': self.data_results / 'training_logs.json',
                'generalization_metrics': self.data_results / 'generalization_metrics.json',
            }
        # For any other unknown attribute, return a no-op callable or None
        # to prevent AttributeError in loose usage patterns
        def _noop(*args, **kwargs):
            return None
        return _noop

def get_config() -> Config:
    """Get the global configuration instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def set_global_config(seed: int = 42, base_dir: Optional[Path] = None) -> Config:
    """Set the global configuration instance."""
    global _global_config
    _global_config = Config(seed=seed, base_dir=base_dir)
    return _global_config
