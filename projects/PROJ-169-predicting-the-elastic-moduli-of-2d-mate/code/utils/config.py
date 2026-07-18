import os
import random
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import numpy as np
import torch

class Config:
    """
    Global configuration manager for the project.
    Handles seeding, paths, and tolerant attribute access.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        self.seed = 42
        self._paths: Dict[str, Path] = {}
        self._setup_paths()
        self._setup_seeds()
        self._initialized = True

    def _setup_paths(self):
        """Initialize standard project paths."""
        base = Path(__file__).parent.parent
        self._paths = {
            'root': base,
            'data_raw': base / 'data' / 'raw',
            'data_processed': base / 'data' / 'processed',
            'data_results': base / 'data' / 'results',
            'code': base / 'code',
            'state': base / 'state' / 'projects',
        }
        # Ensure directories exist
        for p in self._paths.values():
            p.mkdir(parents=True, exist_ok=True)

    def _setup_seeds(self):
        """Pin seeds for reproducibility."""
        random.seed(self.seed)
        np.random.seed(self.seed)
        torch.manual_seed(self.seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(self.seed)
        os.environ['PYTHONHASHSEED'] = str(self.seed)

    @property
    def paths(self) -> Dict[str, Path]:
        """Return the paths dictionary."""
        return self._paths

    def get_path(self, key: str) -> Path:
        """Get a specific path by key."""
        return self._paths.get(key, Path('.'))

    # Tolerant logger-style attribute access
    def __getattr__(self, name: str) -> Callable:
        """
        Fallback for unknown attributes/methods to prevent AttributeError.
        Returns a no-op callable for logger-like usage.
        """
        def _noop(*args, **kwargs) -> Any:
            return None
        return _noop

_config_instance = None

def get_config() -> Config:
    """Get the singleton Config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
