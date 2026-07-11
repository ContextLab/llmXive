import os
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, List

import numpy as np

# Optional torch import for reproducibility in deep learning contexts
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


@dataclass
class ProjectConfig:
    """
    Centralized configuration management for the psychology research project.
    Handles paths, environment variables, and reproducibility seeds.
    """
    project_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[2])
    data_dir: Path = field(default_factory=lambda: Path("data"))
    code_dir: Path = field(default_factory=lambda: Path("code"))
    output_dir: Path = field(default_factory=lambda: Path("data/processed"))
    logs_dir: Path = field(default_factory=lambda: Path("data/logs"))
    
    # Reproducibility settings
    random_seed: int = 42
    deterministic_mode: bool = True

    def __post_init__(self):
        """Ensure paths are absolute relative to project root."""
        self.project_root = self.project_root.resolve()
        self.data_dir = self.project_root / self.data_dir
        self.code_dir = self.project_root / self.code_dir
        self.output_dir = self.project_root / self.output_dir
        self.logs_dir = self.project_root / self.logs_dir
        
        # Create directories if they don't exist
        for d in [self.data_dir, self.output_dir, self.logs_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def get_data_path(self, subpath: str) -> Path:
        """Construct a full path within the data directory."""
        return self.data_dir / subpath

    def get_output_path(self, subpath: str) -> Path:
        """Construct a full path within the output directory."""
        return self.output_dir / subpath

    def get_code_path(self, subpath: str) -> Path:
        """Construct a full path within the code directory."""
        return self.code_dir / subpath


# Global configuration instance
_config: Optional[ProjectConfig] = None


def get_config() -> ProjectConfig:
    """
    Retrieve the singleton ProjectConfig instance.
    Initializes it if it doesn't exist.
    """
    global _config
    if _config is None:
        _config = ProjectConfig()
    return _config


def set_seed(seed: Optional[int] = None) -> None:
    """
    Pin random seeds for reproducibility across numpy, python random, and optionally torch.
    
    Args:
        seed: The seed value. Defaults to the value in ProjectConfig if None.
    """
    if seed is None:
        seed = get_config().random_seed
    
    # Python standard library random
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior in CuDNN
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Environment variable for some libraries that respect it
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_data_path(subpath: str) -> Path:
    """
    Helper to get a path relative to the data directory.
    """
    return get_config().get_data_path(subpath)


def get_output_path(subpath: str) -> Path:
    """
    Helper to get a path relative to the output directory.
    """
    return get_config().get_output_path(subpath)


def get_code_path(subpath: str) -> Path:
    """
    Helper to get a path relative to the code directory.
    """
    return get_config().get_code_path(subpath)