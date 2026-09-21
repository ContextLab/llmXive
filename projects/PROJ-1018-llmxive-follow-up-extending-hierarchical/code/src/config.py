from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import os
import random
import numpy as np
import torch


@dataclass
class Config:
    """
    Base configuration manager for the llmXive pipeline.
    
    This dataclass centralizes all hyperparameters and runtime settings
    required for data loading, model inference, clustering, and evaluation.
    """
    # Randomness control for reproducibility
    seed: int = 42
    
    # Data processing parameters
    chunk_size: int = 2048
    
    # Model configuration
    model_path: str = "lmsys/pg-19-test"
    
    # Clustering parameters (User Story 2)
    k_clusters: int = 100
    
    # Optional: Override paths if needed
    data_dir: str = field(default_factory=lambda: "data")
    output_dir: str = field(default_factory=lambda: "data/processed")
    interim_dir: str = field(default_factory=lambda: "data/interim")
    
    # Performance tuning
    max_workers: int = 4
    batch_size: int = 32
    
    # Logging
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Validate and initialize derived settings."""
        self._set_seed(self.seed)
        self._validate_paths()
    
    def _set_seed(self, seed: int) -> None:
        """Set global random seeds for reproducibility."""
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    
    def _validate_paths(self) -> None:
        """Ensure required directories exist."""
        for path in [self.data_dir, self.output_dir, self.interim_dir]:
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary for serialization."""
        return {
            "seed": self.seed,
            "chunk_size": self.chunk_size,
            "model_path": self.model_path,
            "k_clusters": self.k_clusters,
            "data_dir": self.data_dir,
            "output_dir": self.output_dir,
            "interim_dir": self.interim_dir,
            "max_workers": self.max_workers,
            "batch_size": self.batch_size,
            "log_level": self.log_level
        }
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create a Config instance from a dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__dataclass_fields__})