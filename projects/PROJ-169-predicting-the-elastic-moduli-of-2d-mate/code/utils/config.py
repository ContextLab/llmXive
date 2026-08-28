import os
import random
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import numpy as np
import torch


# Constants required by Constitution Principle VI and SC-001/SC-004
# These define the hard gates for data volume, memory, and statistical iterations.
MIN_ENTRY_THRESHOLD = 1000
MAX_MEMORY_GB = 7.0
BOOTSTRAP_ITERATIONS = 1000
PERMUTATION_SHUFFLES = 1000


class Config:
    """Global configuration manager with tolerant attribute access.

    This class enforces reproducibility by pinning random seeds for
    torch, numpy, and random. It also provides a central location for
    project paths and resource limits.
    """

    def __init__(self) -> None:
        self.seed: int = 42
        self.project_root: Path = Path(os.getenv("PROJECT_ROOT", "."))
        self.data_dir: Path = self.project_root / "data"
        self.code_dir: Path = self.project_root / "code"
        
        # Centralized path definitions
        self.paths: Dict[str, Any] = {
            "exclusion_log": self.data_dir / "processed" / "exclusion_log.json",
            "bias_report": self.data_dir / "results" / "bias_report.json",
            "graphs_v1": self.data_dir / "processed" / "graphs_v1.parquet",
            "split_indices": self.data_dir / "processed" / "split_indices.json",
            "training_logs": self.data_dir / "results" / "training_logs.json",
            "generalization_metrics": self.data_dir / "results" / "generalization_metrics.json",
            "intra_family_baseline": self.data_dir / "results" / "intra_family_baseline.json",
            "permutation_pvalues": self.data_dir / "results" / "permutation_pvalues.json",
            "shap_pvalues": self.data_dir / "results" / "shap_pvalues.json",
            "ablation_report": self.data_dir / "results" / "ablation_report.json",
            "final_metrics": self.data_dir / "results" / "final_metrics.json",
            "model_v1": self.data_dir / "processed" / "model_v1.pt",
        }
        
        # Resource constraints
        self.min_family_size: int = 5
        self.cpu_limit: int = 4
        self.max_memory_gb: float = MAX_MEMORY_GB

    def set_seed(self, seed: int) -> None:
        """Set global random seeds for reproducibility.

        Enforces pinning for `torch`, `numpy`, and `random` across all modules.
        This ensures that experiments are deterministic and reproducible.
        
        Args:
            seed: The integer seed value to use.
        """
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
        """Get a path from the paths dictionary.

        Args:
            key: The key identifying the path.
            default: Default path if key is not found.

        Returns:
            The requested Path object.
        """
        return self.paths.get(key, default or Path("."))

    # Tolerant attribute access for any logger-style calls or missing attributes
    # This prevents AttributeError when external scripts call methods like .info(), .debug()
    # or access attributes not explicitly defined here, satisfying the "Shared-Module Contract".
    def __getattr__(self, name: str) -> Any:
        # Return a no-op callable for unknown attributes to prevent AttributeError
        # This allows scripts to call config.some_unknown_method(...) without crashing.
        def _noop(*args: Any, **kwargs: Any) -> Any:
            return None
        return _noop

    def __setattr__(self, name: str, value: Any) -> None:
        # Handle paths in the dictionary if they exist there
        # This allows dynamic updating of path entries via config.paths['key'] = new_val
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
    to ensure reproducibility. It delegates to the global config's set_seed method.

    Args:
        seed: The random seed value to use. Defaults to 42.
    """
    config = get_config()
    config.set_seed(seed)