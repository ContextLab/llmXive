"""
Configuration Management for llmXive.

Handles project paths, run configurations, and seed pinning.
"""
import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
import numpy as np

@dataclass
class ProjectPaths:
    """Dataclass to hold project directory paths."""
    root: Path
    data_raw: Path
    data_processed: Path
    code: Path
    results: Path
    state: Path
    archive: Path
    specs: Path
    contracts: Path
    
    @classmethod
    def from_root(cls, root: Path) -> 'ProjectPaths':
        """Initialize paths from a root directory."""
        return cls(
            root=root,
            data_raw=root / "data" / "raw",
            data_processed=root / "data" / "processed",
            code=root / "code",
            results=root / "results",
            state=root / "state",
            archive=root / "archive",
            specs=root / "specs" / "001-llmxive-follow-up-extending-lens-rethink",
            contracts=root / "specs" / "001-llmxive-follow-up-extending-lens-rethink" / "contracts"
        )

@dataclass
class RunConfig:
    """Dataclass to hold runtime configuration."""
    project_id: str
    seed: int = 42
    batch_size: int = 32
    max_workers: int = 4
    timeout_seconds: int = 5
    # Model specific configs
    bert_model: str = "bert-base-uncased"
    # Training specific configs
    n_iter_permutation: int = 1000
    alpha_sweep: list = field(default_factory=lambda: [0.01, 0.05, 0.1])
    seed_sweep: list = field(default_factory=lambda: [42, 123, 456])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "project_id": self.project_id,
            "seed": self.seed,
            "batch_size": self.batch_size,
            "max_workers": self.max_workers,
            "timeout_seconds": self.timeout_seconds,
            "bert_model": self.bert_model,
            "n_iter_permutation": self.n_iter_permutation,
            "alpha_sweep": self.alpha_sweep,
            "seed_sweep": self.seed_sweep,
        }

class SeedManager:
    """Utility class to manage random seeds for reproducibility."""
    
    @staticmethod
    def set_seed(seed: int):
        """Set seeds for Python, NumPy, and PyTorch (if available)."""
        random.seed(seed)
        np.random.seed(seed)
        try:
            import torch
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass
        
def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).resolve().parent.parent

def get_paths(project_id: Optional[str] = None) -> ProjectPaths:
    """Get project paths for a specific project ID."""
    root = get_project_root()
    if project_id:
        root = root / project_id
    return ProjectPaths.from_root(root)

def get_config(project_id: str = "PROJ-925-llmxive-follow-up-extending-lens-rethink") -> RunConfig:
    """Get default run configuration."""
    return RunConfig(project_id=project_id)

def init_run(project_id: str, seed: int = 42) -> RunConfig:
    """Initialize a run with specific project ID and seed."""
    config = RunConfig(project_id=project_id, seed=seed)
    SeedManager.set_seed(seed)
    return config