"""
Configuration management for the project.
Handles seeding, path resolution, and environment limits.
"""
import os
import random
from pathlib import Path
from typing import Optional

import numpy as np

class Config:
    """
    Global configuration singleton.
    Handles environment setup, seeding, and resource limits.
    """
    _instance: Optional["Config"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        seed: int = 42,
        root_dir: Optional[str] = None,
        max_workers: Optional[int] = None,
    ):
        if hasattr(self, "_initialized"):
            return

        self.seed = seed
        # Resolve root directory: if not provided, assume project root is 3 levels up from utils/config.py
        self.root_dir = Path(root_dir) if root_dir else Path(__file__).resolve().parent.parent.parent
        
        # CPU limits: use provided max_workers or fall back to detected CPU count
        self.max_workers = max_workers or os.cpu_count() or 1
        
        # Apply random seeds for reproducibility
        random.seed(self.seed)
        np.random.seed(self.seed)
        
        # Seed PyTorch if available
        try:
            import torch
            torch.manual_seed(self.seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.seed)
            # Set deterministic behavior for reproducibility (may impact performance)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
        except ImportError:
            pass  # PyTorch not installed, skip torch seeding

        # Path resolution relative to root_dir
        self.data_dir = self.root_dir / "data"
        self.code_dir = self.root_dir / "code"
        self.figures_dir = self.data_dir / "figures"
        self.results_dir = self.data_dir / "results"
        self.processed_data_dir = self.data_dir / "processed"

        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.processed_data_dir.mkdir(parents=True, exist_ok=True)

    def get_path(self, *parts: str) -> Path:
        """Resolve a path relative to the root directory."""
        return self.root_dir.joinpath(*parts)

    def get_data_path(self, *parts: str) -> Path:
        """Resolve a path relative to the data directory."""
        return self.data_dir.joinpath(*parts)

    def get_results_path(self, *parts: str) -> Path:
        """Resolve a path relative to the results directory."""
        return self.results_dir.joinpath(*parts)

# Default singleton instance
config = Config()