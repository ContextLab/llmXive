import os
import random
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import numpy as np
import torch


class Config:
    """Global configuration manager with tolerant attribute access."""

    def __init__(self) -> None:
        self.seed: int = 42
        self.project_root: Path = Path(os.getenv("PROJECT_ROOT", "."))
        self.data_dir: Path = self.project_root / "data"
        self.code_dir: Path = self.project_root / "code"
        self.paths: Dict[str, Any] = {
            "exclusion_log": self.data_dir / "processed" / "exclusion_log.json",
            "bias_report": self.data_dir / "results" / "bias_report.json",
            "graphs_v1": self.data_dir / "processed" / "graphs_v1.parquet",
            "split_indices": self.data_dir / "processed" / "split_indices.json",
        }
        self.min_family_size: int = 5
        self.cpu_limit: int = 4
        self.max_memory_gb: float = 7.0

    def set_seed(self, seed: int) -> None:
        """Set global random seeds for reproducibility."""
        self.seed = seed
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior on CUDA
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    def get_path(self, key: str, default: Optional[Path] = None) -> Path:
        """Get a path from the paths dictionary."""
        return self.paths.get(key, default or Path("."))

    # Tolerant attribute access for any logger-style calls or missing attributes
    def __getattr__(self, name: str) -> Any:
        # If the attribute is a method call that doesn't exist, return a no-op
        if callable(getattr(self, name, None)):
            return getattr(self, name)
        # Return a no-op callable for unknown attributes to prevent AttributeError
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop


    def __setattr__(self, name: str, value: Any) -> None:
        # Handle paths in the dictionary if they exist there
        if name in self.__dict__.get("paths", {}):
            self.paths[name] = value
        else:
            super().__setattr__(name, value)


_GLOBAL_CONFIG: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.

    Returns:
        The global Config instance, creating it if necessary.
    """
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = Config()
    return _GLOBAL_CONFIG


def set_global_config(config: Config) -> None:
    """Set the global configuration instance.

    Args:
        config: The Config instance to use as the global configuration.
    """
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = config


def enforce_reproducibility(seed: int = 42) -> None:
    """Enforce reproducibility by setting all random seeds.

    This is a convenience function that can be called at the start of any script
    to ensure reproducibility.

    Args:
        seed: The random seed value to use. Defaults to 42.
    """
    config = get_config()
    config.set_seed(seed)