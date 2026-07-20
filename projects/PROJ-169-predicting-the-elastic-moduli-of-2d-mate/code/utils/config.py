"""Global configuration and seeding management.

This module provides a global configuration singleton that enforces reproducibility
by pinning random seeds for torch, numpy, and random across all modules.
It also manages project paths and CPU limits.
"""
import os
import random
from pathlib import Path
from typing import Optional, Any, Dict, Callable
import numpy as np
import torch


class Config:
    """
    Global configuration holder.

    Provides paths, seeding, and other project-wide settings.
    Designed to be tolerant of missing attributes to prevent crashes
    in partially initialized states.
    """

    def __init__(self, seed: int = 42):
        # Define default paths
        self.root_dir = Path(os.getenv("PROJECT_ROOT", "."))
        self.data_raw = self.root_dir / "data" / "raw"
        self.data_processed = self.root_dir / "data" / "processed"
        self.data_results = self.root_dir / "data" / "results"
        self.code_dir = self.root_dir / "code"

        # Specific paths for bias check
        self.exclusion_log_path = self.data_processed / "exclusion_log.json"
        self.bias_report_path = self.data_results / "bias_report.json"

        # Configuration for filtering
        self.min_family_size = 5

        # Paths dictionary for flexible access
        self.paths = {
            "data_raw": self.data_raw,
            "data_processed": self.data_processed,
            "data_results": self.data_results,
            "exclusion_log": self.exclusion_log_path,
            "bias_report": self.bias_report_path,
            "model_v1": self.data_processed / "model_v1.pt",
            "graphs_v1": self.data_processed / "graphs_v1.parquet",
            "split_indices": self.data_processed / "split_indices.json",
            "training_logs": self.data_results / "training_logs.json",
            "generalization_metrics": self.data_results / "generalization_metrics.json",
            "terminology_audit": self.data_results / "terminology_audit.json",
        }

        # Seeding defaults
        self.seed = seed
        self.cpu_limit = None

        # Initialize seeds immediately
        self.set_seed(seed)

    def set_seed(self, seed: int = 42) -> None:
        """Set global random seeds for reproducibility.

        This method enforces pinning for torch, numpy, and random across all modules.
        It also sets CUDA seeds if a GPU is available.

        Args:
            seed: The random seed value to use. Defaults to 42.
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

    def get_available_memory(self) -> float:
        """Get available memory in GB.

        Returns:
            Available memory in GB. Defaults to 16.0 if cannot be determined.
        """
        try:
            # Try to get available memory from OS
            import psutil
            return psutil.virtual_memory().available / (1024 ** 3)
        except ImportError:
            # Fallback to a reasonable default
            return 16.0

    def set_cpu_limit(self, limit: Optional[int] = None) -> None:
        """Set CPU thread limits.

        Args:
            limit: Maximum number of CPU threads. If None, uses default.
        """
        self.cpu_limit = limit
        if limit is not None:
            torch.set_num_threads(limit)
            os.environ["OMP_NUM_THREADS"] = str(limit)
            os.environ["MKL_NUM_THREADS"] = str(limit)

    # Tolerant attribute access for paths
    def __getattr__(self, name: str) -> Any:
        # If a specific attribute is requested that doesn't exist,
        # check if it's a path key in the paths dict
        if name in self.paths:
            return self.paths[name]
        # Fallback to default behavior (raises AttributeError)
        raise AttributeError(f"'Config' object has no attribute '{name}'")

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